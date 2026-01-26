"""
Processing pipeline for the Documentation Consolidation System.

This module provides the main processing pipeline that coordinates all components
to transform scattered documentation into an organized structure.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .analyzer import ContentAnalyzer
from .engine import ConsolidationEngine
from .generator import StructureGenerator
from .filesystem import FileSystem
from .models import (
    DocumentationStructure, MigrationLog, FileAnalysis, 
    ConsolidationGroup, Category
)
from .config import ConsolidationConfig
from .error_handler import ErrorHandler
from .reporting import ConsolidationReporter


@dataclass
class PipelineResult:
    """Result of running the documentation consolidation pipeline."""
    success: bool
    files_processed: int
    files_consolidated: int
    files_moved: int
    files_archived: int
    errors: List[str]
    warnings: List[str]
    migration_log: MigrationLog
    target_directory: str


class DocumentationPipeline:
    """
    Main processing pipeline that coordinates all system components.
    
    This class provides a high-level interface for running the complete
    documentation consolidation process with proper error handling,
    progress tracking, and result reporting.
    """
    
    def __init__(self, config: ConsolidationConfig):
        """
        Initialize the documentation pipeline.
        
        Args:
            config: Configuration object with all system settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize all components
        self.analyzer = ContentAnalyzer(config)
        self.engine = ConsolidationEngine(config)
        self.generator = StructureGenerator(config)
        self.filesystem = FileSystem()
        self.error_handler = ErrorHandler(config)
        self.report_generator = ConsolidationReporter(config, self.error_handler)
        
        # Initialize processing state
        self.migration_log = MigrationLog()
        self.discovered_files: List[Path] = []
        self.file_analyses: List[FileAnalysis] = []
        self.consolidation_groups: List[ConsolidationGroup] = []
        self.consolidated_docs: Dict[str, str] = {}
        self.doc_structure: Optional[DocumentationStructure] = None
        
        self.logger.info("Documentation pipeline initialized")
    
    def run(self, progress_callback: Optional[callable] = None) -> PipelineResult:
        """
        Run the complete documentation consolidation pipeline.
        
        Args:
            progress_callback: Optional callback function for progress updates.
                             Should accept (step: int, total: int, message: str)
        
        Returns:
            PipelineResult with processing results and statistics
        """
        self.logger.info("Starting documentation consolidation pipeline")
        
        try:
            total_steps = 8
            current_step = 0
            
            def update_progress(message: str):
                nonlocal current_step
                current_step += 1
                if progress_callback:
                    progress_callback(current_step, total_steps, message)
                self.logger.info(f"Step {current_step}/{total_steps}: {message}")
            
            # Step 1: Discovery
            update_progress("Discovering files")
            if not self._discover_files():
                return self._create_failure_result("File discovery failed")
            
            # Step 2: Analysis
            update_progress("Analyzing files")
            if not self._analyze_files():
                return self._create_failure_result("File analysis failed")
            
            # Step 3: Consolidation planning
            update_progress("Planning consolidation")
            if not self._plan_consolidation():
                return self._create_failure_result("Consolidation planning failed")
            
            # Step 4: Backup creation
            update_progress("Creating backups")
            if not self._create_backups():
                return self._create_failure_result("Backup creation failed")
            
            # Step 5: Content consolidation
            update_progress("Consolidating content")
            if not self._consolidate_content():
                return self._create_failure_result("Content consolidation failed")
            
            # Step 6: Structure generation
            update_progress("Creating directory structure")
            if not self._create_structure():
                return self._create_failure_result("Structure creation failed")
            
            # Step 7: File organization
            update_progress("Organizing files")
            if not self._organize_files():
                return self._create_failure_result("File organization failed")
            
            # Step 8: Final validation and reporting
            update_progress("Generating reports")
            if not self._generate_reports():
                return self._create_failure_result("Report generation failed")
            
            self.logger.info("Documentation consolidation pipeline completed successfully")
            return self._create_success_result()
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {e}"
            self.logger.error(error_msg)
            self.migration_log.add_error(error_msg)
            return self._create_failure_result(error_msg)
    
    def _discover_files(self) -> bool:
        """Discover all markdown files in the source directory."""
        try:
            self.discovered_files = self.analyzer.discover_files(self.config.source_directory)
            
            if not self.discovered_files:
                self.migration_log.add_error("No markdown files found in source directory")
                return False
            
            self.migration_log.files_processed = len(self.discovered_files)
            self.logger.info(f"Discovered {len(self.discovered_files)} files")
            return True
            
        except Exception as e:
            self.migration_log.add_error(f"File discovery failed: {e}")
            return False
    
    def _analyze_files(self) -> bool:
        """Analyze all discovered files."""
        try:
            self.file_analyses = []
            
            for file_path in self.discovered_files:
                try:
                    analysis = self.analyzer.analyze_file(file_path)
                    
                    # Validate analysis
                    validation_errors = self.analyzer.validate_analysis(analysis)
                    if validation_errors:
                        for error in validation_errors:
                            self.migration_log.add_warning(f"Analysis validation for {file_path}: {error}")
                    
                    self.file_analyses.append(analysis)
                    
                except Exception as e:
                    error_msg = f"Failed to analyze {file_path}: {e}"
                    self.logger.warning(error_msg)
                    self.migration_log.add_warning(error_msg)
            
            if not self.file_analyses:
                self.migration_log.add_error("No files could be analyzed successfully")
                return False
            
            self.logger.info(f"Successfully analyzed {len(self.file_analyses)} files")
            return True
            
        except Exception as e:
            self.migration_log.add_error(f"File analysis failed: {e}")
            return False
    
    def _plan_consolidation(self) -> bool:
        """Plan consolidation groups based on file analyses."""
        try:
            if not self.config.enable_consolidation:
                self.logger.info("Consolidation disabled, skipping planning")
                return True
            
            self.consolidation_groups = self.analyzer.identify_consolidation_candidates(
                self.file_analyses
            )
            
            self.logger.info(f"Identified {len(self.consolidation_groups)} consolidation groups")
            
            # Log consolidation plan
            for group in self.consolidation_groups:
                self.migration_log.add_operation(
                    operation_type="plan_consolidation",
                    source=f"{group.primary_file} + {len(group.related_files)} related",
                    destination=group.output_filename,
                    details=f"Strategy: {group.consolidation_strategy.value}"
                )
            
            return True
            
        except Exception as e:
            self.migration_log.add_error(f"Consolidation planning failed: {e}")
            return False
    
    def _create_backups(self) -> bool:
        """Create backups of original files if enabled."""
        try:
            if not self.config.create_backups:
                self.logger.info("Backup creation disabled")
                return True
            
            all_files = [str(analysis.filepath) for analysis in self.file_analyses]
            success = self.engine.create_backup(all_files, self.config.backup_directory)
            
            if success:
                self.logger.info(f"Created backups for {len(all_files)} files")
                self.migration_log.add_operation(
                    operation_type="backup",
                    source=f"{len(all_files)} files",
                    destination=self.config.backup_directory,
                    details="Backup created successfully"
                )
            else:
                self.migration_log.add_warning("Backup creation failed, continuing without backup")
            
            return True  # Don't fail the entire process if backup fails
            
        except Exception as e:
            self.migration_log.add_warning(f"Backup creation failed: {e}")
            return True  # Don't fail the entire process if backup fails
    
    def _consolidate_content(self) -> bool:
        """Consolidate related files according to consolidation groups."""
        try:
            if not self.config.enable_consolidation or not self.consolidation_groups:
                self.logger.info("No consolidation to perform")
                return True
            
            # Create file analysis lookup
            analysis_lookup = {analysis.filename: analysis for analysis in self.file_analyses}
            
            self.consolidated_docs = {}
            
            for group in self.consolidation_groups:
                try:
                    consolidated_content = self.engine.consolidate_group(group, analysis_lookup)
                    
                    if consolidated_content:
                        self.consolidated_docs[group.output_filename] = consolidated_content
                        
                        self.migration_log.add_operation(
                            operation_type="consolidate",
                            source=f"{group.primary_file} + {len(group.related_files)} others",
                            destination=group.output_filename,
                            details=f"Strategy: {group.consolidation_strategy.value}"
                        )
                    
                except Exception as e:
                    error_msg = f"Failed to consolidate group {group.group_id}: {e}"
                    self.logger.warning(error_msg)
                    self.migration_log.add_warning(error_msg)
            
            self.migration_log.files_consolidated = len(self.consolidated_docs)
            
            # Generate cross-references if enabled
            if self.consolidated_docs and self.config.create_cross_references:
                cross_refs = self.engine.create_cross_references(
                    self.consolidated_docs, self.consolidation_groups
                )
                self.logger.info(f"Generated cross-references for {len(cross_refs)} documents")
            
            return True
            
        except Exception as e:
            self.migration_log.add_error(f"Content consolidation failed: {e}")
            return False
    
    def _create_structure(self) -> bool:
        """Create the documentation directory structure."""
        try:
            self.doc_structure = DocumentationStructure()
            self.doc_structure.migration_log = self.migration_log
            
            success = self.generator.create_directory_structure(self.doc_structure)
            
            if success:
                self.logger.info("Documentation structure created successfully")
                return True
            else:
                self.migration_log.add_error("Failed to create documentation structure")
                return False
            
        except Exception as e:
            self.migration_log.add_error(f"Structure creation failed: {e}")
            return False
    
    def _organize_files(self) -> bool:
        """Organize files into their appropriate locations."""
        try:
            if not self.doc_structure:
                self.migration_log.add_error("Documentation structure not initialized")
                return False
            
            organized_files = self.generator.organize_files(
                self.file_analyses, self.consolidated_docs, self.doc_structure
            )
            
            self.migration_log.files_moved = len(organized_files)
            
            # Generate master index
            master_index_content = self.generator.generate_master_index(
                self.doc_structure, self.file_analyses, self.consolidation_groups
            )
            
            # Write master index
            master_index_path = Path(self.doc_structure.root_path) / self.doc_structure.master_index.filename
            if not self.filesystem.write_file(master_index_path, master_index_content):
                self.migration_log.add_warning("Failed to write master index")
            
            # Create category indexes
            category_indexes = self.generator.create_category_indexes(
                self.doc_structure, organized_files
            )
            
            self.logger.info(f"Organized {len(organized_files)} files into structure")
            return True
            
        except Exception as e:
            self.migration_log.add_error(f"File organization failed: {e}")
            return False
    
    def _generate_reports(self) -> bool:
        """Generate final reports and validation."""
        try:
            if not self.doc_structure:
                return False
            
            # Validate structure
            validation_errors = self.generator.validate_structure(self.doc_structure)
            if validation_errors:
                for error in validation_errors:
                    self.migration_log.add_warning(f"Structure validation: {error}")
            
            # Generate migration report
            report_path = Path(self.doc_structure.root_path) / "archive" / "migration-log.md"
            report_success = self.generator.generate_migration_report(
                self.migration_log, str(report_path)
            )
            
            if not report_success:
                self.migration_log.add_warning("Failed to generate migration report")
            
            return True
            
        except Exception as e:
            self.migration_log.add_error(f"Report generation failed: {e}")
            return False
    
    def _create_success_result(self) -> PipelineResult:
        """Create a successful pipeline result."""
        return PipelineResult(
            success=True,
            files_processed=self.migration_log.files_processed,
            files_consolidated=self.migration_log.files_consolidated,
            files_moved=self.migration_log.files_moved,
            files_archived=self.migration_log.files_archived,
            errors=self.migration_log.errors,
            warnings=self.migration_log.warnings,
            migration_log=self.migration_log,
            target_directory=self.config.target_directory
        )
    
    def _create_failure_result(self, error_message: str) -> PipelineResult:
        """Create a failed pipeline result."""
        return PipelineResult(
            success=False,
            files_processed=self.migration_log.files_processed,
            files_consolidated=self.migration_log.files_consolidated,
            files_moved=self.migration_log.files_moved,
            files_archived=self.migration_log.files_archived,
            errors=self.migration_log.errors + [error_message],
            warnings=self.migration_log.warnings,
            migration_log=self.migration_log,
            target_directory=self.config.target_directory
        )
    
    def get_processing_statistics(self) -> Dict[str, any]:
        """Get detailed processing statistics."""
        # Categorize files by type
        category_counts = {}
        for analysis in self.file_analyses:
            category = analysis.category
            category_counts[category.value] = category_counts.get(category.value, 0) + 1
        
        return {
            'files_discovered': len(self.discovered_files),
            'files_analyzed': len(self.file_analyses),
            'consolidation_groups': len(self.consolidation_groups),
            'consolidated_documents': len(self.consolidated_docs),
            'category_distribution': category_counts,
            'errors': len(self.migration_log.errors),
            'warnings': len(self.migration_log.warnings),
            'processing_time': self.migration_log.timestamp.isoformat() if self.migration_log.timestamp else None
        }