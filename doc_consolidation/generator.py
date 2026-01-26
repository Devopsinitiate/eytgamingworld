"""
Structure Generator component for the Documentation Consolidation System.

This module implements the StructureGenerator class that creates the final
organized documentation hierarchy with proper navigation and places all
processed files in their appropriate locations.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    from .interfaces import StructureGeneratorInterface
    from .models import (
        DocumentationStructure, FileAnalysis, ConsolidationGroup,
        Category, MigrationLog, DirectoryConfig, ContentType
    )
    from .config import ConsolidationConfig
    from .archive_manager import ArchiveManager
    from .markdown_validator import MarkdownValidator, ValidationSummary
except ImportError:
    from interfaces import StructureGeneratorInterface
    from models import (
        DocumentationStructure, FileAnalysis, ConsolidationGroup,
        Category, MigrationLog, DirectoryConfig, ContentType
    )
    from config import ConsolidationConfig
    from archive_manager import ArchiveManager
    from markdown_validator import MarkdownValidator, ValidationSummary


class StructureGenerator(StructureGeneratorInterface):
    """
    Generates the final organized documentation structure.
    
    The StructureGenerator creates directory hierarchies, generates navigation
    indexes, organizes files into appropriate locations, and creates comprehensive
    reports of the consolidation process.
    """
    
    def __init__(self, config: ConsolidationConfig):
        """Initialize the structure generator with configuration."""
        self.config = config
        self.logger = logging.getLogger('doc_consolidation.generator')
        self.archive_manager = None  # Will be initialized when needed
        self.markdown_validator = MarkdownValidator(config)  # Initialize markdown validator
    
    def create_directory_structure(self, structure: DocumentationStructure) -> bool:
        """
        Create the complete directory hierarchy for organized documentation.
        
        This method implements Requirements 1.1 and 1.3:
        - Creates hierarchical folder structure under docs/ with logical categories
        - Maintains separate directories for setup, features, testing, implementation, and reference materials
        
        Args:
            structure: DocumentationStructure defining the target organization
            
        Returns:
            True if directory creation was successful, False otherwise
        """
        self.logger.info(f"Creating directory structure at: {structure.root_path}")
        
        try:
            # Validate structure configuration
            validation_errors = self._validate_structure_config(structure)
            if validation_errors:
                for error in validation_errors:
                    self.logger.error(f"Structure validation error: {error}")
                return False
            
            # Create root documentation directory
            root_path = Path(structure.root_path)
            if not self._create_directory_with_permissions(root_path):
                return False
            
            self.logger.info(f"Created root documentation directory: {root_path}")
            
            # Create category directories with proper hierarchy
            created_dirs = []
            for category, config in structure.categories.items():
                category_path = root_path / config.path
                
                if not self._create_directory_with_permissions(category_path):
                    self.logger.error(f"Failed to create category directory: {category_path}")
                    return False
                
                created_dirs.append(str(category_path))
                self.logger.debug(f"Created category directory: {category_path} for {category.value}")
                
                # Create subdirectories for this category
                for subdir in config.subdirectories:
                    # Special handling for deprecated subdirectory in archive category
                    if (category == Category.HISTORICAL_ARCHIVE and 
                        subdir == "deprecated" and 
                        not structure.archive_section.include_deprecated):
                        self.logger.debug(f"Skipping deprecated subdirectory due to archive config: {subdir}")
                        continue
                    
                    subdir_path = category_path / subdir
                    
                    if not self._create_directory_with_permissions(subdir_path):
                        self.logger.error(f"Failed to create subdirectory: {subdir_path}")
                        return False
                    
                    created_dirs.append(str(subdir_path))
                    self.logger.debug(f"Created subdirectory: {subdir_path}")
            
            # Create archive directory structure (if not already created by HISTORICAL_ARCHIVE category)
            archive_path = root_path / structure.archive_section.path
            historical_archive_path = None
            
            if Category.HISTORICAL_ARCHIVE in structure.categories:
                historical_archive_path = structure.categories[Category.HISTORICAL_ARCHIVE].path
            
            # Only create archive directory if it's different from historical archive category path
            if structure.archive_section.path != historical_archive_path:
                if not self._create_directory_with_permissions(archive_path):
                    self.logger.error(f"Failed to create archive directory: {archive_path}")
                    return False
                
                created_dirs.append(str(archive_path))
                self.logger.debug(f"Created archive directory: {archive_path}")
            else:
                self.logger.debug(f"Archive directory already created as category: {archive_path}")
            
            # Create deprecated subdirectory in archive if configured
            if structure.archive_section.include_deprecated:
                deprecated_path = archive_path / "deprecated"
                if not self._create_directory_with_permissions(deprecated_path):
                    self.logger.error(f"Failed to create deprecated directory: {deprecated_path}")
                    return False
                
                created_dirs.append(str(deprecated_path))
                self.logger.debug(f"Created deprecated directory: {deprecated_path}")
            
            # Verify all required directories were created
            verification_result = self._verify_directory_structure(structure)
            if not verification_result:
                self.logger.error("Directory structure verification failed")
                return False
            
            self.logger.info(f"Directory structure created successfully. Created {len(created_dirs)} directories.")
            self.logger.info(f"Structure follows Django conventions: {self.config.follow_django_conventions}")
            
            return True
            
        except PermissionError as e:
            self.logger.error(f"Permission denied while creating directory structure: {e}")
            return False
        except OSError as e:
            self.logger.error(f"OS error while creating directory structure: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while creating directory structure: {e}")
            return False
    
    def generate_master_index(self, structure: DocumentationStructure,
                            file_analyses: List[FileAnalysis],
                            consolidated_groups: List[ConsolidationGroup]) -> str:
        """
        Generate the master README.md index for navigation.
        
        This method implements Requirements 4.1, 4.2, 4.3, 4.4, 4.5:
        - Creates comprehensive README.md in docs/ directory
        - Organizes links by category with clear descriptions
        - Includes quick-start sections for developers
        - Maintains consistent naming conventions
        - Provides search-friendly organization
        
        Args:
            structure: DocumentationStructure with configuration
            file_analyses: List of all file analyses
            consolidated_groups: List of consolidation groups that were processed
            
        Returns:
            Master index content as markdown string
        """
        self.logger.info("Generating enhanced master index with comprehensive navigation")
        
        sections = []
        
        # Enhanced Header with project context
        sections.extend(self._generate_enhanced_header(structure))
        
        # Enhanced Quick Start section with better organization
        if structure.master_index.include_quick_start:
            sections.extend(self._generate_enhanced_quick_start_section(structure))
        
        # Comprehensive Table of Contents with better organization
        sections.extend(self._generate_enhanced_table_of_contents(
            structure, file_analyses, consolidated_groups))
        
        # Enhanced Search and Navigation Tips
        if structure.master_index.include_search_tips:
            sections.extend(self._generate_enhanced_search_tips_section(structure))
        
        # Enhanced Project Overview with statistics
        sections.extend(self._generate_enhanced_project_overview_section(
            file_analyses, consolidated_groups))
        
        # Enhanced Recent Updates with better formatting
        sections.extend(self._generate_enhanced_recent_updates_section(file_analyses))
        
        # Additional sections for better navigation
        sections.extend(self._generate_developer_resources_section(structure))
        sections.extend(self._generate_maintenance_section(structure))
        
        # Enhanced Footer with more information
        sections.extend(self._generate_enhanced_footer())
        
        self.logger.info(f"Generated master index with {len(sections)} sections")
        return "\n".join(sections)
    
    def organize_files(self, file_analyses: List[FileAnalysis],
                      consolidated_docs: Dict[str, str],
                      structure: DocumentationStructure) -> Dict[str, str]:
        """
        Move and organize files into their appropriate directory locations.
        
        This method implements Requirements 1.2 and 1.5:
        - Groups related documentation into appropriate subdirectories
        - Preserves all important information during reorganization
        
        Args:
            file_analyses: List of FileAnalysis objects for all files
            consolidated_docs: Dictionary of consolidated document content
            structure: DocumentationStructure defining target organization
            
        Returns:
            Dictionary mapping original file paths to new locations
        """
        self.logger.info("Organizing files into directory structure")
        
        file_moves = {}
        root_path = Path(structure.root_path)
        
        # Track used filenames to handle conflicts
        used_filenames = {}  # target_dir -> set of filenames
        
        try:
            # First, write consolidated documents
            for filename, content in consolidated_docs.items():
                # Determine appropriate directory based on filename
                target_dir = self._determine_target_directory_for_consolidated(filename, structure)
                target_path = root_path / target_dir
                
                # Handle naming conflicts for consolidated files
                final_filename = self._resolve_filename_conflict(
                    filename, target_path, used_filenames.get(target_dir, set())
                )
                
                final_target_path = target_path / final_filename
                
                # Ensure target directory exists
                if not self._create_directory_with_permissions(final_target_path.parent):
                    self.logger.error(f"Failed to create directory: {final_target_path.parent}")
                    continue
                
                # Write consolidated content with integrity verification
                if self._write_file_with_integrity_check(final_target_path, content):
                    file_moves[f"consolidated_{filename}"] = str(final_target_path)
                    
                    # Track used filename
                    if target_dir not in used_filenames:
                        used_filenames[target_dir] = set()
                    used_filenames[target_dir].add(final_filename)
                    
                    self.logger.debug(f"Created consolidated file: {final_target_path}")
                else:
                    self.logger.error(f"Failed to write consolidated file: {final_target_path}")
            
            # Then, organize individual files that weren't consolidated
            consolidated_source_files = self._get_consolidated_source_files(consolidated_docs, file_analyses)
            
            for analysis in file_analyses:
                original_path = analysis.filepath
                filename = analysis.filename
                
                # Skip files that were consolidated
                if str(original_path) in consolidated_source_files:
                    self.logger.debug(f"Skipping consolidated file: {original_path}")
                    continue
                
                # Determine target directory and subdirectory
                target_dir_path = self._determine_target_directory_for_analysis(analysis, structure)
                
                # Handle naming conflicts
                final_filename = self._resolve_filename_conflict(
                    filename, target_dir_path, used_filenames.get(str(target_dir_path.relative_to(root_path)), set())
                )
                
                final_target_path = target_dir_path / final_filename
                
                # Ensure target directory exists
                if not self._create_directory_with_permissions(final_target_path.parent):
                    self.logger.error(f"Failed to create directory: {final_target_path.parent}")
                    continue
                
                # Move or copy file with integrity verification
                if self._move_file_with_integrity_check(original_path, final_target_path):
                    file_moves[str(original_path)] = str(final_target_path)
                    
                    # Track used filename
                    target_dir_key = str(target_dir_path.relative_to(root_path))
                    if target_dir_key not in used_filenames:
                        used_filenames[target_dir_key] = set()
                    used_filenames[target_dir_key].add(final_filename)
                    
                    self.logger.debug(f"Moved file: {original_path} -> {final_target_path}")
                else:
                    self.logger.error(f"Failed to move file: {original_path} -> {final_target_path}")
            
            self.logger.info(f"Successfully organized {len(file_moves)} files")
            
            # Log any naming conflicts that were resolved
            conflict_count = sum(len(names) for names in used_filenames.values()) - len(file_moves)
            if conflict_count > 0:
                self.logger.info(f"Resolved {conflict_count} filename conflicts during organization")
            
            return file_moves
            
        except Exception as e:
            self.logger.error(f"Error organizing files: {e}")
            return {}
    
    def create_category_indexes(self, structure: DocumentationStructure,
                              organized_files: Dict[str, str]) -> Dict[str, str]:
        """
        Create enhanced index files for each category directory.
        
        This method implements Requirements 4.2 and 4.4:
        - Organizes links by category with clear descriptions
        - Maintains consistent naming conventions
        
        Args:
            structure: DocumentationStructure with category definitions
            organized_files: Dictionary mapping files to their new locations
            
        Returns:
            Dictionary mapping category paths to their index content
        """
        self.logger.info("Creating enhanced category index files")
        
        category_indexes = {}
        root_path = Path(structure.root_path)
        
        for category, config in structure.categories.items():
            category_path = root_path / config.path
            index_path = category_path / "README.md"
            
            # Generate enhanced index content
            index_content = self._generate_enhanced_category_index(category, config, organized_files)
            
            # Write index file
            try:
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(index_content)
                
                category_indexes[config.path] = index_content
                self.logger.debug(f"Created enhanced category index: {index_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to create index for {config.path}: {e}")
        
        return category_indexes
    
    def validate_structure(self, structure: DocumentationStructure) -> List[str]:
        """
        Validate the generated documentation structure with comprehensive markdown validation.
        
        Enhanced for Task 7.1: Create markdown validation
        - Validates all generated markdown files for proper formatting (Requirement 8.1)
        - Checks internal link functionality after reorganization (Requirement 8.2)
        - Verifies content integrity and completeness (Requirement 8.3)
        
        Args:
            structure: DocumentationStructure to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        self.logger.info("Performing comprehensive structure and markdown validation")
        errors = []
        root_path = Path(structure.root_path)
        
        # Check if root directory exists
        if not root_path.exists():
            errors.append(f"Root documentation directory does not exist: {root_path}")
            return errors
        
        # Check category directories
        for category, config in structure.categories.items():
            category_path = root_path / config.path
            if not category_path.exists():
                errors.append(f"Category directory missing: {category_path}")
            
            # Check subdirectories
            for subdir in config.subdirectories:
                subdir_path = category_path / subdir
                if not subdir_path.exists():
                    errors.append(f"Subdirectory missing: {subdir_path}")
        
        # Check master index
        master_index_path = root_path / structure.master_index.filename
        if not master_index_path.exists():
            errors.append(f"Master index missing: {master_index_path}")
        
        # Check archive directory
        archive_path = root_path / structure.archive_section.path
        if not archive_path.exists():
            errors.append(f"Archive directory missing: {archive_path}")
        
        # Comprehensive markdown validation (Task 7.1)
        if self.config.validate_output:
            self.logger.info("Performing comprehensive markdown validation")
            
            try:
                # Validate all markdown files in the documentation structure
                validation_summary = self.markdown_validator.validate_directory(root_path, structure)
                
                # Add validation errors to the main error list
                for result in validation_summary.results:
                    if not result.is_valid:
                        file_relative = result.filepath.relative_to(root_path)
                        
                        # Add format issues
                        for issue in result.format_issues:
                            errors.append(f"Format issue in {file_relative}: {issue}")
                        
                        # Add broken links
                        for link in result.broken_links:
                            errors.append(f"Broken link in {file_relative}: {link}")
                        
                        # Add content issues
                        for issue in result.content_issues:
                            errors.append(f"Content issue in {file_relative}: {issue}")
                        
                        # Add general errors
                        for error in result.errors:
                            errors.append(f"Validation error in {file_relative}: {error}")
                
                # Generate validation report
                validation_report_path = root_path / "archive" / "validation-report.md"
                if validation_report_path.parent.exists():
                    report_generated = self.markdown_validator.generate_validation_report(
                        validation_summary, validation_report_path
                    )
                    if report_generated:
                        self.logger.info(f"Generated validation report: {validation_report_path}")
                    else:
                        self.logger.warning("Failed to generate validation report")
                
                # Log validation summary
                self.logger.info(f"Markdown validation complete: {validation_summary.valid_files}/"
                               f"{validation_summary.total_files} files valid "
                               f"({validation_summary.success_rate:.1f}% success rate)")
                
                if validation_summary.total_broken_links > 0:
                    self.logger.warning(f"Found {validation_summary.total_broken_links} broken links")
                
            except Exception as e:
                error_msg = f"Markdown validation failed: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)
        
        # Legacy link validation for master index (kept for backward compatibility)
        try:
            with open(master_index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                broken_links = self._find_broken_links(content, root_path)
                for link in broken_links:
                    errors.append(f"Broken link in master index: {link}")
        except Exception as e:
            errors.append(f"Could not validate master index links: {e}")
        
        return errors
    
    def validate_markdown_files(self, directory_path: Path, 
                               generate_report: bool = True) -> ValidationSummary:
        """
        Standalone markdown validation for all files in a directory.
        
        Task 7.1: Create markdown validation
        This method provides comprehensive markdown validation including:
        - Format validation (Requirement 8.1)
        - Link functionality checking (Requirement 8.2)  
        - Content integrity verification (Requirement 8.3)
        
        Args:
            directory_path: Path to directory containing markdown files
            generate_report: Whether to generate a validation report file
            
        Returns:
            ValidationSummary with comprehensive validation results
        """
        self.logger.info(f"Starting comprehensive markdown validation for: {directory_path}")
        
        # Perform validation
        validation_summary = self.markdown_validator.validate_directory(directory_path)
        
        # Generate report if requested
        if generate_report and validation_summary.total_files > 0:
            report_path = directory_path / "validation-report.md"
            report_generated = self.markdown_validator.generate_validation_report(
                validation_summary, report_path
            )
            if report_generated:
                self.logger.info(f"Validation report generated: {report_path}")
            else:
                self.logger.warning("Failed to generate validation report")
        
        # Log summary
        self.logger.info(f"Markdown validation summary:")
        self.logger.info(f"  - Total files: {validation_summary.total_files}")
        self.logger.info(f"  - Valid files: {validation_summary.valid_files}")
        self.logger.info(f"  - Success rate: {validation_summary.success_rate:.1f}%")
        self.logger.info(f"  - Total errors: {validation_summary.total_errors}")
        self.logger.info(f"  - Total warnings: {validation_summary.total_warnings}")
        self.logger.info(f"  - Broken links: {validation_summary.total_broken_links}")
        
        return validation_summary
    
    def generate_migration_report(self, migration_log: MigrationLog,
                                output_path: str) -> bool:
        """
        Generate a comprehensive report of all consolidation operations.
        
        Args:
            migration_log: MigrationLog with all recorded operations
            output_path: Path where the report should be saved
            
        Returns:
            True if report generation was successful, False otherwise
        """
        self.logger.info(f"Generating migration report: {output_path}")
        
        try:
            sections = []
            
            # Header
            sections.append("# Documentation Consolidation Migration Report")
            sections.append("")
            sections.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            sections.append(f"**Process Started:** {migration_log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            sections.append("")
            
            # Summary Statistics
            sections.append("## Summary")
            sections.append("")
            sections.append(f"- **Files Processed:** {migration_log.files_processed}")
            sections.append(f"- **Files Moved:** {migration_log.files_moved}")
            sections.append(f"- **Files Consolidated:** {migration_log.files_consolidated}")
            sections.append(f"- **Files Archived:** {migration_log.files_archived}")
            sections.append(f"- **Errors:** {len(migration_log.errors)}")
            sections.append(f"- **Warnings:** {len(migration_log.warnings)}")
            sections.append("")
            
            # Operations Log
            if migration_log.operations:
                sections.append("## Operations Performed")
                sections.append("")
                sections.append("| Operation | Source | Destination | Details | Timestamp |")
                sections.append("|-----------|--------|-------------|---------|-----------|")
                
                for op in migration_log.operations:
                    sections.append(
                        f"| {op.get('type', 'N/A')} | "
                        f"{op.get('source', 'N/A')} | "
                        f"{op.get('destination', 'N/A')} | "
                        f"{op.get('details', 'N/A')} | "
                        f"{op.get('timestamp', 'N/A')} |"
                    )
                sections.append("")
            
            # Errors and Warnings
            if migration_log.errors:
                sections.append("## Errors")
                sections.append("")
                for error in migration_log.errors:
                    sections.append(f"- ❌ {error}")
                sections.append("")
            
            if migration_log.warnings:
                sections.append("## Warnings")
                sections.append("")
                for warning in migration_log.warnings:
                    sections.append(f"- ⚠️ {warning}")
                sections.append("")
            
            # Recommendations
            sections.append("## Recommendations")
            sections.append("")
            sections.append("1. **Review Consolidated Files:** Check that consolidated documents ")
            sections.append("   maintain all important information from original files.")
            sections.append("")
            sections.append("2. **Update Internal Links:** Some internal links may need updating ")
            sections.append("   to reflect the new file organization.")
            sections.append("")
            sections.append("3. **Verify Archive Content:** Review archived files to ensure ")
            sections.append("   they are no longer needed in the main documentation.")
            sections.append("")
            sections.append("4. **Update Build Scripts:** If your project uses documentation ")
            sections.append("   build tools, update them to use the new structure.")
            sections.append("")
            
            # Footer
            sections.append("---")
            sections.append("")
            sections.append("This report was generated by the Documentation Consolidation System.")
            sections.append("For questions or issues, please contact the development team.")
            
            # Write report
            report_content = "\n".join(sections)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info("Migration report generated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate migration report: {e}")
            return False
    
    def process_archive_operations(self, structure: DocumentationStructure,
                                 file_analyses: List[FileAnalysis]) -> Dict[str, str]:
        """
        Process archive operations including directory creation and file movement.
        
        This method implements Task 6.2 requirements:
        - Create archive/ directory structure
        - Move historical documentation to archive
        - Add freshness indicators to outdated content
        
        Args:
            structure: DocumentationStructure with archive configuration
            file_analyses: List of FileAnalysis objects for all discovered files
            
        Returns:
            Dictionary mapping original file paths to archive locations
        """
        self.logger.info("Processing archive operations for Task 6.2")
        
        # Initialize archive manager if not already done
        if self.archive_manager is None:
            self.archive_manager = ArchiveManager(structure)
        
        archived_files = {}
        
        try:
            # Step 1: Create archive directory structure (Requirement 7.3)
            self.logger.info("Creating archive directory structure")
            if not self.archive_manager.create_archive_directory_structure():
                self.logger.error("Failed to create archive directory structure")
                return archived_files
            
            # Step 2: Move historical documentation to archive (Requirement 7.3)
            self.logger.info("Moving historical documentation to archive")
            moved_files = self.archive_manager.move_historical_documentation_to_archive(file_analyses)
            archived_files.update(moved_files)
            
            # Step 3: Add freshness indicators to outdated content (Requirement 7.4)
            self.logger.info("Adding freshness indicators to outdated content")
            freshness_updates = self.archive_manager.add_freshness_indicators_to_outdated_content(file_analyses)
            
            # Step 4: Create archive migration log
            self.logger.info("Creating archive migration log")
            if not self.archive_manager.create_archive_migration_log(moved_files):
                self.logger.warning("Failed to create archive migration log")
            
            # Step 5: Validate archive structure
            self.logger.info("Validating archive structure")
            validation_errors = self.archive_manager.validate_archive_structure()
            if validation_errors:
                for error in validation_errors:
                    self.logger.warning(f"Archive validation warning: {error}")
                    structure.migration_log.add_warning(f"Archive validation: {error}")
            
            # Log summary
            self.logger.info(f"Archive operations completed successfully:")
            self.logger.info(f"  - Files archived: {len(moved_files)}")
            self.logger.info(f"  - Freshness indicators added: {len(freshness_updates)}")
            self.logger.info(f"  - Validation errors: {len(validation_errors)}")
            
            # Update migration log with archive operations summary
            structure.migration_log.add_operation(
                "archive_operations_complete",
                "archive_processing",
                structure.archive_section.path,
                f"Archived {len(moved_files)} files, added {len(freshness_updates)} freshness indicators"
            )
            
            return archived_files
            
        except Exception as e:
            self.logger.error(f"Error during archive operations: {e}")
            structure.migration_log.add_error(f"Archive operations failed: {e}")
            return archived_files
    
    def _generate_quick_start_section(self) -> List[str]:
        """Generate quick start section for master index."""
        return [
            "## Quick Start",
            "",
            "### For New Developers",
            "1. Start with [Setup & Configuration](setup/) for installation instructions",
            "2. Review [Developer Quick Start](development/quick-start.md) for development setup",
            "3. Explore [Feature Documentation](features/) to understand system components",
            "",
            "### For Existing Developers",
            "- [Testing Guide](testing/) - How to run and write tests",
            "- [API Reference](reference/) - Quick reference for APIs and utilities",
            "- [Implementation History](implementation/) - Track of completed features",
            "",
            "### Common Tasks",
            "- **Setting up the development environment:** [Installation Guide](setup/installation.md)",
            "- **Running tests:** [Testing Procedures](testing/testing-procedures.md)",
            "- **Understanding payment flow:** [Payment System Guide](features/payments/)",
            "- **Tournament management:** [Tournament Documentation](features/tournaments/)",
            "",
        ]
    
    def _generate_enhanced_header(self, structure: DocumentationStructure) -> List[str]:
        """Generate enhanced header section with project context."""
        return [
            f"# {structure.master_index.title}",
            "",
            "[![Documentation Status](https://img.shields.io/badge/docs-consolidated-brightgreen.svg)](.)",
            "[![Django](https://img.shields.io/badge/Django-5.x-green.svg)](https://djangoproject.com/)",
            "",
            "Welcome to the **comprehensive documentation** for this Django project. This documentation ",
            "has been professionally organized and consolidated following Django community best practices ",
            "to provide intuitive navigation, comprehensive coverage, and excellent developer experience.",
            "",
            "🚀 **Quick Navigation:** Use the table of contents below or browse by category",
            "📚 **Comprehensive Coverage:** All project documentation in one organized location",
            "🔍 **Search-Friendly:** Consistent naming and clear organization for easy discovery",
            "⚡ **Developer-Focused:** Quick-start guides and practical examples throughout",
            "",
        ]
    
    def _generate_enhanced_quick_start_section(self, structure: DocumentationStructure) -> List[str]:
        """Generate enhanced quick start section with better organization."""
        sections = [
            "## 🚀 Quick Start Guide",
            "",
            "### New to the Project?",
            "",
            "**Essential First Steps:**",
            "1. 📋 **[Installation & Setup](setup/)** - Get your development environment ready",
            "2. 🏃 **[Developer Quick Start](development/quick-start.md)** - Your first 15 minutes",
            "3. 🎯 **[Core Features Overview](features/)** - Understand what the system does",
            "4. 🧪 **[Run Your First Test](testing/)** - Verify everything works",
            "",
            "### Experienced Developer?",
            "",
            "**Jump Right In:**",
            "- 🔧 **[API Documentation](development/)** - Integration guides and references",
            "- 📊 **[Testing Framework](testing/)** - Test suites and validation procedures",
            "- 📈 **[Implementation Status](implementation/)** - What's built and what's planned",
            "- 🔍 **[Quick References](reference/)** - Cheat sheets and troubleshooting",
            "",
            "### Common Developer Tasks",
            "",
            "| Task | Documentation | Quick Link |",
            "|------|---------------|------------|",
            "| **Environment Setup** | Complete installation guide | [setup/installation.md](setup/installation.md) |",
            "| **Payment Integration** | Payment system documentation | [features/payments/](features/payments/) |",
            "| **Tournament Management** | Tournament system guides | [features/tournaments/](features/tournaments/) |",
            "| **Authentication Setup** | Auth system configuration | [features/authentication/](features/authentication/) |",
            "| **Testing & Validation** | Test execution procedures | [testing/testing-procedures.md](testing/testing-procedures.md) |",
            "| **API Integration** | Integration guides | [development/integration-guide.md](development/integration-guide.md) |",
            "",
        ]
        
        return sections
    
    def _generate_enhanced_table_of_contents(self, structure: DocumentationStructure,
                                           file_analyses: List[FileAnalysis],
                                           consolidated_groups: List[ConsolidationGroup]) -> List[str]:
        """Generate enhanced table of contents with better organization."""
        sections = [
            "## 📚 Documentation Catalog",
            "",
            "### By Category",
            "",
        ]
        
        # Generate enhanced TOC for each category
        for category in structure.master_index.category_order:
            if category in structure.categories:
                config = structure.categories[category]
                
                # Category header with icon and description
                category_icon = self._get_category_icon(category)
                sections.append(f"#### {category_icon} [{config.description}]({config.path}/)")
                sections.append("")
                
                # Enhanced category description
                category_desc = self._get_enhanced_category_description(category)
                if category_desc:
                    sections.append(f"*{category_desc}*")
                    sections.append("")
                
                # Get and organize category files
                category_files = self._get_enhanced_category_files(category, file_analyses, consolidated_groups)
                
                if category_files:
                    # Group files by type for better organization
                    grouped_files = self._group_files_by_type(category_files)
                    
                    for file_type, files in grouped_files.items():
                        if files:
                            if len(grouped_files) > 1:  # Only show type headers if multiple types
                                sections.append(f"**{file_type}:**")
                            
                            for file_info in files[:8]:  # Show top 8 files per type
                                title = file_info['title']
                                path = file_info['path']
                                desc = file_info.get('description', '')
                                
                                if desc:
                                    sections.append(f"- **[{title}]({path})** - {desc}")
                                else:
                                    sections.append(f"- **[{title}]({path})**")
                            
                            if len(files) > 8:
                                sections.append(f"- *[...and {len(files) - 8} more {file_type.lower()}]({config.path}/)*")
                            
                            sections.append("")
                    
                    # Add subdirectory navigation if available
                    if config.subdirectories:
                        sections.append("**Subdirectories:**")
                        for subdir in config.subdirectories:
                            subdir_title = subdir.replace('-', ' ').replace('_', ' ').title()
                            sections.append(f"- 📁 **[{subdir_title}]({config.path}/{subdir}/)**")
                        sections.append("")
                else:
                    sections.append("*No files currently in this category*")
                    sections.append("")
                
                sections.append("---")
                sections.append("")
        
        return sections
    
    def _generate_enhanced_search_tips_section(self, structure: DocumentationStructure) -> List[str]:
        """Generate enhanced search and navigation tips section."""
        return [
            "## 🔍 Navigation & Search Guide",
            "",
            "### Finding What You Need",
            "",
            "**By Purpose:**",
            "- 🛠️ **Getting Started:** Check [setup/](setup/) and [development/](development/)",
            "- 🎯 **Feature-Specific:** Browse [features/](features/) by component",
            "- 🧪 **Testing & QA:** Everything in [testing/](testing/) and [reference/](reference/)",
            "- 📊 **Project History:** Review [implementation/](implementation/) for completed work",
            "",
            "**By File Type:**",
            "- 📋 **Guides & Tutorials:** Look for files ending in `-guide.md` or `-tutorial.md`",
            "- 🔧 **Setup Instructions:** Files containing `setup`, `install`, or `config`",
            "- 📊 **Reports & Summaries:** Check `*-summary.md` and `*-report.md` files",
            "- 🔍 **Quick References:** Files starting with `quick-` or ending in `-reference.md`",
            "",
            "### Search Strategies",
            "",
            "**IDE/Editor Search:**",
            "- Use **Ctrl+Shift+F** (VS Code) or **Cmd+Shift+F** (Mac) to search across all docs",
            "- Search for specific terms like `payment`, `tournament`, `auth`, `test`",
            "- Use file name patterns: `*setup*`, `*guide*`, `*test*`",
            "",
            "**GitHub Search:**",
            "- Use GitHub's search with `path:docs/` to search within documentation",
            "- Combine with keywords: `path:docs/ payment setup`",
            "",
            "**Command Line:**",
            "```bash",
            "# Search for content in all documentation",
            "grep -r \"search term\" docs/",
            "",
            "# Find files by name pattern",
            "find docs/ -name \"*payment*\" -type f",
            "```",
            "",
        ]
    
    def _generate_enhanced_project_overview_section(self, file_analyses: List[FileAnalysis],
                                                  consolidated_groups: List[ConsolidationGroup]) -> List[str]:
        """Generate enhanced project overview section with statistics."""
        # Calculate comprehensive statistics
        stats = self._calculate_documentation_statistics(file_analyses, consolidated_groups)
        
        sections = [
            "## 📊 Project Documentation Overview",
            "",
            "### Documentation Statistics",
            "",
            f"- **📄 Total Documents:** {stats['total_documents']}",
            f"- **📝 Total Word Count:** {stats['total_words']:,} words",
            f"- **🔗 Consolidated Groups:** {stats['consolidated_groups']}",
            f"- **📁 Categories Covered:** {stats['categories_covered']}",
            f"- **🔄 Last Updated:** {stats['last_updated']}",
            "",
            "### Content Breakdown by Category",
            "",
        ]
        
        # Add category breakdown
        for category, count in stats['category_breakdown'].items():
            if count > 0:
                category_name = category.value.replace('_', ' ').title()
                percentage = (count / stats['total_documents']) * 100
                sections.append(f"- **{category_name}:** {count} documents ({percentage:.1f}%)")
        
        sections.extend([
            "",
            "### Key Features Documented",
            "",
        ])
        
        # Add feature coverage
        features = stats.get('features_covered', [])
        if features:
            for feature in features:
                sections.append(f"- ✅ **{feature}**")
        else:
            sections.append("- 📋 *Feature documentation analysis in progress*")
        
        sections.extend([
            "",
            "### Documentation Quality Metrics",
            "",
            f"- **📊 Average Document Length:** {stats['avg_document_length']} words",
            f"- **🔗 Internal Links:** {stats['internal_links']} cross-references",
            f"- **📈 Coverage Score:** {stats['coverage_score']}/10",
            "",
        ])
        
        return sections
    
    def _generate_enhanced_recent_updates_section(self, file_analyses: List[FileAnalysis]) -> List[str]:
        """Generate enhanced recent updates section with better formatting."""
        # Find recently modified files with more sophisticated analysis
        recent_files = []
        for analysis in file_analyses:
            if analysis.metadata.last_modified:
                recent_files.append({
                    'date': analysis.metadata.last_modified,
                    'filename': analysis.filename,
                    'category': analysis.category,
                    'word_count': analysis.metadata.word_count,
                    'path': f"{analysis.category.value}/{analysis.filename}"
                })
        
        # Sort by modification date (most recent first)
        recent_files.sort(key=lambda x: x['date'], reverse=True)
        
        sections = [
            "## 📅 Recent Documentation Updates",
            "",
        ]
        
        if recent_files:
            sections.extend([
                "### Latest Changes",
                "",
                "| Document | Category | Updated | Size |",
                "|----------|----------|---------|------|",
            ])
            
            for file_info in recent_files[:10]:  # Show top 10
                date_str = file_info['date'].strftime('%Y-%m-%d')
                category_name = file_info['category'].value.replace('_', ' ').title()
                word_count = f"{file_info['word_count']} words"
                filename = file_info['filename'].replace('.md', '')
                
                sections.append(
                    f"| **[{filename}]({file_info['path']})** | {category_name} | {date_str} | {word_count} |"
                )
            
            sections.extend([
                "",
                "### Update Frequency",
                "",
            ])
            
            # Calculate update frequency
            update_stats = self._calculate_update_frequency(recent_files)
            for period, count in update_stats.items():
                sections.append(f"- **{period}:** {count} updates")
            
            sections.extend(["", ""])
        else:
            sections.extend([
                "No recent modification dates available in file metadata.",
                "",
                "*Note: This may indicate files were migrated or timestamps were not preserved.*",
                "",
                ""
            ])
        
        return sections
    
    def _generate_developer_resources_section(self, structure: DocumentationStructure) -> List[str]:
        """Generate developer resources section."""
        return [
            "## 🛠️ Developer Resources",
            "",
            "### Essential Tools & Links",
            "",
            "**Development Environment:**",
            "- 🐍 **Python/Django:** [Official Django Documentation](https://docs.djangoproject.com/)",
            "- 🧪 **Testing:** [pytest Documentation](https://docs.pytest.org/)",
            "- 📦 **Package Management:** [pip Documentation](https://pip.pypa.io/)",
            "",
            "**Project-Specific Resources:**",
            "- 📋 **[Setup Checklist](setup/)** - Complete environment setup",
            "- 🔧 **[Development Tools](development/)** - IDE setup and debugging",
            "- 🧪 **[Testing Framework](testing/)** - Test execution and writing",
            "- 📊 **[Code Quality](reference/)** - Standards and best practices",
            "",
            "### Getting Help",
            "",
            "**Documentation Issues:**",
            "1. Check the [migration log](archive/migration-log.md) for recent changes",
            "2. Search existing documentation using the strategies above",
            "3. Contact the development team for clarification",
            "",
            "**Technical Issues:**",
            "1. Review [troubleshooting guides](reference/troubleshooting.md)",
            "2. Check [testing procedures](testing/testing-procedures.md)",
            "3. Consult [implementation history](implementation/) for context",
            "",
        ]
    
    def _generate_maintenance_section(self, structure: DocumentationStructure) -> List[str]:
        """Generate maintenance and meta-information section."""
        return [
            "## 🔧 Documentation Maintenance",
            "",
            "### About This Documentation",
            "",
            "This documentation was automatically consolidated and organized using the ",
            "**Documentation Consolidation System**. The system analyzed over 100+ scattered ",
            "markdown files and organized them into this structured, navigable format.",
            "",
            "**Key Features:**",
            "- ✅ **Automated Organization:** Files categorized by content and purpose",
            "- ✅ **Content Preservation:** All original information maintained",
            "- ✅ **Cross-References:** Related documents linked together",
            "- ✅ **Search Optimization:** Consistent naming and clear structure",
            "",
            "### Maintenance Guidelines",
            "",
            "**Adding New Documentation:**",
            "1. Place files in the appropriate category directory",
            "2. Follow the established naming conventions",
            "3. Update category README.md files as needed",
            "4. Add cross-references to related documents",
            "",
            "**Updating Existing Documentation:**",
            "1. Maintain the established structure and format",
            "2. Update the master index if adding major sections",
            "3. Check and update internal links",
            "4. Consider impact on related documents",
            "",
        ]
    
    def _generate_enhanced_footer(self) -> List[str]:
        """Generate enhanced footer with comprehensive information."""
        return [
            "---",
            "",
            "## 📋 Documentation Metadata",
            "",
            f"**📅 Consolidated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**  ",
            f"**🔧 System:** Documentation Consolidation System v1.0**  ",
            f"**📊 Format:** Markdown with Django conventions**  ",
            f"**🔍 Structure:** Hierarchical category-based organization**  ",
            "",
            "### Quick Links",
            "",
            "- 📋 **[Migration Log](archive/migration-log.md)** - Detailed consolidation report",
            "- 🏠 **[Project Root](../)** - Return to main project directory",
            "- 📚 **[All Categories](#-documentation-catalog)** - Jump to category overview",
            "- 🚀 **[Quick Start](#-quick-start-guide)** - Get started immediately",
            "",
            "### Support & Feedback",
            "",
            "For questions, issues, or suggestions regarding this documentation:",
            "",
            "1. **Documentation Issues:** Check the migration log for recent changes",
            "2. **Missing Information:** Review the archive section for historical content",
            "3. **Technical Problems:** Contact the development team",
            "4. **Suggestions:** Propose improvements through the standard project channels",
            "",
            "*This documentation is maintained as part of the project's development workflow.*",
            "",
        ]
    
    def _generate_search_tips_section(self) -> List[str]:
        """Generate search and navigation tips section."""
        return [
            "## Navigation Tips",
            "",
            "### Finding Information",
            "- **By Feature:** Use the [features/](features/) directory for component-specific docs",
            "- **By Task:** Check [implementation/](implementation/) for completed work history",
            "- **By Type:** Browse categories in the table of contents above",
            "",
            "### Search Strategies",
            "- Use your IDE's search functionality to find specific terms across all docs",
            "- Check the [reference/](reference/) section for quick lookups",
            "- Review [archive/](archive/) for historical context if needed",
            "",
        ]
    
    def _generate_project_overview_section(self, file_analyses: List[FileAnalysis]) -> List[str]:
        """Generate project overview section."""
        # Count files by category
        category_counts = {}
        for analysis in file_analyses:
            category = analysis.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        sections = [
            "## Project Overview",
            "",
            "This Django project includes comprehensive documentation covering:",
            "",
        ]
        
        # Add category summaries
        category_descriptions = {
            Category.SETUP_CONFIG: "Installation and configuration procedures",
            Category.FEATURE_DOCS: "Feature-specific implementation guides",
            Category.INTEGRATION_GUIDES: "API and system integration documentation",
            Category.TESTING_VALIDATION: "Testing procedures and validation reports",
            Category.IMPLEMENTATION_COMPLETION: "Implementation history and completion records",
            Category.QUICK_REFERENCES: "Quick reference guides and troubleshooting",
            Category.HISTORICAL_ARCHIVE: "Historical documentation and deprecated content"
        }
        
        for category, count in category_counts.items():
            if count > 0 and category in category_descriptions:
                sections.append(f"- **{category_descriptions[category]}** ({count} documents)")
        
        sections.extend(["", ""])
        return sections
    
    def _generate_recent_updates_section(self, file_analyses: List[FileAnalysis]) -> List[str]:
        """Generate recent updates section."""
        # Find recently modified files
        recent_files = []
        for analysis in file_analyses:
            if analysis.metadata.last_modified:
                recent_files.append((analysis.metadata.last_modified, analysis.filename))
        
        # Sort by modification date (most recent first)
        recent_files.sort(reverse=True)
        
        sections = [
            "## Recent Updates",
            "",
        ]
        
        if recent_files:
            sections.append("Recently modified documentation:")
            sections.append("")
            
            for date, filename in recent_files[:5]:  # Show top 5
                sections.append(f"- **{filename}** - {date.strftime('%Y-%m-%d')}")
            
            sections.extend(["", ""])
        else:
            sections.extend([
                "No recent modification dates available.",
                "",
                ""
            ])
        
        return sections
    
    def _get_category_files(self, category: Category, 
                          file_analyses: List[FileAnalysis],
                          consolidated_groups: List[ConsolidationGroup]) -> List[Dict[str, str]]:
        """Get files for a specific category."""
        files = []
        
        # Add individual files
        for analysis in file_analyses:
            if analysis.category == category:
                files.append({
                    'title': analysis.filename.replace('.md', '').replace('_', ' '),
                    'path': f"{analysis.category.value}/{analysis.filename}",
                    'description': f"Word count: {analysis.metadata.word_count}"
                })
        
        # Add consolidated files
        for group in consolidated_groups:
            if group.category == category:
                files.append({
                    'title': group.output_filename.replace('.md', '').replace('_', ' '),
                    'path': f"{category.value}/{group.output_filename}",
                    'description': f"Consolidated from {group.total_files} files"
                })
        
        return files
    
    def _get_enhanced_category_files(self, category: Category, 
                                   file_analyses: List[FileAnalysis],
                                   consolidated_groups: List[ConsolidationGroup]) -> List[Dict[str, str]]:
        """Get enhanced file information for a specific category."""
        files = []
        
        # Add individual files with enhanced metadata
        for analysis in file_analyses:
            if analysis.category == category:
                # Create better title formatting
                title = self._format_file_title(analysis.filename)
                
                # Create enhanced description
                description = self._create_file_description(analysis)
                
                # Determine file type for grouping
                file_type = self._determine_file_type(analysis)
                
                files.append({
                    'title': title,
                    'path': f"{analysis.category.value}/{analysis.filename}",
                    'description': description,
                    'type': file_type,
                    'word_count': analysis.metadata.word_count,
                    'last_modified': analysis.metadata.last_modified
                })
        
        # Add consolidated files with enhanced metadata
        for group in consolidated_groups:
            if group.category == category:
                title = self._format_file_title(group.output_filename)
                description = f"📋 Consolidated guide combining {group.total_files} related documents"
                
                files.append({
                    'title': title,
                    'path': f"{category.value}/{group.output_filename}",
                    'description': description,
                    'type': 'Consolidated Guides',
                    'word_count': 0,  # Would need to calculate from consolidated content
                    'consolidated': True
                })
        
        # Sort files by type, then by title
        files.sort(key=lambda x: (x['type'], x['title']))
        
        return files
    
    def _get_category_icon(self, category: Category) -> str:
        """Get emoji icon for category."""
        icons = {
            Category.SETUP_CONFIG: "🛠️",
            Category.FEATURE_DOCS: "🎯",
            Category.INTEGRATION_GUIDES: "🔗",
            Category.TESTING_VALIDATION: "🧪",
            Category.QUICK_REFERENCES: "🔍",
            Category.IMPLEMENTATION_COMPLETION: "📊",
            Category.HISTORICAL_ARCHIVE: "📚",
            Category.UNCATEGORIZED: "📄"
        }
        return icons.get(category, "📄")
    
    def _get_enhanced_category_description(self, category: Category) -> str:
        """Get enhanced description for category."""
        descriptions = {
            Category.SETUP_CONFIG: "Complete installation guides, configuration procedures, and environment setup instructions",
            Category.FEATURE_DOCS: "Comprehensive documentation for all system features, organized by component and functionality",
            Category.INTEGRATION_GUIDES: "API documentation, integration procedures, and developer resources for system connectivity",
            Category.TESTING_VALIDATION: "Testing frameworks, validation procedures, test reports, and quality assurance documentation",
            Category.QUICK_REFERENCES: "Quick lookup guides, troubleshooting resources, and handy reference materials",
            Category.IMPLEMENTATION_COMPLETION: "Development history, implementation records, and project completion documentation",
            Category.HISTORICAL_ARCHIVE: "Historical documentation, deprecated content, and legacy system information",
            Category.UNCATEGORIZED: "Miscellaneous documentation that doesn't fit into other categories"
        }
        return descriptions.get(category, "")
    
    def _group_files_by_type(self, files: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Group files by their type for better organization."""
        grouped = {}
        
        for file_info in files:
            file_type = file_info.get('type', 'General Documentation')
            if file_type not in grouped:
                grouped[file_type] = []
            grouped[file_type].append(file_info)
        
        # Sort groups by priority
        type_priority = {
            'Setup Guides': 1,
            'Feature Guides': 2,
            'Consolidated Guides': 3,
            'API Documentation': 4,
            'Test Reports': 5,
            'Quick References': 6,
            'Implementation Records': 7,
            'General Documentation': 8,
            'Historical Documents': 9
        }
        
        sorted_grouped = {}
        for file_type in sorted(grouped.keys(), key=lambda x: type_priority.get(x, 10)):
            sorted_grouped[file_type] = grouped[file_type]
        
        return sorted_grouped
    
    def _format_file_title(self, filename: str) -> str:
        """Format filename into a readable title."""
        # Remove extension
        title = filename.replace('.md', '')
        
        # Handle common patterns
        title = title.replace('_', ' ')
        title = title.replace('-', ' ')
        
        # Handle specific patterns
        if title.upper().startswith('TASK '):
            # Convert TASK 5 1 COMPLETE to "Task 5.1 Complete"
            parts = title.split(' ')
            if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                task_num = f"{parts[1]}.{parts[2]}"
                rest = ' '.join(parts[3:])
                title = f"Task {task_num} {rest}"
        
        # Capitalize appropriately
        words = title.split()
        formatted_words = []
        
        for word in words:
            if word.upper() in ['API', 'URL', 'HTTP', 'JSON', 'XML', 'CSS', 'JS', 'HTML']:
                formatted_words.append(word.upper())
            elif word.lower() in ['and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with']:
                formatted_words.append(word.lower())
            else:
                formatted_words.append(word.capitalize())
        
        # Always capitalize first word
        if formatted_words:
            formatted_words[0] = formatted_words[0].capitalize()
        
        return ' '.join(formatted_words)
    
    def _create_file_description(self, analysis: FileAnalysis) -> str:
        """Create enhanced description for a file."""
        descriptions = []
        
        # Add content type information
        if analysis.content_type == ContentType.COMPLETION_SUMMARY:
            descriptions.append("📋 Implementation completion summary")
        elif analysis.content_type == ContentType.FEATURE_GUIDE:
            descriptions.append("🎯 Feature implementation guide")
        elif analysis.content_type == ContentType.SETUP_PROCEDURE:
            descriptions.append("🛠️ Setup and configuration guide")
        elif analysis.content_type == ContentType.TEST_REPORT:
            descriptions.append("🧪 Testing report and results")
        elif analysis.content_type == ContentType.QUICK_REFERENCE:
            descriptions.append("🔍 Quick reference guide")
        elif analysis.content_type == ContentType.INTEGRATION_GUIDE:
            descriptions.append("🔗 Integration and API guide")
        else:
            descriptions.append("📄 Documentation")
        
        # Add word count if significant
        if analysis.metadata.word_count > 0:
            if analysis.metadata.word_count > 2000:
                descriptions.append(f"({analysis.metadata.word_count:,} words - comprehensive)")
            elif analysis.metadata.word_count > 500:
                descriptions.append(f"({analysis.metadata.word_count} words)")
        
        # Add key topics if available
        if analysis.metadata.key_topics:
            topics = analysis.metadata.key_topics[:3]  # Show top 3 topics
            topics_str = ', '.join(topics)
            descriptions.append(f"Topics: {topics_str}")
        
        return ' • '.join(descriptions) if descriptions else "Documentation file"
    
    def _determine_file_type(self, analysis: FileAnalysis) -> str:
        """Determine file type for grouping."""
        filename_lower = analysis.filename.lower()
        
        # Check content type first
        if analysis.content_type == ContentType.COMPLETION_SUMMARY:
            return "Implementation Records"
        elif analysis.content_type == ContentType.FEATURE_GUIDE:
            return "Feature Guides"
        elif analysis.content_type == ContentType.SETUP_PROCEDURE:
            return "Setup Guides"
        elif analysis.content_type == ContentType.TEST_REPORT:
            return "Test Reports"
        elif analysis.content_type == ContentType.QUICK_REFERENCE:
            return "Quick References"
        elif analysis.content_type == ContentType.INTEGRATION_GUIDE:
            return "API Documentation"
        elif analysis.content_type == ContentType.HISTORICAL_DOC:
            return "Historical Documents"
        
        # Check filename patterns
        if 'api' in filename_lower or 'integration' in filename_lower:
            return "API Documentation"
        elif 'quick' in filename_lower or 'reference' in filename_lower:
            return "Quick References"
        elif 'test' in filename_lower or 'validation' in filename_lower:
            return "Test Reports"
        elif 'setup' in filename_lower or 'install' in filename_lower:
            return "Setup Guides"
        elif 'complete' in filename_lower or 'summary' in filename_lower:
            return "Implementation Records"
        
        return "General Documentation"
    
    def _calculate_documentation_statistics(self, file_analyses: List[FileAnalysis],
                                          consolidated_groups: List[ConsolidationGroup]) -> Dict[str, any]:
        """Calculate comprehensive documentation statistics."""
        stats = {
            'total_documents': len(file_analyses),
            'consolidated_groups': len(consolidated_groups),
            'total_words': sum(analysis.metadata.word_count for analysis in file_analyses),
            'categories_covered': len(set(analysis.category for analysis in file_analyses)),
            'category_breakdown': {},
            'features_covered': [],
            'internal_links': sum(len(analysis.metadata.internal_links) for analysis in file_analyses),
            'avg_document_length': 0,
            'coverage_score': 0,
            'last_updated': 'Unknown'
        }
        
        # Calculate category breakdown
        for analysis in file_analyses:
            category = analysis.category
            stats['category_breakdown'][category] = stats['category_breakdown'].get(category, 0) + 1
        
        # Calculate average document length
        if stats['total_documents'] > 0:
            stats['avg_document_length'] = stats['total_words'] // stats['total_documents']
        
        # Identify features covered
        features = set()
        for analysis in file_analyses:
            for topic in analysis.metadata.key_topics:
                if topic.lower() in ['payment', 'tournament', 'auth', 'notification', 'dashboard']:
                    features.add(topic.capitalize())
        stats['features_covered'] = sorted(list(features))
        
        # Calculate coverage score (simple heuristic)
        base_score = min(10, stats['categories_covered'] * 1.5)  # Up to 10 points for category coverage
        if stats['total_words'] > 10000:
            base_score += 1  # Bonus for comprehensive content
        if stats['internal_links'] > 20:
            base_score += 1  # Bonus for good cross-referencing
        stats['coverage_score'] = min(10, int(base_score))
        
        # Find last updated date
        last_dates = [analysis.metadata.last_modified for analysis in file_analyses 
                     if analysis.metadata.last_modified]
        if last_dates:
            stats['last_updated'] = max(last_dates).strftime('%Y-%m-%d')
        
        return stats
    
    def _calculate_update_frequency(self, recent_files: List[Dict[str, any]]) -> Dict[str, int]:
        """Calculate update frequency statistics."""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        stats = {
            'Last 7 days': 0,
            'Last 30 days': 0,
            'Last 90 days': 0,
            'Older': 0
        }
        
        for file_info in recent_files:
            file_date = file_info['date']
            days_ago = (now - file_date).days
            
            if days_ago <= 7:
                stats['Last 7 days'] += 1
            elif days_ago <= 30:
                stats['Last 30 days'] += 1
            elif days_ago <= 90:
                stats['Last 90 days'] += 1
            else:
                stats['Older'] += 1
        
        return stats
    
    def _determine_target_directory_for_consolidated(self, filename: str, 
                                                   structure: DocumentationStructure) -> str:
        """
        Determine target directory for a consolidated file based on its name.
        
        Args:
            filename: Name of the consolidated file
            structure: DocumentationStructure with category definitions
            
        Returns:
            Relative path to target directory
        """
        filename_lower = filename.lower()
        
        # Check for specific patterns in consolidated files
        if 'payment' in filename_lower:
            return "features/payments"
        elif 'tournament' in filename_lower:
            return "features/tournaments"
        elif 'auth' in filename_lower:
            return "features/authentication"
        elif 'notification' in filename_lower:
            return "features/notifications"
        elif 'dashboard' in filename_lower:
            return "features/dashboard"
        elif 'test' in filename_lower or 'validation' in filename_lower:
            return "testing"
        elif 'setup' in filename_lower or 'install' in filename_lower or 'config' in filename_lower:
            return "setup"
        elif 'complete' in filename_lower or 'summary' in filename_lower or 'implementation' in filename_lower:
            return "implementation"
        elif 'quick' in filename_lower or 'reference' in filename_lower:
            return "reference"
        elif 'integration' in filename_lower or 'api' in filename_lower:
            return "development"
        
        return "reference"  # Default location for consolidated files
    
    def _determine_target_directory_for_analysis(self, analysis: FileAnalysis, 
                                               structure: DocumentationStructure) -> Path:
        """
        Determine target directory path for a file analysis.
        
        Args:
            analysis: FileAnalysis object for the file
            structure: DocumentationStructure with category definitions
            
        Returns:
            Path object for the target directory
        """
        root_path = Path(structure.root_path)
        
        # Get category configuration
        category_config = structure.categories.get(analysis.category)
        if not category_config:
            self.logger.warning(f"No category config found for {analysis.category}, using uncategorized")
            return root_path / "uncategorized"
        
        target_dir = category_config.path
        
        # Determine if file should go in a subdirectory
        subdir = self._determine_subdirectory_enhanced(analysis, category_config)
        if subdir:
            target_dir = f"{target_dir}/{subdir}"
        
        return root_path / target_dir
    
    def _determine_subdirectory_enhanced(self, analysis: FileAnalysis, 
                                       config: DirectoryConfig) -> str:
        """
        Enhanced subdirectory determination with better logic.
        
        Args:
            analysis: FileAnalysis object for the file
            config: DirectoryConfig for the category
            
        Returns:
            Subdirectory name or empty string if no subdirectory needed
        """
        filename_lower = analysis.filename.lower()
        
        # Feature-specific subdirectory logic
        if config.path == "features":
            if 'payment' in filename_lower:
                return "payments"
            elif 'tournament' in filename_lower:
                return "tournaments"
            elif 'auth' in filename_lower or 'login' in filename_lower:
                return "authentication"
            elif 'notification' in filename_lower or 'notify' in filename_lower:
                return "notifications"
            elif 'dashboard' in filename_lower:
                return "dashboard"
        
        # Testing subdirectory logic
        elif config.path == "testing":
            if analysis.content_type == ContentType.TEST_REPORT:
                return "test-reports"
            elif 'validation' in filename_lower:
                return "validation-results"
        
        # Implementation subdirectory logic
        elif config.path == "implementation":
            if analysis.content_type == ContentType.COMPLETION_SUMMARY:
                return "completion-summaries"
            elif 'phase' in filename_lower:
                return "phase-summaries"
            elif 'task' in filename_lower:
                return "task-histories"
        
        # Archive subdirectory logic
        elif config.path == "archive":
            if analysis.is_outdated or analysis.preservation_priority == Priority.ARCHIVE:
                return "deprecated"
        
        # Check if filename matches any configured subdirectory patterns
        for subdir in config.subdirectories:
            subdir_lower = subdir.lower().replace('-', '').replace('_', '')
            filename_clean = filename_lower.replace('-', '').replace('_', '')
            
            if subdir_lower in filename_clean:
                return subdir
        
        return ""  # No subdirectory
    
    def _resolve_filename_conflict(self, filename: str, target_dir: Path, 
                                 used_filenames: Set[str]) -> str:
        """
        Resolve filename conflicts by adding numeric suffixes.
        
        Args:
            filename: Original filename
            target_dir: Target directory path
            used_filenames: Set of already used filenames in the directory
            
        Returns:
            Resolved filename that doesn't conflict
        """
        if filename not in used_filenames:
            # Check if file already exists in target directory
            if not (target_dir / filename).exists():
                return filename
        
        # Extract name and extension
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            base_name, extension = name_parts
            extension = f".{extension}"
        else:
            base_name = filename
            extension = ""
        
        # Try numeric suffixes
        counter = 1
        while counter <= 999:  # Reasonable limit
            new_filename = f"{base_name}_{counter:03d}{extension}"
            
            if (new_filename not in used_filenames and 
                not (target_dir / new_filename).exists()):
                self.logger.info(f"Resolved filename conflict: {filename} -> {new_filename}")
                return new_filename
            
            counter += 1
        
        # If we can't resolve after 999 attempts, use timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{base_name}_{timestamp}{extension}"
        self.logger.warning(f"Used timestamp to resolve filename conflict: {filename} -> {new_filename}")
        return new_filename
    
    def _write_file_with_integrity_check(self, target_path: Path, content: str) -> bool:
        """
        Write file content with integrity verification.
        
        Args:
            target_path: Path where to write the file
            content: Content to write
            
        Returns:
            True if write was successful and verified, False otherwise
        """
        try:
            # Write content
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verify by reading back
            with open(target_path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            
            if written_content == content:
                self.logger.debug(f"File integrity verified: {target_path}")
                return True
            else:
                self.logger.error(f"File integrity check failed: {target_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to write file {target_path}: {e}")
            return False
    
    def _move_file_with_integrity_check(self, source_path: Path, target_path: Path) -> bool:
        """
        Move file with integrity verification.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            True if move was successful and verified, False otherwise
        """
        try:
            # Read original content for verification
            with open(source_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Perform copy or move based on configuration
            if self.config.create_backups:
                shutil.copy2(source_path, target_path)
                self.logger.debug(f"Copied file (backup mode): {source_path} -> {target_path}")
            else:
                shutil.move(str(source_path), target_path)
                self.logger.debug(f"Moved file: {source_path} -> {target_path}")
            
            # Verify integrity by reading target file
            with open(target_path, 'r', encoding='utf-8') as f:
                target_content = f.read()
            
            if target_content == original_content:
                self.logger.debug(f"File move integrity verified: {target_path}")
                return True
            else:
                self.logger.error(f"File move integrity check failed: {source_path} -> {target_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to move file {source_path} -> {target_path}: {e}")
            return False
    
    def _get_consolidated_source_files(self, consolidated_docs: Dict[str, str], 
                                     file_analyses: List[FileAnalysis]) -> Set[str]:
        """
        Get set of source files that were used in consolidation.
        
        Args:
            consolidated_docs: Dictionary of consolidated document content
            file_analyses: List of all file analyses
            
        Returns:
            Set of source file paths that were consolidated
        """
        consolidated_files = set()
        
        # This is a simplified approach - in a real implementation, 
        # we would track which source files went into each consolidated document
        # For now, we'll identify files that likely were consolidated based on patterns
        
        for analysis in file_analyses:
            filename = analysis.filename
            
            # Check if this file's content might be in a consolidated document
            for consolidated_filename in consolidated_docs.keys():
                if (self._files_likely_consolidated(filename, consolidated_filename) or
                    self._content_likely_consolidated(analysis, consolidated_docs[consolidated_filename])):
                    consolidated_files.add(str(analysis.filepath))
                    break
        
        return consolidated_files
    
    def _files_likely_consolidated(self, original_filename: str, consolidated_filename: str) -> bool:
        """
        Check if an original file was likely consolidated into a consolidated file.
        
        Args:
            original_filename: Original file name
            consolidated_filename: Consolidated file name
            
        Returns:
            True if files are likely related through consolidation
        """
        original_lower = original_filename.lower()
        consolidated_lower = consolidated_filename.lower()
        
        # Check for common consolidation patterns
        if 'complete' in original_lower and 'summary' in consolidated_lower:
            return True
        
        if 'task' in original_lower and 'implementation' in consolidated_lower:
            return True
        
        # Check for feature-specific consolidation
        features = ['payment', 'tournament', 'auth', 'notification', 'dashboard']
        for feature in features:
            if feature in original_lower and feature in consolidated_lower:
                return True
        
        return False
    
    def _content_likely_consolidated(self, analysis: FileAnalysis, consolidated_content: str) -> bool:
        """
        Check if file content was likely included in consolidated content.
        
        Args:
            analysis: FileAnalysis for the original file
            consolidated_content: Content of the consolidated document
            
        Returns:
            True if content was likely consolidated
        """
        # Simple heuristic: check if key topics from the original file appear in consolidated content
        consolidated_lower = consolidated_content.lower()
        
        for topic in analysis.metadata.key_topics:
            if topic.lower() in consolidated_lower:
                return True
        
        # Check if filename (without extension) appears in consolidated content
        base_filename = analysis.filename.replace('.md', '').lower()
        if base_filename in consolidated_lower:
            return True
        
        return False
    
    def _determine_subdirectory(self, analysis: FileAnalysis, 
                              config: DirectoryConfig) -> str:
        """Determine subdirectory within a category for a file."""
        filename_lower = analysis.filename.lower()
        
        # Check if file matches any subdirectory patterns
        for subdir in config.subdirectories:
            if subdir.lower() in filename_lower:
                return subdir
        
        # Special cases based on content type
        if analysis.content_type.value == "test_report":
            return "test-reports"
        elif analysis.content_type.value == "completion_summary":
            return "completion-summaries"
        
        return ""  # No subdirectory
    
    def _generate_category_index(self, category: Category, 
                               config: DirectoryConfig,
                               organized_files: Dict[str, str]) -> str:
        """Generate index content for a category directory."""
        sections = []
        
        # Header
        category_name = config.path.replace('_', ' ').title()
        sections.append(f"# {category_name}")
        sections.append("")
        sections.append(config.description)
        sections.append("")
        
        # Find files in this category
        category_files = []
        for original_path, new_path in organized_files.items():
            if config.path in new_path:
                filename = Path(new_path).name
                category_files.append(filename)
        
        if category_files:
            sections.append("## Available Documentation")
            sections.append("")
            
            for filename in sorted(category_files):
                title = filename.replace('.md', '').replace('_', ' ').title()
                sections.append(f"- [{title}]({filename})")
            
            sections.append("")
        
        # Add subdirectory links if they exist
        if config.subdirectories:
            sections.append("## Subdirectories")
            sections.append("")
            
            for subdir in config.subdirectories:
                subdir_title = subdir.replace('-', ' ').replace('_', ' ').title()
                sections.append(f"- [{subdir_title}]({subdir}/)")
            
            sections.append("")
        
        # Footer
        sections.append("---")
        sections.append("")
        sections.append(f"[← Back to Documentation Index](../README.md)")
        
        return "\n".join(sections)
    
    def _generate_enhanced_category_index(self, category: Category, 
                                        config: DirectoryConfig,
                                        organized_files: Dict[str, str]) -> str:
        """Generate enhanced index content for a category directory."""
        sections = []
        
        # Enhanced Header with icon and description
        category_icon = self._get_category_icon(category)
        category_name = config.path.replace('_', ' ').title()
        sections.append(f"# {category_icon} {category_name}")
        sections.append("")
        
        # Enhanced description
        enhanced_desc = self._get_enhanced_category_description(category)
        if enhanced_desc:
            sections.append(enhanced_desc)
        else:
            sections.append(config.description)
        sections.append("")
        
        # Quick navigation
        sections.append("## 🚀 Quick Navigation")
        sections.append("")
        sections.append("| Resource | Description |")
        sections.append("|----------|-------------|")
        sections.append(f"| [📚 Main Documentation](../README.md) | Return to main documentation index |")
        
        # Add category-specific quick links
        quick_links = self._get_category_quick_links(category, config)
        for link_text, link_path, description in quick_links:
            sections.append(f"| [{link_text}]({link_path}) | {description} |")
        
        sections.append("")
        
        # Find and organize files in this category
        category_files = self._get_organized_category_files(config.path, organized_files)
        
        if category_files:
            # Group files by subdirectory
            files_by_subdir = self._group_files_by_subdirectory(category_files, config)
            
            sections.append("## 📋 Available Documentation")
            sections.append("")
            
            # Show files in main directory first
            main_files = files_by_subdir.get('', [])
            if main_files:
                sections.append("### Main Documentation")
                sections.append("")
                
                for file_info in sorted(main_files, key=lambda x: x['title']):
                    title = file_info['title']
                    filename = file_info['filename']
                    description = file_info.get('description', '')
                    
                    if description:
                        sections.append(f"- **[{title}]({filename})** - {description}")
                    else:
                        sections.append(f"- **[{title}]({filename})**")
                
                sections.append("")
            
            # Show files in subdirectories
            for subdir in config.subdirectories:
                subdir_files = files_by_subdir.get(subdir, [])
                if subdir_files:
                    subdir_title = subdir.replace('-', ' ').replace('_', ' ').title()
                    sections.append(f"### {subdir_title}")
                    sections.append("")
                    
                    for file_info in sorted(subdir_files, key=lambda x: x['title']):
                        title = file_info['title']
                        filename = file_info['filename']
                        description = file_info.get('description', '')
                        
                        if description:
                            sections.append(f"- **[{title}]({subdir}/{filename})** - {description}")
                        else:
                            sections.append(f"- **[{title}]({subdir}/{filename})**")
                    
                    sections.append("")
        
        # Add subdirectory navigation if they exist
        if config.subdirectories:
            sections.append("## 📁 Subdirectories")
            sections.append("")
            
            for subdir in config.subdirectories:
                subdir_title = subdir.replace('-', ' ').replace('_', ' ').title()
                subdir_desc = self._get_subdirectory_description(category, subdir)
                
                if subdir_desc:
                    sections.append(f"- **[{subdir_title}]({subdir}/)** - {subdir_desc}")
                else:
                    sections.append(f"- **[{subdir_title}]({subdir}/)**")
            
            sections.append("")
        
        # Category-specific help section
        help_section = self._generate_category_help_section(category)
        if help_section:
            sections.extend(help_section)
        
        # Enhanced Footer
        sections.append("---")
        sections.append("")
        sections.append("## 🔗 Related Resources")
        sections.append("")
        
        # Add related category links
        related_categories = self._get_related_categories(category)
        for related_cat, related_config in related_categories:
            related_icon = self._get_category_icon(related_cat)
            sections.append(f"- {related_icon} **[{related_config.description}](../{related_config.path}/)** - {self._get_enhanced_category_description(related_cat)[:100]}...")
        
        sections.append("")
        sections.append(f"📚 **[← Back to Main Documentation Index](../README.md)**")
        sections.append("")
        sections.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d')}*")
        
        return "\n".join(sections)
    
    def _find_broken_links(self, content: str, root_path: Path) -> List[str]:
        """Find broken internal links in content."""
        import re
        
        broken_links = []
        
        # Find all markdown links
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        
        for match in link_pattern.finditer(content):
            link_text = match.group(1)
            link_url = match.group(2)
            
            # Skip external links
            if link_url.startswith(('http://', 'https://', 'mailto:')):
                continue
            
            # Check if internal link exists
            link_path = root_path / link_url.lstrip('./')
            if not link_path.exists():
                broken_links.append(f"{link_text} -> {link_url}")
        
        return broken_links
    
    def _validate_structure_config(self, structure: DocumentationStructure) -> List[str]:
        """
        Validate the structure configuration before creating directories.
        
        Args:
            structure: DocumentationStructure to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate root path
        if not structure.root_path:
            errors.append("Root path cannot be empty")
        elif not structure.root_path.endswith('/'):
            # Ensure root path ends with slash for consistency
            structure.root_path += '/'
        
        # Validate categories
        if not structure.categories:
            errors.append("No categories defined in structure")
        
        # Check for duplicate paths among categories
        used_paths = set()
        for category, config in structure.categories.items():
            if config.path in used_paths:
                errors.append(f"Duplicate path found: {config.path}")
            used_paths.add(config.path)
            
            # Validate path format
            if not config.path or '/' in config.path:
                errors.append(f"Invalid category path: {config.path}")
        
        # Check if archive path conflicts with category paths (only if they're different)
        # If HISTORICAL_ARCHIVE category uses the same path as archive_section, that's OK
        archive_path = structure.archive_section.path
        historical_archive_path = None
        
        if Category.HISTORICAL_ARCHIVE in structure.categories:
            historical_archive_path = structure.categories[Category.HISTORICAL_ARCHIVE].path
        
        # Only flag as conflict if archive path conflicts with non-historical-archive categories
        if archive_path in used_paths and archive_path != historical_archive_path:
            errors.append(f"Archive path conflicts with category path: {archive_path}")
        
        return errors
    
    def _create_directory_with_permissions(self, directory_path: Path) -> bool:
        """
        Create a directory with proper permissions and error handling.
        
        Args:
            directory_path: Path object for the directory to create
            
        Returns:
            True if directory was created successfully, False otherwise
        """
        try:
            # Create directory with parents if needed
            directory_path.mkdir(parents=True, exist_ok=True)
            
            # Verify directory was created and is accessible
            if not directory_path.exists():
                self.logger.error(f"Directory was not created: {directory_path}")
                return False
            
            if not directory_path.is_dir():
                self.logger.error(f"Path exists but is not a directory: {directory_path}")
                return False
            
            # Test write permissions by creating a temporary file
            try:
                test_file = directory_path / ".write_test"
                test_file.touch()
                test_file.unlink()  # Clean up test file
            except (PermissionError, OSError) as e:
                self.logger.warning(f"Directory created but may have permission issues: {directory_path} - {e}")
                # Don't fail here as the directory might still be usable
            
            return True
            
        except PermissionError as e:
            self.logger.error(f"Permission denied creating directory {directory_path}: {e}")
            return False
        except OSError as e:
            self.logger.error(f"OS error creating directory {directory_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating directory {directory_path}: {e}")
            return False
    
    def _verify_directory_structure(self, structure: DocumentationStructure) -> bool:
        """
        Verify that all required directories were created correctly.
        
        Args:
            structure: DocumentationStructure that should have been created
            
        Returns:
            True if verification passed, False otherwise
        """
        root_path = Path(structure.root_path)
        
        # Check root directory
        if not root_path.exists() or not root_path.is_dir():
            self.logger.error(f"Root directory verification failed: {root_path}")
            return False
        
        # Check all category directories and subdirectories
        for category, config in structure.categories.items():
            category_path = root_path / config.path
            
            if not category_path.exists() or not category_path.is_dir():
                self.logger.error(f"Category directory verification failed: {category_path}")
                return False
            
            # Check subdirectories
            for subdir in config.subdirectories:
                # Special handling for deprecated subdirectory in archive category
                if (category == Category.HISTORICAL_ARCHIVE and 
                    subdir == "deprecated" and 
                    not structure.archive_section.include_deprecated):
                    self.logger.debug(f"Skipping deprecated subdirectory verification due to archive config")
                    continue
                
                subdir_path = category_path / subdir
                if not subdir_path.exists() or not subdir_path.is_dir():
                    self.logger.error(f"Subdirectory verification failed: {subdir_path}")
                    return False
        
        # Check archive directory
        archive_path = root_path / structure.archive_section.path
        if not archive_path.exists() or not archive_path.is_dir():
            self.logger.error(f"Archive directory verification failed: {archive_path}")
            return False
        
        # Check deprecated directory if it should exist
        if structure.archive_section.include_deprecated:
            deprecated_path = archive_path / "deprecated"
            if not deprecated_path.exists() or not deprecated_path.is_dir():
                self.logger.error(f"Deprecated directory verification failed: {deprecated_path}")
                return False
        
        self.logger.debug("Directory structure verification passed")
        return True
    def _get_category_quick_links(self, category: Category, config: DirectoryConfig) -> List[Tuple[str, str, str]]:
        """Get quick links for a category."""
        links = []
        
        if category == Category.SETUP_CONFIG:
            links.extend([
                ("🛠️ Installation Guide", "installation.md", "Complete setup instructions"),
                ("⚙️ Configuration", "configuration.md", "System configuration options"),
                ("🔧 Troubleshooting", "troubleshooting.md", "Common setup issues")
            ])
        elif category == Category.FEATURE_DOCS:
            links.extend([
                ("💳 Payment System", "payments/", "Payment processing documentation"),
                ("🏆 Tournament System", "tournaments/", "Tournament management guides"),
                ("🔐 Authentication", "authentication/", "User authentication system")
            ])
        elif category == Category.INTEGRATION_GUIDES:
            links.extend([
                ("🚀 Quick Start", "quick-start.md", "Get started in 15 minutes"),
                ("🔗 API Reference", "api-reference.md", "Complete API documentation"),
                ("🧪 Testing Guide", "testing-guide.md", "Integration testing procedures")
            ])
        elif category == Category.TESTING_VALIDATION:
            links.extend([
                ("🧪 Test Procedures", "testing-procedures.md", "How to run tests"),
                ("📊 Test Reports", "test-reports/", "Latest test execution results"),
                ("✅ Validation Results", "validation-results/", "System validation reports")
            ])
        elif category == Category.QUICK_REFERENCES:
            links.extend([
                ("🔍 Quick References", "quick-references.md", "Handy lookup guides"),
                ("🆘 Troubleshooting", "troubleshooting.md", "Common issues and solutions"),
                ("📖 Glossary", "glossary.md", "Terms and definitions")
            ])
        elif category == Category.IMPLEMENTATION_COMPLETION:
            links.extend([
                ("📋 Completion Summary", "completion-summary.md", "Overall implementation status"),
                ("📊 Phase Summaries", "phase-summaries/", "Implementation by phase"),
                ("📝 Task Histories", "task-histories/", "Detailed task completion records")
            ])
        
        return links
    
    def _get_organized_category_files(self, category_path: str, organized_files: Dict[str, str]) -> List[Dict[str, str]]:
        """Get organized file information for a category."""
        files = []
        
        for original_path, new_path in organized_files.items():
            if category_path in new_path:
                path_obj = Path(new_path)
                filename = path_obj.name
                
                # Determine if file is in a subdirectory
                relative_path = path_obj.relative_to(Path(new_path).parts[0])  # Remove docs/ part
                path_parts = relative_path.parts
                
                subdir = ""
                if len(path_parts) > 2:  # docs/category/subdir/file.md
                    subdir = path_parts[1]
                
                title = self._format_file_title(filename)
                
                files.append({
                    'title': title,
                    'filename': filename,
                    'subdir': subdir,
                    'original_path': original_path,
                    'description': self._get_file_description_from_path(original_path)
                })
        
        return files
    
    def _group_files_by_subdirectory(self, files: List[Dict[str, str]], config: DirectoryConfig) -> Dict[str, List[Dict[str, str]]]:
        """Group files by subdirectory."""
        grouped = {}
        
        for file_info in files:
            subdir = file_info.get('subdir', '')
            if subdir not in grouped:
                grouped[subdir] = []
            grouped[subdir].append(file_info)
        
        return grouped
    
    def _get_subdirectory_description(self, category: Category, subdir: str) -> str:
        """Get description for a subdirectory."""
        descriptions = {
            # Feature subdirectories
            'authentication': 'User authentication and authorization system documentation',
            'payments': 'Payment processing and financial transaction guides',
            'tournaments': 'Tournament management and competition system docs',
            'notifications': 'Notification system and messaging documentation',
            'dashboard': 'Dashboard and user interface documentation',
            
            # Testing subdirectories
            'test-reports': 'Automated test execution results and reports',
            'validation-results': 'System validation and compliance reports',
            
            # Implementation subdirectories
            'completion-summaries': 'High-level implementation completion reports',
            'phase-summaries': 'Implementation progress by development phase',
            'task-histories': 'Detailed task-by-task completion records',
            
            # Archive subdirectories
            'deprecated': 'Outdated documentation preserved for reference'
        }
        
        return descriptions.get(subdir, '')
    
    def _generate_category_help_section(self, category: Category) -> List[str]:
        """Generate category-specific help section."""
        if category == Category.SETUP_CONFIG:
            return [
                "## 🆘 Getting Help with Setup",
                "",
                "**Common Setup Issues:**",
                "1. **Environment Problems:** Check [troubleshooting.md](troubleshooting.md)",
                "2. **Dependency Issues:** Review [installation.md](installation.md) requirements",
                "3. **Configuration Errors:** Consult [configuration.md](configuration.md)",
                "",
                "**Still Need Help?**",
                "- Check the [main troubleshooting guide](../reference/troubleshooting.md)",
                "- Review [implementation history](../implementation/) for context",
                "- Contact the development team",
                "",
            ]
        elif category == Category.FEATURE_DOCS:
            return [
                "## 🎯 Feature Documentation Guide",
                "",
                "**Understanding Features:**",
                "- Each feature has its own subdirectory with comprehensive docs",
                "- Start with the main feature guide in each subdirectory",
                "- Check [integration guides](../development/) for feature interactions",
                "",
                "**Implementation Status:**",
                "- Review [implementation records](../implementation/) for completion status",
                "- Check [test reports](../testing/) for feature validation",
                "",
            ]
        elif category == Category.TESTING_VALIDATION:
            return [
                "## 🧪 Testing Guide",
                "",
                "**Running Tests:**",
                "1. Follow procedures in [testing-procedures.md](testing-procedures.md)",
                "2. Check [test reports](test-reports/) for latest results",
                "3. Review [validation results](validation-results/) for compliance",
                "",
                "**Writing Tests:**",
                "- Follow patterns in existing test documentation",
                "- Check [development guides](../development/) for testing standards",
                "",
            ]
        
        return []
    
    def _get_related_categories(self, category: Category) -> List[Tuple[Category, DirectoryConfig]]:
        """Get related categories for cross-referencing."""
        # This would ideally be configured, but for now we'll use some logical relationships
        relationships = {
            Category.SETUP_CONFIG: [Category.INTEGRATION_GUIDES, Category.TESTING_VALIDATION],
            Category.FEATURE_DOCS: [Category.INTEGRATION_GUIDES, Category.IMPLEMENTATION_COMPLETION],
            Category.INTEGRATION_GUIDES: [Category.FEATURE_DOCS, Category.TESTING_VALIDATION],
            Category.TESTING_VALIDATION: [Category.SETUP_CONFIG, Category.INTEGRATION_GUIDES],
            Category.QUICK_REFERENCES: [Category.FEATURE_DOCS, Category.INTEGRATION_GUIDES],
            Category.IMPLEMENTATION_COMPLETION: [Category.FEATURE_DOCS, Category.TESTING_VALIDATION],
            Category.HISTORICAL_ARCHIVE: [Category.IMPLEMENTATION_COMPLETION]
        }
        
        related = []
        related_categories = relationships.get(category, [])
        
        # This would need access to the full structure, so we'll return empty for now
        # In a real implementation, this would be passed in or stored as instance variable
        return related
    
    def _get_file_description_from_path(self, original_path: str) -> str:
        """Get file description based on original path patterns."""
        path_lower = original_path.lower()
        
        if 'complete' in path_lower:
            return "Implementation completion record"
        elif 'test' in path_lower:
            return "Testing documentation"
        elif 'setup' in path_lower:
            return "Setup and configuration guide"
        elif 'payment' in path_lower:
            return "Payment system documentation"
        elif 'tournament' in path_lower:
            return "Tournament management guide"
        elif 'auth' in path_lower:
            return "Authentication system documentation"
        elif 'quick' in path_lower:
            return "Quick reference guide"
        elif 'integration' in path_lower:
            return "Integration documentation"
        
        return ""