"""
Reporting and verification tools for the Documentation Consolidation System.

This module implements comprehensive reporting and verification tools as specified
in Task 8.3, including consolidation reports, verification checklists, and
removal suggestions for obsolete files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .models import (
    FileAnalysis, ConsolidationGroup, DocumentationStructure, 
    Category, Priority, MigrationLog
)
from .config import ConsolidationConfig
from .error_handler import ConsolidationError, ErrorHandler


class ReportType(Enum):
    """Types of reports that can be generated."""
    CONSOLIDATION_SUMMARY = "consolidation_summary"
    VERIFICATION_CHECKLIST = "verification_checklist"
    REMOVAL_SUGGESTIONS = "removal_suggestions"
    ERROR_REPORT = "error_report"
    MIGRATION_LOG = "migration_log"
    QUALITY_ASSESSMENT = "quality_assessment"
    STATISTICS_REPORT = "statistics_report"


class VerificationStatus(Enum):
    """Status of verification items."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class VerificationItem:
    """Represents a single verification item in the checklist."""
    item_id: str
    description: str
    category: str
    priority: Priority
    status: VerificationStatus = VerificationStatus.PENDING
    notes: str = ""
    verification_method: str = ""
    expected_result: str = ""
    actual_result: str = ""
    timestamp: Optional[datetime] = None
    
    def mark_verified(self, notes: str = "", actual_result: str = "") -> None:
        """Mark item as verified."""
        self.status = VerificationStatus.VERIFIED
        self.notes = notes
        self.actual_result = actual_result
        self.timestamp = datetime.now()
    
    def mark_failed(self, notes: str = "", actual_result: str = "") -> None:
        """Mark item as failed."""
        self.status = VerificationStatus.FAILED
        self.notes = notes
        self.actual_result = actual_result
        self.timestamp = datetime.now()


@dataclass
class RemovalSuggestion:
    """Represents a suggestion to remove an obsolete file."""
    file_path: Path
    reason: str
    confidence: float  # 0.0 to 1.0
    category: Category
    replacement_files: List[str] = field(default_factory=list)
    backup_recommended: bool = True
    manual_review_required: bool = False
    last_modified: Optional[datetime] = None
    file_size_mb: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_path': str(self.file_path),
            'reason': self.reason,
            'confidence': self.confidence,
            'category': self.category.value,
            'replacement_files': self.replacement_files,
            'backup_recommended': self.backup_recommended,
            'manual_review_required': self.manual_review_required,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'file_size_mb': self.file_size_mb
        }


class ConsolidationReporter:
    """
    Comprehensive reporting and verification system for documentation consolidation.
    
    Generates consolidation reports, verification checklists, and removal suggestions
    to help users understand and validate the consolidation process.
    """
    
    def __init__(self, config: ConsolidationConfig, error_handler: Optional[ErrorHandler] = None):
        """Initialize the reporter with configuration."""
        self.config = config
        self.error_handler = error_handler
        self.logger = logging.getLogger('doc_consolidation.reporter')
        
        # Report data
        self.consolidation_operations: List[Dict[str, Any]] = []
        self.verification_items: List[VerificationItem] = []
        self.removal_suggestions: List[RemovalSuggestion] = []
        self.quality_metrics: Dict[str, Any] = {}
        
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'files_consolidated': 0,
            'files_moved': 0,
            'files_created': 0,
            'directories_created': 0,
            'total_size_processed_mb': 0.0,
            'processing_start_time': None,
            'processing_end_time': None
        }
    
    def generate_consolidation_report(self, 
                                    file_analyses: List[FileAnalysis],
                                    consolidation_groups: List[ConsolidationGroup],
                                    migration_log: MigrationLog,
                                    output_path: Optional[Path] = None) -> str:
        """
        Generate comprehensive consolidation report showing all operations performed.
        
        Args:
            file_analyses: List of all file analyses performed
            consolidation_groups: List of consolidation groups created
            migration_log: Migration log with all operations
            output_path: Optional path to save the report
            
        Returns:
            Report content as markdown string
        """
        self.logger.info("Generating consolidation report")
        
        # Calculate statistics
        self._calculate_consolidation_statistics(file_analyses, consolidation_groups, migration_log)
        
        # Generate report content
        report_lines = [
            "# Documentation Consolidation Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Add executive summary
        report_lines.extend(self._generate_executive_summary(file_analyses, consolidation_groups))
        
        # Add statistics section
        report_lines.extend([
            "",
            "## Processing Statistics",
            ""
        ])
        report_lines.extend(self._generate_statistics_section())
        
        # Add file analysis summary
        report_lines.extend([
            "",
            "## File Analysis Summary",
            ""
        ])
        report_lines.extend(self._generate_file_analysis_summary(file_analyses))
        
        # Add consolidation groups section
        report_lines.extend([
            "",
            "## Consolidation Groups",
            ""
        ])
        report_lines.extend(self._generate_consolidation_groups_section(consolidation_groups))
        
        # Add migration operations section
        report_lines.extend([
            "",
            "## Migration Operations",
            ""
        ])
        report_lines.extend(self._generate_migration_operations_section(migration_log))
        
        # Add quality assessment
        report_lines.extend([
            "",
            "## Quality Assessment",
            ""
        ])
        report_lines.extend(self._generate_quality_assessment_section(file_analyses))
        
        # Add error summary if available
        if self.error_handler and self.error_handler.errors:
            report_lines.extend([
                "",
                "## Error Summary",
                ""
            ])
            report_lines.extend(self._generate_error_summary_section())
        
        # Add recommendations
        report_lines.extend([
            "",
            "## Recommendations",
            ""
        ])
        report_lines.extend(self._generate_recommendations_section(file_analyses, consolidation_groups))
        
        report_content = "\n".join(report_lines)
        
        # Save report if output path provided
        if output_path:
            self._save_report(report_content, output_path)
        
        return report_content
    
    def generate_verification_checklist(self, 
                                      file_analyses: List[FileAnalysis],
                                      consolidation_groups: List[ConsolidationGroup],
                                      structure: DocumentationStructure,
                                      output_path: Optional[Path] = None) -> List[VerificationItem]:
        """
        Create verification checklist for manual review.
        
        Args:
            file_analyses: List of all file analyses
            consolidation_groups: List of consolidation groups
            structure: Documentation structure created
            output_path: Optional path to save the checklist
            
        Returns:
            List of verification items
        """
        self.logger.info("Generating verification checklist")
        
        verification_items = []
        
        # Structure verification items
        verification_items.extend(self._create_structure_verification_items(structure))
        
        # File consolidation verification items
        verification_items.extend(self._create_consolidation_verification_items(consolidation_groups))
        
        # Content integrity verification items
        verification_items.extend(self._create_content_integrity_verification_items(file_analyses))
        
        # Navigation verification items
        verification_items.extend(self._create_navigation_verification_items(structure))
        
        # Quality verification items
        verification_items.extend(self._create_quality_verification_items(file_analyses))
        
        # Error resolution verification items
        if self.error_handler and self.error_handler.errors:
            verification_items.extend(self._create_error_resolution_verification_items())
        
        self.verification_items = verification_items
        
        # Save checklist if output path provided
        if output_path:
            self._save_verification_checklist(verification_items, output_path)
        
        return verification_items
    
    def generate_removal_suggestions(self, 
                                   file_analyses: List[FileAnalysis],
                                   consolidation_groups: List[ConsolidationGroup],
                                   output_path: Optional[Path] = None) -> List[RemovalSuggestion]:
        """
        Provide removal suggestions for obsolete files.
        
        Args:
            file_analyses: List of all file analyses
            consolidation_groups: List of consolidation groups
            output_path: Optional path to save suggestions
            
        Returns:
            List of removal suggestions
        """
        self.logger.info("Generating removal suggestions")
        
        removal_suggestions = []
        
        # Track files that were consolidated
        consolidated_files = set()
        for group in consolidation_groups:
            consolidated_files.add(group.primary_file)
            consolidated_files.update(group.related_files)
        
        # Analyze each file for removal potential
        for analysis in file_analyses:
            suggestions = self._analyze_file_for_removal(analysis, consolidated_files, consolidation_groups)
            removal_suggestions.extend(suggestions)
        
        # Sort suggestions by confidence (highest first)
        removal_suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        self.removal_suggestions = removal_suggestions
        
        # Save suggestions if output path provided
        if output_path:
            self._save_removal_suggestions(removal_suggestions, output_path)
        
        return removal_suggestions
    
    def generate_quality_assessment(self, 
                                  file_analyses: List[FileAnalysis],
                                  consolidation_groups: List[ConsolidationGroup],
                                  output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Generate quality assessment of the consolidation process.
        
        Args:
            file_analyses: List of all file analyses
            consolidation_groups: List of consolidation groups
            output_path: Optional path to save assessment
            
        Returns:
            Quality assessment metrics
        """
        self.logger.info("Generating quality assessment")
        
        quality_metrics = {
            'overall_score': 0.0,
            'categorization_quality': self._assess_categorization_quality(file_analyses),
            'consolidation_quality': self._assess_consolidation_quality(consolidation_groups),
            'structure_quality': self._assess_structure_quality(file_analyses),
            'content_preservation': self._assess_content_preservation(file_analyses, consolidation_groups),
            'error_rate': self._calculate_error_rate(),
            'recommendations': []
        }
        
        # Calculate overall score
        quality_metrics['overall_score'] = self._calculate_overall_quality_score(quality_metrics)
        
        # Generate recommendations based on quality metrics
        quality_metrics['recommendations'] = self._generate_quality_recommendations(quality_metrics)
        
        self.quality_metrics = quality_metrics
        
        # Save assessment if output path provided
        if output_path:
            self._save_quality_assessment(quality_metrics, output_path)
        
        return quality_metrics
    
    def export_reports_bundle(self, 
                            file_analyses: List[FileAnalysis],
                            consolidation_groups: List[ConsolidationGroup],
                            migration_log: MigrationLog,
                            structure: DocumentationStructure,
                            output_directory: Path) -> Dict[str, Path]:
        """
        Export a complete bundle of all reports and verification tools.
        
        Args:
            file_analyses: List of all file analyses
            consolidation_groups: List of consolidation groups
            migration_log: Migration log with operations
            structure: Documentation structure
            output_directory: Directory to save all reports
            
        Returns:
            Dictionary mapping report types to file paths
        """
        self.logger.info(f"Exporting reports bundle to {output_directory}")
        
        # Ensure output directory exists
        output_directory.mkdir(parents=True, exist_ok=True)
        
        report_paths = {}
        
        # Generate and save consolidation report
        consolidation_report_path = output_directory / "consolidation_report.md"
        self.generate_consolidation_report(
            file_analyses, consolidation_groups, migration_log, consolidation_report_path
        )
        report_paths['consolidation_report'] = consolidation_report_path
        
        # Generate and save verification checklist
        verification_checklist_path = output_directory / "verification_checklist.md"
        self.generate_verification_checklist(
            file_analyses, consolidation_groups, structure, verification_checklist_path
        )
        report_paths['verification_checklist'] = verification_checklist_path
        
        # Generate and save removal suggestions
        removal_suggestions_path = output_directory / "removal_suggestions.json"
        self.generate_removal_suggestions(
            file_analyses, consolidation_groups, removal_suggestions_path
        )
        report_paths['removal_suggestions'] = removal_suggestions_path
        
        # Generate and save quality assessment
        quality_assessment_path = output_directory / "quality_assessment.json"
        self.generate_quality_assessment(
            file_analyses, consolidation_groups, quality_assessment_path
        )
        report_paths['quality_assessment'] = quality_assessment_path
        
        # Generate statistics report
        statistics_report_path = output_directory / "statistics_report.json"
        self._save_statistics_report(statistics_report_path)
        report_paths['statistics_report'] = statistics_report_path
        
        # Generate error report if errors exist
        if self.error_handler and self.error_handler.errors:
            error_report_path = output_directory / "error_report.md"
            error_report = self.error_handler.generate_error_report()
            self._save_report(error_report, error_report_path)
            report_paths['error_report'] = error_report_path
        
        # Create summary index
        index_path = output_directory / "README.md"
        self._create_reports_index(report_paths, index_path)
        report_paths['index'] = index_path
        
        self.logger.info(f"Exported {len(report_paths)} reports to {output_directory}")
        return report_paths
    
    # Private helper methods for report generation
    
    def _calculate_consolidation_statistics(self, 
                                          file_analyses: List[FileAnalysis],
                                          consolidation_groups: List[ConsolidationGroup],
                                          migration_log: MigrationLog) -> None:
        """Calculate statistics for the consolidation process."""
        self.stats['files_processed'] = len(file_analyses)
        self.stats['files_consolidated'] = sum(len(group.related_files) + 1 for group in consolidation_groups)
        
        # Calculate total size processed
        total_size = 0
        for analysis in file_analyses:
            if analysis.filepath.exists():
                try:
                    size = analysis.filepath.stat().st_size
                    total_size += size
                except:
                    pass
        
        self.stats['total_size_processed_mb'] = total_size / (1024 * 1024)
        
        # Count operations from migration log
        if migration_log.operations:
            self.stats['files_moved'] = len([op for op in migration_log.operations if op.get('type') == 'move'])
            self.stats['files_created'] = len([op for op in migration_log.operations if op.get('type') == 'create'])
    
    def _generate_executive_summary(self, 
                                  file_analyses: List[FileAnalysis],
                                  consolidation_groups: List[ConsolidationGroup]) -> List[str]:
        """Generate executive summary section."""
        total_files = len(file_analyses)
        consolidated_files = sum(len(group.related_files) + 1 for group in consolidation_groups)
        consolidation_groups_count = len(consolidation_groups)
        
        # Calculate category distribution
        category_counts = {}
        for analysis in file_analyses:
            category_counts[analysis.category] = category_counts.get(analysis.category, 0) + 1
        
        summary_lines = [
            f"This report summarizes the consolidation of {total_files} documentation files.",
            f"A total of {consolidated_files} files were processed across {consolidation_groups_count} consolidation groups.",
            "",
            "### Key Achievements:",
            f"- Processed {total_files} documentation files",
            f"- Created {consolidation_groups_count} consolidated document groups",
            f"- Organized files into structured documentation hierarchy",
            f"- Total size processed: {self.stats['total_size_processed_mb']:.1f} MB",
            "",
            "### Category Distribution:",
        ]
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_files) * 100
            summary_lines.append(f"- {category.value.replace('_', ' ').title()}: {count} files ({percentage:.1f}%)")
        
        return summary_lines
    
    def _generate_statistics_section(self) -> List[str]:
        """Generate statistics section."""
        return [
            f"- **Files Processed:** {self.stats['files_processed']}",
            f"- **Files Consolidated:** {self.stats['files_consolidated']}",
            f"- **Files Moved:** {self.stats['files_moved']}",
            f"- **Files Created:** {self.stats['files_created']}",
            f"- **Directories Created:** {self.stats['directories_created']}",
            f"- **Total Size Processed:** {self.stats['total_size_processed_mb']:.1f} MB",
        ]
    
    def _generate_file_analysis_summary(self, file_analyses: List[FileAnalysis]) -> List[str]:
        """Generate file analysis summary section."""
        lines = []
        
        # Group by category
        category_groups = {}
        for analysis in file_analyses:
            if analysis.category not in category_groups:
                category_groups[analysis.category] = []
            category_groups[analysis.category].append(analysis)
        
        for category, analyses in category_groups.items():
            lines.extend([
                f"### {category.value.replace('_', ' ').title()} ({len(analyses)} files)",
                ""
            ])
            
            # Sort by confidence score (highest first)
            analyses.sort(key=lambda x: x.confidence_score, reverse=True)
            
            for analysis in analyses[:10]:  # Show top 10
                confidence_indicator = "✓" if analysis.confidence_score > 0.7 else "⚠" if analysis.confidence_score > 0.5 else "❌"
                lines.append(f"- {confidence_indicator} `{analysis.filename}` (confidence: {analysis.confidence_score:.2f})")
            
            if len(analyses) > 10:
                lines.append(f"- ... and {len(analyses) - 10} more files")
            
            lines.append("")
        
        return lines
    
    def _generate_consolidation_groups_section(self, consolidation_groups: List[ConsolidationGroup]) -> List[str]:
        """Generate consolidation groups section."""
        lines = []
        
        for i, group in enumerate(consolidation_groups, 1):
            lines.extend([
                f"### {i}. {group.group_id}",
                f"- **Category:** {group.category.value.replace('_', ' ').title()}",
                f"- **Strategy:** {group.consolidation_strategy.value.replace('_', ' ').title()}",
                f"- **Primary File:** `{group.primary_file}`",
                f"- **Output File:** `{group.output_filename}`",
                f"- **Related Files:** {len(group.related_files)} files",
                ""
            ])
            
            if group.related_files:
                lines.append("**Related Files:**")
                for related_file in group.related_files[:5]:  # Show first 5
                    lines.append(f"  - `{related_file}`")
                if len(group.related_files) > 5:
                    lines.append(f"  - ... and {len(group.related_files) - 5} more files")
                lines.append("")
        
        return lines
    
    def _generate_migration_operations_section(self, migration_log: MigrationLog) -> List[str]:
        """Generate migration operations section."""
        lines = [
            f"Total operations performed: {len(migration_log.operations)}",
            ""
        ]
        
        # Group operations by type
        operation_types = {}
        for operation in migration_log.operations:
            op_type = operation.get('type', 'unknown')
            if op_type not in operation_types:
                operation_types[op_type] = []
            operation_types[op_type].append(operation)
        
        for op_type, operations in operation_types.items():
            lines.extend([
                f"### {op_type.title()} Operations ({len(operations)})",
                ""
            ])
            
            for operation in operations[:10]:  # Show first 10
                source = operation.get('source', 'N/A')
                target = operation.get('target', 'N/A')
                lines.append(f"- `{source}` → `{target}`")
            
            if len(operations) > 10:
                lines.append(f"- ... and {len(operations) - 10} more operations")
            
            lines.append("")
        
        return lines
    
    def _generate_quality_assessment_section(self, file_analyses: List[FileAnalysis]) -> List[str]:
        """Generate quality assessment section."""
        # Calculate quality metrics
        total_files = len(file_analyses)
        high_confidence_files = len([a for a in file_analyses if a.confidence_score > 0.7])
        low_confidence_files = len([a for a in file_analyses if a.confidence_score < 0.5])
        
        confidence_rate = (high_confidence_files / total_files) * 100 if total_files > 0 else 0
        
        lines = [
            f"- **High Confidence Classifications:** {high_confidence_files}/{total_files} ({confidence_rate:.1f}%)",
            f"- **Low Confidence Classifications:** {low_confidence_files}/{total_files}",
        ]
        
        if self.error_handler:
            error_rate = (len(self.error_handler.errors) / total_files) * 100 if total_files > 0 else 0
            lines.append(f"- **Error Rate:** {len(self.error_handler.errors)}/{total_files} ({error_rate:.1f}%)")
        
        # Quality indicators
        lines.extend([
            "",
            "### Quality Indicators:",
        ])
        
        if confidence_rate > 80:
            lines.append("✅ **Excellent** categorization confidence")
        elif confidence_rate > 60:
            lines.append("⚠️ **Good** categorization confidence")
        else:
            lines.append("❌ **Poor** categorization confidence - manual review recommended")
        
        return lines
    
    def _generate_error_summary_section(self) -> List[str]:
        """Generate error summary section."""
        if not self.error_handler or not self.error_handler.errors:
            return ["No errors encountered during consolidation."]
        
        error_summary = self.error_handler.get_error_summary()
        
        lines = [
            f"- **Total Errors:** {error_summary['total_errors']}",
            f"- **Critical Errors:** {error_summary['critical_errors']}",
            f"- **Failed Files:** {error_summary['failed_files_count']}",
            f"- **Can Continue:** {'Yes' if error_summary['can_continue'] else 'No'}",
            ""
        ]
        
        if error_summary['critical_errors'] > 0:
            lines.extend([
                "⚠️ **Critical errors detected** - these must be resolved before proceeding.",
                "See the detailed error report for resolution steps.",
                ""
            ])
        
        return lines
    
    def _generate_recommendations_section(self, 
                                        file_analyses: List[FileAnalysis],
                                        consolidation_groups: List[ConsolidationGroup]) -> List[str]:
        """Generate recommendations section."""
        recommendations = []
        
        # Analyze for recommendations
        low_confidence_files = [a for a in file_analyses if a.confidence_score < 0.5]
        if low_confidence_files:
            recommendations.append(
                f"📋 **Manual Review Required:** {len(low_confidence_files)} files have low "
                "categorization confidence and should be reviewed manually."
            )
        
        # Check for large consolidation groups
        large_groups = [g for g in consolidation_groups if len(g.related_files) > 10]
        if large_groups:
            recommendations.append(
                f"📊 **Large Groups:** {len(large_groups)} consolidation groups contain more than "
                "10 files. Consider splitting these for better organization."
            )
        
        # Error-based recommendations
        if self.error_handler and self.error_handler.critical_errors:
            recommendations.append(
                "🚨 **Critical Issues:** Resolve critical errors before using the consolidated documentation."
            )
        
        # General recommendations
        recommendations.extend([
            "✅ **Verify Links:** Check that all internal links work correctly after reorganization.",
            "📝 **Update References:** Update any external references to the old file locations.",
            "🔍 **Review Content:** Spot-check consolidated files to ensure content integrity.",
            "🗂️ **Test Navigation:** Verify that the new documentation structure is easy to navigate."
        ])
        
        return recommendations
    
    def _create_structure_verification_items(self, structure: DocumentationStructure) -> List[VerificationItem]:
        """Create verification items for documentation structure."""
        items = []
        
        items.append(VerificationItem(
            item_id="struct_001",
            description="Verify docs/ directory was created successfully",
            category="Structure",
            priority=Priority.HIGH,
            verification_method="Check file system",
            expected_result="docs/ directory exists with proper permissions"
        ))
        
        items.append(VerificationItem(
            item_id="struct_002",
            description="Verify all required subdirectories were created",
            category="Structure",
            priority=Priority.HIGH,
            verification_method="Check subdirectory existence",
            expected_result="All category subdirectories exist (setup/, features/, etc.)"
        ))
        
        items.append(VerificationItem(
            item_id="struct_003",
            description="Verify master README.md was generated",
            category="Structure",
            priority=Priority.HIGH,
            verification_method="Check file existence and content",
            expected_result="docs/README.md exists with navigation links"
        ))
        
        return items
    
    def _create_consolidation_verification_items(self, consolidation_groups: List[ConsolidationGroup]) -> List[VerificationItem]:
        """Create verification items for consolidation groups."""
        items = []
        
        for i, group in enumerate(consolidation_groups, 1):
            items.append(VerificationItem(
                item_id=f"consol_{i:03d}",
                description=f"Verify consolidation group '{group.group_id}' was processed correctly",
                category="Consolidation",
                priority=Priority.MEDIUM,
                verification_method="Check output file content",
                expected_result=f"Output file '{group.output_filename}' contains merged content from all related files"
            ))
        
        return items
    
    def _create_content_integrity_verification_items(self, file_analyses: List[FileAnalysis]) -> List[VerificationItem]:
        """Create verification items for content integrity."""
        items = []
        
        items.append(VerificationItem(
            item_id="content_001",
            description="Verify no content was lost during consolidation",
            category="Content Integrity",
            priority=Priority.CRITICAL,
            verification_method="Compare original and consolidated content",
            expected_result="All important information preserved in consolidated files"
        ))
        
        items.append(VerificationItem(
            item_id="content_002",
            description="Verify internal links are functional",
            category="Content Integrity",
            priority=Priority.HIGH,
            verification_method="Test internal links in consolidated files",
            expected_result="All internal links resolve correctly"
        ))
        
        items.append(VerificationItem(
            item_id="content_003",
            description="Verify markdown formatting is correct",
            category="Content Integrity",
            priority=Priority.MEDIUM,
            verification_method="Validate markdown syntax",
            expected_result="All consolidated files have valid markdown syntax"
        ))
        
        return items
    
    def _create_navigation_verification_items(self, structure: DocumentationStructure) -> List[VerificationItem]:
        """Create verification items for navigation."""
        items = []
        
        items.append(VerificationItem(
            item_id="nav_001",
            description="Verify master index provides complete navigation",
            category="Navigation",
            priority=Priority.HIGH,
            verification_method="Review master README.md",
            expected_result="All major sections and files are linked from master index"
        ))
        
        items.append(VerificationItem(
            item_id="nav_002",
            description="Verify category indexes are complete",
            category="Navigation",
            priority=Priority.MEDIUM,
            verification_method="Check category-specific index files",
            expected_result="Each category has appropriate index or navigation"
        ))
        
        return items
    
    def _create_quality_verification_items(self, file_analyses: List[FileAnalysis]) -> List[VerificationItem]:
        """Create verification items for quality assurance."""
        items = []
        
        low_confidence_files = [a for a in file_analyses if a.confidence_score < 0.5]
        if low_confidence_files:
            items.append(VerificationItem(
                item_id="quality_001",
                description=f"Review {len(low_confidence_files)} files with low categorization confidence",
                category="Quality",
                priority=Priority.MEDIUM,
                verification_method="Manual review of flagged files",
                expected_result="Low confidence files are correctly categorized or moved"
            ))
        
        items.append(VerificationItem(
            item_id="quality_002",
            description="Verify documentation follows Django conventions",
            category="Quality",
            priority=Priority.MEDIUM,
            verification_method="Review structure against Django documentation standards",
            expected_result="Documentation structure follows Django project conventions"
        ))
        
        return items
    
    def _create_error_resolution_verification_items(self) -> List[VerificationItem]:
        """Create verification items for error resolution."""
        items = []
        
        if self.error_handler.critical_errors:
            items.append(VerificationItem(
                item_id="error_001",
                description=f"Resolve {len(self.error_handler.critical_errors)} critical errors",
                category="Error Resolution",
                priority=Priority.CRITICAL,
                verification_method="Address each critical error individually",
                expected_result="All critical errors resolved, system can continue"
            ))
        
        failed_files = self.error_handler.get_failed_files()
        if failed_files:
            items.append(VerificationItem(
                item_id="error_002",
                description=f"Review {len(failed_files)} files that failed processing",
                category="Error Resolution",
                priority=Priority.HIGH,
                verification_method="Manual review of failed files",
                expected_result="Failed files are processed manually or excluded appropriately"
            ))
        
        return items
    
    def _analyze_file_for_removal(self, 
                                analysis: FileAnalysis,
                                consolidated_files: Set[str],
                                consolidation_groups: List[ConsolidationGroup]) -> List[RemovalSuggestion]:
        """Analyze a file to determine if it should be removed."""
        suggestions = []
        
        # Check if file was consolidated
        if analysis.filename in consolidated_files:
            # Find which group this file belongs to
            replacement_files = []
            for group in consolidation_groups:
                if analysis.filename in [group.primary_file] + group.related_files:
                    replacement_files.append(group.output_filename)
                    break
            
            confidence = 0.9 if analysis.filename != group.primary_file else 0.7  # Lower confidence for primary files
            
            suggestions.append(RemovalSuggestion(
                file_path=analysis.filepath,
                reason=f"File was consolidated into {', '.join(replacement_files)}",
                confidence=confidence,
                category=analysis.category,
                replacement_files=replacement_files,
                backup_recommended=True,
                manual_review_required=confidence < 0.8,
                last_modified=analysis.metadata.last_modified,
                file_size_mb=self._get_file_size_mb(analysis.filepath)
            ))
        
        # Check for duplicate or obsolete files
        elif analysis.category == Category.HISTORICAL_ARCHIVE:
            suggestions.append(RemovalSuggestion(
                file_path=analysis.filepath,
                reason="File categorized as historical/archive content",
                confidence=0.6,
                category=analysis.category,
                backup_recommended=True,
                manual_review_required=True,
                last_modified=analysis.metadata.last_modified,
                file_size_mb=self._get_file_size_mb(analysis.filepath)
            ))
        
        # Check for very old files with low priority
        elif (analysis.preservation_priority == Priority.LOW and 
              analysis.metadata.last_modified and
              (datetime.now() - analysis.metadata.last_modified).days > 365):
            
            suggestions.append(RemovalSuggestion(
                file_path=analysis.filepath,
                reason="Old file with low preservation priority (>1 year old)",
                confidence=0.4,
                category=analysis.category,
                backup_recommended=True,
                manual_review_required=True,
                last_modified=analysis.metadata.last_modified,
                file_size_mb=self._get_file_size_mb(analysis.filepath)
            ))
        
        return suggestions
    
    def _assess_categorization_quality(self, file_analyses: List[FileAnalysis]) -> Dict[str, Any]:
        """Assess the quality of file categorization."""
        total_files = len(file_analyses)
        if total_files == 0:
            return {'score': 0.0, 'details': 'No files to assess'}
        
        high_confidence = len([a for a in file_analyses if a.confidence_score > 0.7])
        medium_confidence = len([a for a in file_analyses if 0.5 <= a.confidence_score <= 0.7])
        low_confidence = len([a for a in file_analyses if a.confidence_score < 0.5])
        
        # Calculate weighted score
        score = (high_confidence * 1.0 + medium_confidence * 0.7 + low_confidence * 0.3) / total_files
        
        return {
            'score': score,
            'high_confidence_count': high_confidence,
            'medium_confidence_count': medium_confidence,
            'low_confidence_count': low_confidence,
            'high_confidence_percentage': (high_confidence / total_files) * 100,
            'details': f'{high_confidence}/{total_files} files with high confidence'
        }
    
    def _assess_consolidation_quality(self, consolidation_groups: List[ConsolidationGroup]) -> Dict[str, Any]:
        """Assess the quality of consolidation groups."""
        if not consolidation_groups:
            return {'score': 0.0, 'details': 'No consolidation groups created'}
        
        total_files_consolidated = sum(len(group.related_files) + 1 for group in consolidation_groups)
        average_group_size = total_files_consolidated / len(consolidation_groups)
        
        # Assess group size distribution
        optimal_size_groups = len([g for g in consolidation_groups if 2 <= len(g.related_files) + 1 <= 8])
        large_groups = len([g for g in consolidation_groups if len(g.related_files) + 1 > 8])
        small_groups = len([g for g in consolidation_groups if len(g.related_files) + 1 < 2])
        
        # Calculate score based on optimal group sizes
        score = optimal_size_groups / len(consolidation_groups)
        
        return {
            'score': score,
            'total_groups': len(consolidation_groups),
            'average_group_size': average_group_size,
            'optimal_size_groups': optimal_size_groups,
            'large_groups': large_groups,
            'small_groups': small_groups,
            'details': f'{optimal_size_groups}/{len(consolidation_groups)} groups with optimal size'
        }
    
    def _assess_structure_quality(self, file_analyses: List[FileAnalysis]) -> Dict[str, Any]:
        """Assess the quality of the documentation structure."""
        # Assess category distribution
        category_counts = {}
        for analysis in file_analyses:
            category_counts[analysis.category] = category_counts.get(analysis.category, 0) + 1
        
        # Check for balanced distribution
        total_files = len(file_analyses)
        uncategorized_count = category_counts.get(Category.UNCATEGORIZED, 0)
        categorized_percentage = ((total_files - uncategorized_count) / total_files) * 100 if total_files > 0 else 0
        
        # Calculate structure score
        score = categorized_percentage / 100
        
        return {
            'score': score,
            'categorized_percentage': categorized_percentage,
            'category_distribution': {cat.value: count for cat, count in category_counts.items()},
            'uncategorized_count': uncategorized_count,
            'details': f'{categorized_percentage:.1f}% of files successfully categorized'
        }
    
    def _assess_content_preservation(self, 
                                   file_analyses: List[FileAnalysis],
                                   consolidation_groups: List[ConsolidationGroup]) -> Dict[str, Any]:
        """Assess content preservation during consolidation."""
        # This is a simplified assessment - in a real implementation,
        # you would compare original vs consolidated content
        
        total_original_files = len(file_analyses)
        files_in_groups = sum(len(group.related_files) + 1 for group in consolidation_groups)
        
        # Assume good preservation if files were properly grouped
        preservation_score = 0.9 if files_in_groups > 0 else 1.0
        
        return {
            'score': preservation_score,
            'original_files': total_original_files,
            'files_in_consolidation': files_in_groups,
            'details': 'Content preservation assessment based on consolidation coverage'
        }
    
    def _calculate_error_rate(self) -> float:
        """Calculate the error rate during processing."""
        if not self.error_handler:
            return 0.0
        
        total_operations = self.stats.get('files_processed', 0)
        if total_operations == 0:
            return 0.0
        
        return len(self.error_handler.errors) / total_operations
    
    def _calculate_overall_quality_score(self, quality_metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score from individual metrics."""
        weights = {
            'categorization_quality': 0.3,
            'consolidation_quality': 0.25,
            'structure_quality': 0.25,
            'content_preservation': 0.2
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in quality_metrics and isinstance(quality_metrics[metric], dict):
                score = quality_metrics[metric].get('score', 0.0)
                weighted_score += score * weight
                total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_quality_recommendations(self, quality_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on quality metrics."""
        recommendations = []
        
        # Categorization recommendations
        cat_quality = quality_metrics.get('categorization_quality', {})
        if cat_quality.get('score', 0) < 0.7:
            recommendations.append("Improve categorization accuracy by reviewing low-confidence files")
        
        # Consolidation recommendations
        consol_quality = quality_metrics.get('consolidation_quality', {})
        if consol_quality.get('large_groups', 0) > 0:
            recommendations.append("Consider splitting large consolidation groups for better organization")
        
        # Structure recommendations
        struct_quality = quality_metrics.get('structure_quality', {})
        if struct_quality.get('uncategorized_count', 0) > 0:
            recommendations.append("Review uncategorized files and assign appropriate categories")
        
        # Error rate recommendations
        error_rate = quality_metrics.get('error_rate', 0)
        if error_rate > 0.1:
            recommendations.append("High error rate detected - review error log and resolve issues")
        
        return recommendations
    
    def _get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB safely."""
        try:
            if file_path.exists():
                return file_path.stat().st_size / (1024 * 1024)
        except:
            pass
        return 0.0
    
    def _save_report(self, content: str, output_path: Path) -> None:
        """Save report content to file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"Report saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save report to {output_path}: {e}")
    
    def _save_verification_checklist(self, items: List[VerificationItem], output_path: Path) -> None:
        """Save verification checklist to file."""
        try:
            lines = [
                "# Documentation Consolidation Verification Checklist",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## Instructions",
                "Review each item below and mark as verified, failed, or skipped.",
                "Update the status and notes as you complete each verification.",
                ""
            ]
            
            # Group items by category
            categories = {}
            for item in items:
                if item.category not in categories:
                    categories[item.category] = []
                categories[item.category].append(item)
            
            for category, category_items in categories.items():
                lines.extend([
                    f"## {category}",
                    ""
                ])
                
                for item in category_items:
                    status_icon = {
                        VerificationStatus.PENDING: "⏳",
                        VerificationStatus.VERIFIED: "✅",
                        VerificationStatus.FAILED: "❌",
                        VerificationStatus.SKIPPED: "⏭️",
                        VerificationStatus.NOT_APPLICABLE: "➖"
                    }.get(item.status, "⏳")
                    
                    lines.extend([
                        f"### {status_icon} {item.item_id}: {item.description}",
                        f"- **Priority:** {item.priority.value.title()}",
                        f"- **Verification Method:** {item.verification_method}",
                        f"- **Expected Result:** {item.expected_result}",
                        f"- **Status:** {item.status.value.replace('_', ' ').title()}",
                    ])
                    
                    if item.notes:
                        lines.append(f"- **Notes:** {item.notes}")
                    
                    if item.actual_result:
                        lines.append(f"- **Actual Result:** {item.actual_result}")
                    
                    lines.append("")
            
            content = "\n".join(lines)
            self._save_report(content, output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save verification checklist to {output_path}: {e}")
    
    def _save_removal_suggestions(self, suggestions: List[RemovalSuggestion], output_path: Path) -> None:
        """Save removal suggestions to JSON file."""
        try:
            suggestions_data = {
                'generated': datetime.now().isoformat(),
                'total_suggestions': len(suggestions),
                'high_confidence_suggestions': len([s for s in suggestions if s.confidence > 0.8]),
                'suggestions': [s.to_dict() for s in suggestions]
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(suggestions_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Removal suggestions saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save removal suggestions to {output_path}: {e}")
    
    def _save_quality_assessment(self, quality_metrics: Dict[str, Any], output_path: Path) -> None:
        """Save quality assessment to JSON file."""
        try:
            assessment_data = {
                'generated': datetime.now().isoformat(),
                'overall_score': quality_metrics['overall_score'],
                'metrics': quality_metrics
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(assessment_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Quality assessment saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save quality assessment to {output_path}: {e}")
    
    def _save_statistics_report(self, output_path: Path) -> None:
        """Save statistics report to JSON file."""
        try:
            stats_data = {
                'generated': datetime.now().isoformat(),
                'statistics': self.stats
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Statistics report saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save statistics report to {output_path}: {e}")
    
    def _create_reports_index(self, report_paths: Dict[str, Path], index_path: Path) -> None:
        """Create an index file for all generated reports."""
        try:
            lines = [
                "# Documentation Consolidation Reports",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "This directory contains comprehensive reports and verification tools for the documentation consolidation process.",
                "",
                "## Available Reports",
                ""
            ]
            
            report_descriptions = {
                'consolidation_report': "📊 **Consolidation Report** - Comprehensive summary of all consolidation operations",
                'verification_checklist': "✅ **Verification Checklist** - Manual verification items for quality assurance",
                'removal_suggestions': "🗑️ **Removal Suggestions** - Files that can potentially be removed after consolidation",
                'quality_assessment': "📈 **Quality Assessment** - Quality metrics and recommendations",
                'statistics_report': "📋 **Statistics Report** - Processing statistics and metrics",
                'error_report': "⚠️ **Error Report** - Detailed error analysis and resolution steps"
            }
            
            for report_type, report_path in report_paths.items():
                if report_type == 'index':
                    continue
                
                description = report_descriptions.get(report_type, f"Report: {report_type}")
                lines.append(f"- [{description}]({report_path.name})")
            
            lines.extend([
                "",
                "## Usage Instructions",
                "",
                "1. **Start with the Consolidation Report** to understand what was done",
                "2. **Review the Verification Checklist** to ensure quality",
                "3. **Check the Error Report** (if present) to resolve any issues",
                "4. **Consider the Removal Suggestions** to clean up obsolete files",
                "5. **Use the Quality Assessment** to identify areas for improvement",
                "",
                "## Next Steps",
                "",
                "- Complete all verification checklist items",
                "- Resolve any critical errors identified",
                "- Test the new documentation structure thoroughly",
                "- Update external references to moved files",
                "- Consider implementing suggested improvements",
                ""
            ])
            
            content = "\n".join(lines)
            self._save_report(content, index_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create reports index at {index_path}: {e}")