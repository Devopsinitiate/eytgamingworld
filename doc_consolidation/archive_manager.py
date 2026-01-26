"""
Archive Manager module for the Documentation Consolidation System.

This module implements archive section creation functionality as part of Task 6.2.
It provides methods to create archive directory structure, move historical documentation
to archive, and add freshness indicators to outdated content.

Requirements implemented: 7.3, 7.4
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import (
    FileAnalysis, DocumentationStructure, ArchiveConfig, 
    Category, Priority, MigrationLog
)
from .outdated_content_detector import OutdatedContentDetector


class ArchiveManager:
    """
    Manages archive section creation and historical documentation organization.
    
    This class implements the archive section creation functionality required by
    Task 6.2, including directory structure creation, file movement, and freshness
    indicator management.
    """
    
    def __init__(self, structure: DocumentationStructure):
        """
        Initialize the archive manager.
        
        Args:
            structure: DocumentationStructure containing archive configuration
        """
        self.structure = structure
        self.archive_config = structure.archive_section
        self.migration_log = structure.migration_log
        self.logger = logging.getLogger('doc_consolidation.archive_manager')
        
        # Initialize outdated content detector for identifying archive candidates
        self.outdated_detector = OutdatedContentDetector()
    
    def create_archive_directory_structure(self) -> bool:
        """
        Create archive/ directory structure.
        
        Implements Requirement 7.3: Create archive section for historical documentation.
        
        Returns:
            True if archive directory structure was created successfully, False otherwise
        """
        self.logger.info("Creating archive directory structure")
        
        try:
            root_path = Path(self.structure.root_path)
            archive_path = root_path / self.archive_config.path
            
            # Create main archive directory
            if not self._create_directory_safely(archive_path):
                return False
            
            self.logger.info(f"Created main archive directory: {archive_path}")
            
            # Create deprecated subdirectory if configured
            if self.archive_config.include_deprecated:
                deprecated_path = archive_path / "deprecated"
                if not self._create_directory_safely(deprecated_path):
                    return False
                
                self.logger.info(f"Created deprecated subdirectory: {deprecated_path}")
            
            # Create additional archive subdirectories for organization
            archive_subdirs = [
                "legacy-features",      # For deprecated feature documentation
                "old-implementations",  # For superseded implementation guides
                "historical-reports",   # For old test reports and validation results
                "migration-records"     # For migration logs and consolidation records
            ]
            
            for subdir in archive_subdirs:
                subdir_path = archive_path / subdir
                if not self._create_directory_safely(subdir_path):
                    self.logger.warning(f"Failed to create archive subdirectory: {subdir_path}")
                    continue
                
                self.logger.debug(f"Created archive subdirectory: {subdir_path}")
            
            # Create archive index file
            if not self._create_archive_index(archive_path):
                self.logger.warning("Failed to create archive index file")
            
            # Log operation
            self.migration_log.add_operation(
                "create_archive_structure",
                str(archive_path),
                "",
                f"Created archive directory structure with {len(archive_subdirs) + 1} subdirectories"
            )
            
            self.logger.info("Archive directory structure created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create archive directory structure: {e}")
            self.migration_log.add_error(f"Archive structure creation failed: {e}")
            return False
    
    def move_historical_documentation_to_archive(self, file_analyses: List[FileAnalysis]) -> Dict[str, str]:
        """
        Move historical documentation to archive.
        
        Implements Requirement 7.3: Move historical documentation to archive.
        
        Args:
            file_analyses: List of FileAnalysis objects for all discovered files
            
        Returns:
            Dictionary mapping original file paths to new archive locations
        """
        self.logger.info("Moving historical documentation to archive")
        
        # Identify files that should be archived
        outdated_content = self.outdated_detector.identify_outdated_content(file_analyses)
        archive_candidates = outdated_content.get('archive_candidates', [])
        
        # Also check for files explicitly marked for archival
        additional_archive_files = [
            analysis for analysis in file_analyses 
            if (analysis.preservation_priority == Priority.ARCHIVE or
                analysis.category == Category.HISTORICAL_ARCHIVE)
        ]
        
        # Combine and deduplicate archive candidates
        all_archive_files = list({analysis.filepath: analysis for analysis in 
                                (archive_candidates + additional_archive_files)}.values())
        
        self.logger.info(f"Identified {len(all_archive_files)} files for archival")
        
        moved_files = {}
        root_path = Path(self.structure.root_path)
        archive_path = root_path / self.archive_config.path
        
        for analysis in all_archive_files:
            try:
                # Determine appropriate archive subdirectory
                target_subdir = self._determine_archive_subdirectory(analysis)
                target_dir = archive_path / target_subdir
                
                # Ensure target directory exists
                if not self._create_directory_safely(target_dir):
                    self.logger.error(f"Failed to create archive subdirectory: {target_dir}")
                    continue
                
                # Determine target filename (handle conflicts)
                target_filename = self._resolve_archive_filename_conflict(
                    analysis.filename, target_dir
                )
                target_path = target_dir / target_filename
                
                # Move file to archive with freshness indicators
                if self._move_file_to_archive_with_indicators(analysis, target_path):
                    moved_files[str(analysis.filepath)] = str(target_path)
                    
                    # Log the operation
                    self.migration_log.add_operation(
                        "archive_file",
                        str(analysis.filepath),
                        str(target_path),
                        f"Archived to {target_subdir}: {analysis.processing_notes[-1] if analysis.processing_notes else 'Historical content'}"
                    )
                    
                    self.migration_log.files_archived += 1
                    self.logger.debug(f"Archived file: {analysis.filepath} -> {target_path}")
                else:
                    self.logger.error(f"Failed to archive file: {analysis.filepath}")
                    
            except Exception as e:
                self.logger.error(f"Error archiving file {analysis.filepath}: {e}")
                self.migration_log.add_error(f"Failed to archive {analysis.filepath}: {e}")
        
        self.logger.info(f"Successfully archived {len(moved_files)} files")
        return moved_files
    
    def add_freshness_indicators_to_outdated_content(self, file_analyses: List[FileAnalysis]) -> Dict[str, str]:
        """
        Add freshness indicators to outdated content.
        
        Implements Requirement 7.4: Add freshness indicators to outdated content.
        
        Args:
            file_analyses: List of FileAnalysis objects for all discovered files
            
        Returns:
            Dictionary mapping file paths to their freshness indicators
        """
        self.logger.info("Adding freshness indicators to outdated content")
        
        # Get freshness indicators from outdated content detector
        freshness_indicators = self.outdated_detector.create_freshness_indicators(file_analyses)
        
        # Create a comprehensive freshness report
        freshness_report_path = Path(self.structure.root_path) / self.archive_config.path / "freshness-report.md"
        
        if self._create_freshness_report(freshness_indicators, freshness_report_path):
            self.logger.info(f"Created freshness report: {freshness_report_path}")
        
        # Add freshness indicators to individual files that are not being archived
        updated_files = {}
        
        for analysis in file_analyses:
            # Skip files that are being archived
            if (analysis.preservation_priority == Priority.ARCHIVE or
                analysis.category == Category.HISTORICAL_ARCHIVE):
                continue
            
            filepath_str = str(analysis.filepath)
            if filepath_str in freshness_indicators:
                indicator = freshness_indicators[filepath_str]
                
                # Add freshness indicator to file if it's outdated
                if self._should_add_freshness_indicator(indicator):
                    if self._add_freshness_indicator_to_file(analysis.filepath, indicator):
                        updated_files[filepath_str] = indicator
                        self.logger.debug(f"Added freshness indicator to: {analysis.filepath}")
        
        self.logger.info(f"Added freshness indicators to {len(updated_files)} files")
        return updated_files
    
    def create_archive_migration_log(self, moved_files: Dict[str, str]) -> bool:
        """
        Create detailed migration log for archive operations.
        
        Args:
            moved_files: Dictionary mapping original paths to archive locations
            
        Returns:
            True if migration log was created successfully, False otherwise
        """
        self.logger.info("Creating archive migration log")
        
        try:
            archive_path = Path(self.structure.root_path) / self.archive_config.path
            log_path = archive_path / "migration-log.md"
            
            sections = []
            
            # Header
            sections.append("# Archive Migration Log")
            sections.append("")
            sections.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            sections.append(f"**Archive Path:** `{self.archive_config.path}/`")
            sections.append("")
            
            # Summary
            sections.append("## Migration Summary")
            sections.append("")
            sections.append(f"- **Files Archived:** {len(moved_files)}")
            sections.append(f"- **Archive Policy:** {self.archive_config.retention_policy}")
            sections.append(f"- **Include Deprecated:** {self.archive_config.include_deprecated}")
            sections.append("")
            
            # Detailed file movements
            if moved_files:
                sections.append("## Archived Files")
                sections.append("")
                sections.append("| Original Location | Archive Location | Reason |")
                sections.append("|-------------------|------------------|--------|")
                
                for original, archived in moved_files.items():
                    # Extract reason from migration log operations
                    reason = "Historical content"
                    for op in self.migration_log.operations:
                        if op.get('source') == original and op.get('type') == 'archive_file':
                            reason = op.get('details', reason)
                            break
                    
                    # Make paths relative for readability
                    original_rel = Path(original).name
                    archived_rel = str(Path(archived).relative_to(Path(self.structure.root_path)))
                    
                    sections.append(f"| `{original_rel}` | `{archived_rel}` | {reason} |")
                
                sections.append("")
            
            # Archive structure
            sections.append("## Archive Structure")
            sections.append("")
            sections.append("The archive is organized into the following subdirectories:")
            sections.append("")
            sections.append("- **`deprecated/`** - Deprecated content that may still have reference value")
            sections.append("- **`legacy-features/`** - Documentation for removed or superseded features")
            sections.append("- **`old-implementations/`** - Superseded implementation guides and procedures")
            sections.append("- **`historical-reports/`** - Old test reports and validation results")
            sections.append("- **`migration-records/`** - Migration logs and consolidation records")
            sections.append("")
            
            # Access instructions
            sections.append("## Accessing Archived Content")
            sections.append("")
            sections.append("Archived content is preserved for reference but is not part of the main documentation.")
            sections.append("To access archived content:")
            sections.append("")
            sections.append("1. Browse the archive directory structure above")
            sections.append("2. Check the freshness report for content age information")
            sections.append("3. Review individual files for historical context")
            sections.append("")
            sections.append("**Note:** Archived content may be outdated and should not be used for current development.")
            sections.append("")
            
            # Footer
            sections.append("---")
            sections.append("")
            sections.append("*This log was generated automatically by the Documentation Consolidation System.*")
            
            # Write migration log
            log_content = "\n".join(sections)
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            self.logger.info(f"Archive migration log created: {log_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create archive migration log: {e}")
            return False
    
    def validate_archive_structure(self) -> List[str]:
        """
        Validate the created archive structure.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        root_path = Path(self.structure.root_path)
        archive_path = root_path / self.archive_config.path
        
        # Check main archive directory
        if not archive_path.exists():
            errors.append(f"Archive directory does not exist: {archive_path}")
            return errors
        
        if not archive_path.is_dir():
            errors.append(f"Archive path is not a directory: {archive_path}")
            return errors
        
        # Check required subdirectories
        required_subdirs = ["deprecated"] if self.archive_config.include_deprecated else []
        
        for subdir in required_subdirs:
            subdir_path = archive_path / subdir
            if not subdir_path.exists():
                errors.append(f"Required archive subdirectory missing: {subdir_path}")
        
        # Check for archive index
        index_path = archive_path / "README.md"
        if not index_path.exists():
            errors.append(f"Archive index missing: {index_path}")
        
        # Check migration log if configured
        if self.archive_config.include_migration_log:
            log_path = archive_path / "migration-log.md"
            if not log_path.exists():
                errors.append(f"Migration log missing: {log_path}")
        
        return errors
    
    # Helper methods
    
    def _create_directory_safely(self, directory_path: Path) -> bool:
        """
        Create a directory with proper error handling.
        
        Args:
            directory_path: Path to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            directory_path.mkdir(parents=True, exist_ok=True)
            return True
        except (PermissionError, OSError) as e:
            self.logger.error(f"Failed to create directory {directory_path}: {e}")
            return False
    
    def _create_archive_index(self, archive_path: Path) -> bool:
        """
        Create README.md index file for the archive directory.
        
        Args:
            archive_path: Path to the archive directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            index_path = archive_path / "README.md"
            
            sections = []
            
            # Header
            sections.append("# 📚 Documentation Archive")
            sections.append("")
            sections.append("This directory contains historical documentation that has been archived ")
            sections.append("for reference purposes. The content here may be outdated and should not ")
            sections.append("be used for current development activities.")
            sections.append("")
            
            # Purpose
            sections.append("## Purpose")
            sections.append("")
            sections.append("The archive serves several important functions:")
            sections.append("")
            sections.append("- **Historical Reference:** Preserve implementation history and decisions")
            sections.append("- **Legacy Support:** Maintain documentation for deprecated features")
            sections.append("- **Audit Trail:** Keep records of system evolution and changes")
            sections.append("- **Knowledge Preservation:** Retain institutional knowledge and context")
            sections.append("")
            
            # Structure
            sections.append("## Archive Structure")
            sections.append("")
            sections.append("### Subdirectories")
            sections.append("")
            sections.append("- **`deprecated/`** - Content that is no longer current but may have reference value")
            sections.append("- **`legacy-features/`** - Documentation for removed or superseded system features")
            sections.append("- **`old-implementations/`** - Previous implementation approaches and procedures")
            sections.append("- **`historical-reports/`** - Test reports, validation results, and analysis from past phases")
            sections.append("- **`migration-records/`** - Logs and records from documentation consolidation processes")
            sections.append("")
            
            # Usage guidelines
            sections.append("## Usage Guidelines")
            sections.append("")
            sections.append("### ⚠️ Important Warnings")
            sections.append("")
            sections.append("- **Outdated Information:** Content may not reflect current system state")
            sections.append("- **Deprecated Procedures:** Setup and configuration steps may no longer work")
            sections.append("- **Legacy Code:** Code examples may be incompatible with current versions")
            sections.append("- **Historical Context:** Information is preserved for reference, not active use")
            sections.append("")
            
            sections.append("### ✅ Appropriate Uses")
            sections.append("")
            sections.append("- Understanding historical implementation decisions")
            sections.append("- Researching previous approaches to similar problems")
            sections.append("- Maintaining legacy system components")
            sections.append("- Conducting system evolution analysis")
            sections.append("")
            
            # Navigation
            sections.append("## Navigation")
            sections.append("")
            sections.append("### Quick Links")
            sections.append("")
            sections.append("- 📋 **[Migration Log](migration-log.md)** - Detailed record of archival operations")
            sections.append("- 📊 **[Freshness Report](freshness-report.md)** - Content age and freshness analysis")
            sections.append("- 🏠 **[Main Documentation](../README.md)** - Return to current documentation")
            sections.append("")
            
            sections.append("### Finding Content")
            sections.append("")
            sections.append("1. **Browse by Category:** Use the subdirectories above to find content by type")
            sections.append("2. **Check Migration Log:** Review what was archived and when")
            sections.append("3. **Search by Topic:** Use your IDE or grep to search across archived content")
            sections.append("4. **Review Freshness Report:** Understand content age and relevance")
            sections.append("")
            
            # Maintenance
            sections.append("## Archive Maintenance")
            sections.append("")
            sections.append(f"**Retention Policy:** {self.archive_config.retention_policy}")
            sections.append(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}")
            sections.append("")
            sections.append("The archive is maintained automatically by the Documentation Consolidation System. ")
            sections.append("Content is moved here based on age, relevance, and deprecation status.")
            sections.append("")
            
            # Footer
            sections.append("---")
            sections.append("")
            sections.append("*For questions about archived content, consult the migration log or contact the development team.*")
            
            # Write index file
            index_content = "\n".join(sections)
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create archive index: {e}")
            return False
    
    def _determine_archive_subdirectory(self, analysis: FileAnalysis) -> str:
        """
        Determine appropriate archive subdirectory for a file.
        
        Args:
            analysis: FileAnalysis object for the file
            
        Returns:
            Subdirectory name within archive
        """
        filename_lower = analysis.filename.lower()
        
        # Check processing notes for specific archival reasons
        archival_reason = ""
        for note in analysis.processing_notes:
            if "archive candidate:" in note.lower():
                archival_reason = note.lower()
                break
        
        # Determine subdirectory based on content and reason
        if "deprecated" in archival_reason or "obsolete" in filename_lower:
            return "deprecated"
        elif "feature" in archival_reason or analysis.category.value == "feature_docs":
            return "legacy-features"
        elif "implementation" in archival_reason or "complete" in filename_lower:
            return "old-implementations"
        elif "test" in filename_lower or "report" in filename_lower or "validation" in filename_lower:
            return "historical-reports"
        elif "migration" in filename_lower or "log" in filename_lower:
            return "migration-records"
        else:
            # Default to deprecated for general historical content
            return "deprecated"
    
    def _resolve_archive_filename_conflict(self, filename: str, target_dir: Path) -> str:
        """
        Resolve filename conflicts in archive directory.
        
        Args:
            filename: Original filename
            target_dir: Target archive subdirectory
            
        Returns:
            Resolved filename that doesn't conflict
        """
        if not (target_dir / filename).exists():
            return filename
        
        # Add timestamp suffix to resolve conflict
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            base_name, extension = name_parts
            extension = f".{extension}"
        else:
            base_name = filename
            extension = ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{base_name}_archived_{timestamp}{extension}"
        
        self.logger.info(f"Resolved archive filename conflict: {filename} -> {new_filename}")
        return new_filename
    
    def _move_file_to_archive_with_indicators(self, analysis: FileAnalysis, target_path: Path) -> bool:
        """
        Move file to archive and add freshness indicators.
        
        Args:
            analysis: FileAnalysis object for the file
            target_path: Target path in archive
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read original content
            try:
                with open(analysis.filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                try:
                    with open(analysis.filepath, 'r', encoding='cp1252') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(analysis.filepath, 'r', encoding='latin1') as f:
                        content = f.read()
            
            # Add archive header with freshness indicators
            archive_header = self._create_archive_header(analysis)
            archived_content = f"{archive_header}\n\n{content}"
            
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to archive location
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(archived_content)
            
            # Remove original file if not in backup mode
            # For testing and safety, we'll always keep the original file
            # In production, this could be configurable
            # if not getattr(self, 'backup_mode', True):  # Default to backup mode for safety
            #     analysis.filepath.unlink()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move file to archive: {analysis.filepath} -> {target_path}: {e}")
            return False
    
    def _create_archive_header(self, analysis: FileAnalysis) -> str:
        """
        Create archive header with freshness indicators and metadata.
        
        Args:
            analysis: FileAnalysis object for the file
            
        Returns:
            Archive header as markdown string
        """
        sections = []
        
        sections.append("---")
        sections.append("# ⚠️ ARCHIVED CONTENT")
        sections.append("")
        sections.append("**This document has been archived and may contain outdated information.**")
        sections.append("")
        
        # Archive metadata
        sections.append("## Archive Information")
        sections.append("")
        sections.append(f"- **Archived Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"- **Original Location:** `{analysis.filepath.name}`")
        sections.append(f"- **Content Type:** {analysis.content_type.value.replace('_', ' ').title()}")
        sections.append(f"- **Category:** {analysis.category.value.replace('_', ' ').title()}")
        
        if analysis.metadata.last_modified:
            sections.append(f"- **Last Modified:** {analysis.metadata.last_modified.strftime('%Y-%m-%d')}")
        
        sections.append("")
        
        # Freshness indicator
        freshness_indicators = self.outdated_detector.create_freshness_indicators([analysis])
        filepath_key = str(analysis.filepath)
        
        # Try different key formats to find the freshness indicator
        indicator = None
        for key in [filepath_key, analysis.filename, str(analysis.filepath.name)]:
            if key in freshness_indicators:
                indicator = freshness_indicators[key]
                break
        
        if indicator:
            sections.append(f"**Freshness Status:** {indicator}")
            sections.append("")
        else:
            # Create a basic freshness indicator if none found
            if analysis.metadata.last_modified:
                age_days = (datetime.now() - analysis.metadata.last_modified).days
                if age_days > 365:
                    basic_indicator = f"⚫ Old (last updated {age_days} days ago)"
                elif age_days > 180:
                    basic_indicator = f"🔴 Stale (last updated {age_days} days ago)"
                elif age_days > 90:
                    basic_indicator = f"🟠 Aging (last updated {age_days} days ago)"
                else:
                    basic_indicator = f"🟡 Recent (last updated {age_days} days ago)"
                
                sections.append(f"**Freshness Status:** {basic_indicator}")
                sections.append("")
        
        # Archive reason
        if analysis.processing_notes:
            archive_notes = [note for note in analysis.processing_notes if "archive" in note.lower()]
            if archive_notes:
                sections.append("**Archive Reason:**")
                for note in archive_notes:
                    sections.append(f"- {note}")
                sections.append("")
        
        # Warning
        sections.append("⚠️ **Use this content with caution - it may not reflect current system state.**")
        sections.append("")
        sections.append("---")
        
        return "\n".join(sections)
    
    def _create_freshness_report(self, freshness_indicators: Dict[str, str], report_path: Path) -> bool:
        """
        Create comprehensive freshness report.
        
        Args:
            freshness_indicators: Dictionary mapping file paths to freshness indicators
            report_path: Path where to save the report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            sections = []
            
            # Header
            sections.append("# 📊 Content Freshness Report")
            sections.append("")
            sections.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            sections.append(f"**Total Files Analyzed:** {len(freshness_indicators)}")
            sections.append("")
            
            # Summary statistics
            freshness_stats = self._calculate_freshness_statistics(freshness_indicators)
            
            sections.append("## Freshness Summary")
            sections.append("")
            sections.append("| Status | Count | Percentage |")
            sections.append("|--------|-------|------------|")
            
            for status, count in freshness_stats.items():
                percentage = (count / len(freshness_indicators)) * 100 if freshness_indicators else 0
                sections.append(f"| {status} | {count} | {percentage:.1f}% |")
            
            sections.append("")
            
            # Detailed file listing
            sections.append("## Detailed File Analysis")
            sections.append("")
            sections.append("| File | Freshness Status | Recommendation |")
            sections.append("|------|------------------|----------------|")
            
            # Sort files by freshness (most concerning first)
            sorted_files = sorted(freshness_indicators.items(), 
                                key=lambda x: self._get_freshness_priority(x[1]))
            
            for filepath, indicator in sorted_files:
                filename = Path(filepath).name
                recommendation = self._get_freshness_recommendation(indicator)
                sections.append(f"| `{filename}` | {indicator} | {recommendation} |")
            
            sections.append("")
            
            # Recommendations
            sections.append("## Recommendations")
            sections.append("")
            sections.append("### Immediate Action Required")
            sections.append("")
            
            urgent_files = [f for f, i in freshness_indicators.items() if "⚫ Old" in i]
            if urgent_files:
                sections.append("The following files are very old and should be reviewed:")
                sections.append("")
                for filepath in urgent_files[:10]:  # Show top 10
                    sections.append(f"- `{Path(filepath).name}`")
                sections.append("")
            else:
                sections.append("No files require immediate attention.")
                sections.append("")
            
            sections.append("### Maintenance Guidelines")
            sections.append("")
            sections.append("- **🟢 Fresh:** No action needed")
            sections.append("- **🟡 Recent:** Monitor for changes")
            sections.append("- **🟠 Aging:** Review and update if necessary")
            sections.append("- **🔴 Stale:** Verify accuracy and update")
            sections.append("- **⚫ Old:** Consider archiving or major revision")
            sections.append("")
            
            # Footer
            sections.append("---")
            sections.append("")
            sections.append("*This report is generated automatically. For questions about specific files, ")
            sections.append("consult the migration log or contact the development team.*")
            
            # Write report
            report_content = "\n".join(sections)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create freshness report: {e}")
            return False
    
    def _calculate_freshness_statistics(self, freshness_indicators: Dict[str, str]) -> Dict[str, int]:
        """Calculate statistics about content freshness."""
        stats = {
            "🟢 Fresh": 0,
            "🟡 Recent": 0,
            "🟠 Aging": 0,
            "🔴 Stale": 0,
            "⚫ Old": 0,
            "⚠️ Unknown": 0
        }
        
        for indicator in freshness_indicators.values():
            if "🟢" in indicator:
                stats["🟢 Fresh"] += 1
            elif "🟡" in indicator:
                stats["🟡 Recent"] += 1
            elif "🟠" in indicator:
                stats["🟠 Aging"] += 1
            elif "🔴" in indicator:
                stats["🔴 Stale"] += 1
            elif "⚫" in indicator:
                stats["⚫ Old"] += 1
            else:
                stats["⚠️ Unknown"] += 1
        
        return stats
    
    def _get_freshness_priority(self, indicator: str) -> int:
        """Get priority score for freshness indicator (lower = more urgent)."""
        if "⚫" in indicator:
            return 1  # Most urgent
        elif "🔴" in indicator:
            return 2
        elif "🟠" in indicator:
            return 3
        elif "🟡" in indicator:
            return 4
        elif "🟢" in indicator:
            return 5  # Least urgent
        else:
            return 6  # Unknown
    
    def _get_freshness_recommendation(self, indicator: str) -> str:
        """Get recommendation based on freshness indicator."""
        if "⚫" in indicator:
            return "Archive or major revision"
        elif "🔴" in indicator:
            return "Verify accuracy and update"
        elif "🟠" in indicator:
            return "Review and update if needed"
        elif "🟡" in indicator:
            return "Monitor for changes"
        elif "🟢" in indicator:
            return "No action needed"
        else:
            return "Review content age"
    
    def _should_add_freshness_indicator(self, indicator: str) -> bool:
        """Determine if freshness indicator should be added to file."""
        # Add indicators to files that are aging, stale, or old
        return any(status in indicator for status in ["🟠", "🔴", "⚫"])
    
    def _add_freshness_indicator_to_file(self, filepath: Path, indicator: str) -> bool:
        """
        Add freshness indicator to a file.
        
        Args:
            filepath: Path to the file
            indicator: Freshness indicator string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read current content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(filepath, 'r', encoding='cp1252') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding='latin1') as f:
                    content = f.read()
            
            # Check if freshness indicator already exists
            if "**Content Freshness:**" in content:
                # Update existing indicator
                import re
                pattern = r'\*\*Content Freshness:\*\* [^\n]+'
                replacement = f"**Content Freshness:** {indicator}"
                content = re.sub(pattern, replacement, content)
            else:
                # Add new freshness indicator at the top
                freshness_header = f"\n> **Content Freshness:** {indicator}\n\n"
                
                # Insert after any existing front matter or at the beginning
                if content.startswith('---'):
                    # Has front matter, insert after it
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        content = f"---{parts[1]}---{freshness_header}{parts[2]}"
                    else:
                        content = freshness_header + content
                else:
                    # No front matter, insert at beginning
                    content = freshness_header + content
            
            # Write updated content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add freshness indicator to {filepath}: {e}")
            return False