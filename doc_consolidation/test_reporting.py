"""
Unit tests for the reporting and verification tools.

Tests comprehensive reporting functionality including consolidation reports,
verification checklists, and removal suggestions as specified in Task 8.3.
"""

import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
from unittest.mock import Mock, patch

from .reporting import (
    ConsolidationReporter, VerificationItem, RemovalSuggestion,
    ReportType, VerificationStatus
)
from .config import ConsolidationConfig
from .error_handler import ErrorHandler, ConsolidationError, ErrorType, ErrorSeverity
from .models import (
    FileAnalysis, ConsolidationGroup, DocumentationStructure, 
    Category, Priority, ContentMetadata, MigrationLog, ConsolidationStrategy, ContentType
)


class TestConsolidationReporter:
    """Test cases for the ConsolidationReporter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConsolidationConfig()
        self.error_handler = ErrorHandler(self.config)
        self.reporter = ConsolidationReporter(self.config, self.error_handler)
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_sample_file_analyses(self) -> List[FileAnalysis]:
        """Create sample file analyses for testing."""
        analyses = []
        
        # High confidence feature file
        analyses.append(FileAnalysis(
            filepath=Path("PAYMENT_SYSTEM_COMPLETE.md"),
            filename="PAYMENT_SYSTEM_COMPLETE.md",
            category=Category.FEATURE_DOCS,
            content_type=ContentType.FEATURE_GUIDE,
            metadata=ContentMetadata(
                word_count=500,
                last_modified=datetime.now() - timedelta(days=30),
                key_topics=["payment", "integration", "api"]
            ),
            preservation_priority=Priority.HIGH,
            confidence_score=0.9
        ))
        
        # Low confidence file
        analyses.append(FileAnalysis(
            filepath=Path("ambiguous_file.md"),
            filename="ambiguous_file.md",
            category=Category.UNCATEGORIZED,
            content_type=ContentType.GENERAL_DOC,
            metadata=ContentMetadata(
                word_count=100,
                last_modified=datetime.now() - timedelta(days=5),
                key_topics=["misc"]
            ),
            preservation_priority=Priority.MEDIUM,
            confidence_score=0.3
        ))
        
        # Setup file
        analyses.append(FileAnalysis(
            filepath=Path("INSTALLATION_SETUP.md"),
            filename="INSTALLATION_SETUP.md",
            category=Category.SETUP_CONFIG,
            content_type=ContentType.SETUP_PROCEDURE,
            metadata=ContentMetadata(
                word_count=800,
                last_modified=datetime.now() - timedelta(days=10),
                key_topics=["installation", "setup", "configuration"]
            ),
            preservation_priority=Priority.HIGH,
            confidence_score=0.85
        ))
        
        # Old archive file
        analyses.append(FileAnalysis(
            filepath=Path("old_deprecated_file.md"),
            filename="old_deprecated_file.md",
            category=Category.HISTORICAL_ARCHIVE,
            content_type=ContentType.HISTORICAL_DOC,
            metadata=ContentMetadata(
                word_count=200,
                last_modified=datetime.now() - timedelta(days=400),
                key_topics=["deprecated"]
            ),
            preservation_priority=Priority.LOW,
            confidence_score=0.7
        ))
        
        return analyses
    
    def create_sample_consolidation_groups(self) -> List[ConsolidationGroup]:
        """Create sample consolidation groups for testing."""
        groups = []
        
        groups.append(ConsolidationGroup(
            group_id="payment_consolidation",
            category=Category.FEATURE_DOCS,
            primary_file="PAYMENT_SYSTEM_COMPLETE.md",
            related_files=["PAYMENT_INTEGRATION.md", "PAYMENT_API.md"],
            consolidation_strategy=ConsolidationStrategy.MERGE_TOPICAL,
            output_filename="payment_comprehensive_guide.md"
        ))
        
        groups.append(ConsolidationGroup(
            group_id="setup_consolidation",
            category=Category.SETUP_CONFIG,
            primary_file="INSTALLATION_SETUP.md",
            related_files=["CONFIG_SETUP.md", "ENV_SETUP.md"],
            consolidation_strategy=ConsolidationStrategy.MERGE_SEQUENTIAL,
            output_filename="installation_guide.md"
        ))
        
        return groups
    
    def create_sample_migration_log(self) -> MigrationLog:
        """Create sample migration log for testing."""
        migration_log = MigrationLog()
        
        migration_log.operations = [
            {
                'type': 'move',
                'source': 'PAYMENT_SYSTEM_COMPLETE.md',
                'target': 'docs/features/payment_comprehensive_guide.md',
                'timestamp': datetime.now().isoformat()
            },
            {
                'type': 'create',
                'source': None,
                'target': 'docs/README.md',
                'timestamp': datetime.now().isoformat()
            },
            {
                'type': 'consolidate',
                'source': 'PAYMENT_INTEGRATION.md',
                'target': 'docs/features/payment_comprehensive_guide.md',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        return migration_log
    
    def create_sample_documentation_structure(self) -> DocumentationStructure:
        """Create sample documentation structure for testing."""
        return DocumentationStructure(
            root_path="docs/",
            categories={
                Category.FEATURE_DOCS: {"path": "features/", "index": "README.md"},
                Category.SETUP_CONFIG: {"path": "setup/", "index": "README.md"}
            }
        )
    
    def test_generate_consolidation_report(self):
        """Test consolidation report generation."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        migration_log = self.create_sample_migration_log()
        
        report = self.reporter.generate_consolidation_report(
            file_analyses, consolidation_groups, migration_log
        )
        
        assert "Documentation Consolidation Report" in report
        assert "Executive Summary" in report
        assert "Processing Statistics" in report
        assert "File Analysis Summary" in report
        assert "Consolidation Groups" in report
        assert "Migration Operations" in report
        assert "Quality Assessment" in report
        assert "Recommendations" in report
        
        # Check statistics
        assert f"Files Processed:** {len(file_analyses)}" in report
        assert f"payment_consolidation" in report
        assert f"setup_consolidation" in report
    
    def test_generate_consolidation_report_with_output_path(self):
        """Test consolidation report generation with file output."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        migration_log = self.create_sample_migration_log()
        
        output_path = self.temp_dir / "consolidation_report.md"
        
        report = self.reporter.generate_consolidation_report(
            file_analyses, consolidation_groups, migration_log, output_path
        )
        
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        
        assert saved_content == report
        assert "Documentation Consolidation Report" in saved_content
    
    def test_generate_verification_checklist(self):
        """Test verification checklist generation."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        structure = self.create_sample_documentation_structure()
        
        checklist = self.reporter.generate_verification_checklist(
            file_analyses, consolidation_groups, structure
        )
        
        assert len(checklist) > 0
        assert all(isinstance(item, VerificationItem) for item in checklist)
        
        # Check for different categories of verification items
        categories = {item.category for item in checklist}
        assert "Structure" in categories
        assert "Consolidation" in categories
        assert "Content Integrity" in categories
        assert "Navigation" in categories
        
        # Check for specific verification items
        item_ids = {item.item_id for item in checklist}
        assert "struct_001" in item_ids  # Directory creation
        assert "content_001" in item_ids  # Content integrity
    
    def test_generate_verification_checklist_with_errors(self):
        """Test verification checklist generation with errors present."""
        # Add some errors to the error handler
        self.error_handler.handle_file_system_error(
            PermissionError("Permission denied"), Path("test.md"), "read_file"
        )
        
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        structure = self.create_sample_documentation_structure()
        
        checklist = self.reporter.generate_verification_checklist(
            file_analyses, consolidation_groups, structure
        )
        
        # Should include error resolution items
        categories = {item.category for item in checklist}
        assert "Error Resolution" in categories
        
        error_items = [item for item in checklist if item.category == "Error Resolution"]
        assert len(error_items) > 0
    
    def test_generate_verification_checklist_with_output_path(self):
        """Test verification checklist generation with file output."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        structure = self.create_sample_documentation_structure()
        
        output_path = self.temp_dir / "verification_checklist.md"
        
        checklist = self.reporter.generate_verification_checklist(
            file_analyses, consolidation_groups, structure, output_path
        )
        
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Documentation Consolidation Verification Checklist" in content
        assert "Instructions" in content
        assert "struct_001" in content
    
    def test_generate_removal_suggestions(self):
        """Test removal suggestions generation."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        
        suggestions = self.reporter.generate_removal_suggestions(
            file_analyses, consolidation_groups
        )
        
        assert len(suggestions) > 0
        assert all(isinstance(s, RemovalSuggestion) for s in suggestions)
        
        # Check for consolidated file suggestions
        consolidated_suggestions = [
            s for s in suggestions 
            if "consolidated" in s.reason.lower()
        ]
        assert len(consolidated_suggestions) > 0
        
        # Check for archive file suggestions
        archive_suggestions = [
            s for s in suggestions 
            if s.category == Category.HISTORICAL_ARCHIVE
        ]
        assert len(archive_suggestions) > 0
        
        # Suggestions should be sorted by confidence (highest first)
        confidences = [s.confidence for s in suggestions]
        assert confidences == sorted(confidences, reverse=True)
    
    def test_generate_removal_suggestions_with_output_path(self):
        """Test removal suggestions generation with file output."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        
        output_path = self.temp_dir / "removal_suggestions.json"
        
        suggestions = self.reporter.generate_removal_suggestions(
            file_analyses, consolidation_groups, output_path
        )
        
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'generated' in data
        assert 'total_suggestions' in data
        assert 'suggestions' in data
        assert data['total_suggestions'] == len(suggestions)
        assert len(data['suggestions']) == len(suggestions)
    
    def test_generate_quality_assessment(self):
        """Test quality assessment generation."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        
        assessment = self.reporter.generate_quality_assessment(
            file_analyses, consolidation_groups
        )
        
        assert 'overall_score' in assessment
        assert 'categorization_quality' in assessment
        assert 'consolidation_quality' in assessment
        assert 'structure_quality' in assessment
        assert 'content_preservation' in assessment
        assert 'error_rate' in assessment
        assert 'recommendations' in assessment
        
        # Check score ranges
        assert 0.0 <= assessment['overall_score'] <= 1.0
        assert 0.0 <= assessment['categorization_quality']['score'] <= 1.0
        assert 0.0 <= assessment['consolidation_quality']['score'] <= 1.0
        
        # Check recommendations
        assert isinstance(assessment['recommendations'], list)
    
    def test_generate_quality_assessment_with_output_path(self):
        """Test quality assessment generation with file output."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        
        output_path = self.temp_dir / "quality_assessment.json"
        
        assessment = self.reporter.generate_quality_assessment(
            file_analyses, consolidation_groups, output_path
        )
        
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'generated' in data
        assert 'overall_score' in data
        assert 'metrics' in data
        assert data['overall_score'] == assessment['overall_score']
    
    def test_export_reports_bundle(self):
        """Test exporting complete reports bundle."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        migration_log = self.create_sample_migration_log()
        structure = self.create_sample_documentation_structure()
        
        output_dir = self.temp_dir / "reports"
        
        report_paths = self.reporter.export_reports_bundle(
            file_analyses, consolidation_groups, migration_log, structure, output_dir
        )
        
        # Check that all expected reports were created
        expected_reports = [
            'consolidation_report', 'verification_checklist', 'removal_suggestions',
            'quality_assessment', 'statistics_report', 'index'
        ]
        
        for report_type in expected_reports:
            assert report_type in report_paths
            assert report_paths[report_type].exists()
        
        # Check index file content
        index_path = report_paths['index']
        with open(index_path, 'r', encoding='utf-8') as f:
            index_content = f.read()
        
        assert "Documentation Consolidation Reports" in index_content
        assert "Available Reports" in index_content
        assert "Usage Instructions" in index_content
    
    def test_export_reports_bundle_with_errors(self):
        """Test exporting reports bundle when errors are present."""
        # Add errors to error handler
        self.error_handler.handle_file_system_error(
            PermissionError("Permission denied"), Path("test.md"), "read_file"
        )
        
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        migration_log = self.create_sample_migration_log()
        structure = self.create_sample_documentation_structure()
        
        output_dir = self.temp_dir / "reports_with_errors"
        
        report_paths = self.reporter.export_reports_bundle(
            file_analyses, consolidation_groups, migration_log, structure, output_dir
        )
        
        # Should include error report when errors are present
        assert 'error_report' in report_paths
        assert report_paths['error_report'].exists()
        
        # Check error report content
        with open(report_paths['error_report'], 'r', encoding='utf-8') as f:
            error_content = f.read()
        
        assert "Error Report" in error_content
        assert "Permission denied" in error_content
    
    def test_statistics_calculation(self):
        """Test statistics calculation."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        migration_log = self.create_sample_migration_log()
        
        # Generate report to trigger statistics calculation
        self.reporter.generate_consolidation_report(
            file_analyses, consolidation_groups, migration_log
        )
        
        stats = self.reporter.stats
        
        assert stats['files_processed'] == len(file_analyses)
        assert stats['files_consolidated'] > 0
        assert stats['total_size_processed_mb'] >= 0
    
    def test_quality_metrics_calculation(self):
        """Test quality metrics calculation."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        
        # Test categorization quality
        cat_quality = self.reporter._assess_categorization_quality(file_analyses)
        assert 'score' in cat_quality
        assert 'high_confidence_count' in cat_quality
        assert 'low_confidence_count' in cat_quality
        
        # Test consolidation quality
        consol_quality = self.reporter._assess_consolidation_quality(consolidation_groups)
        assert 'score' in consol_quality
        assert 'total_groups' in consol_quality
        assert 'average_group_size' in consol_quality
        
        # Test structure quality
        struct_quality = self.reporter._assess_structure_quality(file_analyses)
        assert 'score' in struct_quality
        assert 'categorized_percentage' in struct_quality
        assert 'category_distribution' in struct_quality
    
    def test_removal_suggestion_analysis(self):
        """Test removal suggestion analysis for different file types."""
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        
        # Track consolidated files
        consolidated_files = set()
        for group in consolidation_groups:
            consolidated_files.add(group.primary_file)
            consolidated_files.update(group.related_files)
        
        # Test analysis for each file type
        for analysis in file_analyses:
            suggestions = self.reporter._analyze_file_for_removal(
                analysis, consolidated_files, consolidation_groups
            )
            
            if analysis.filename in consolidated_files:
                # Should suggest removal for consolidated files
                assert len(suggestions) > 0
                assert any("consolidated" in s.reason.lower() for s in suggestions)
            
            elif analysis.category == Category.HISTORICAL_ARCHIVE:
                # Should suggest removal for archive files
                assert len(suggestions) > 0
                assert any("historical" in s.reason.lower() or "archive" in s.reason.lower() for s in suggestions)
    
    def test_verification_item_status_management(self):
        """Test verification item status management."""
        item = VerificationItem(
            item_id="test_001",
            description="Test verification item",
            category="Test",
            priority=Priority.MEDIUM,
            verification_method="Manual check",
            expected_result="Should pass"
        )
        
        # Initial state
        assert item.status == VerificationStatus.PENDING
        assert item.timestamp is None
        
        # Mark as verified
        item.mark_verified("Verification passed", "Actually passed")
        assert item.status == VerificationStatus.VERIFIED
        assert item.notes == "Verification passed"
        assert item.actual_result == "Actually passed"
        assert item.timestamp is not None
        
        # Create new item and mark as failed
        item2 = VerificationItem(
            item_id="test_002",
            description="Test verification item 2",
            category="Test",
            priority=Priority.HIGH
        )
        
        item2.mark_failed("Verification failed", "Actually failed")
        assert item2.status == VerificationStatus.FAILED
        assert item2.notes == "Verification failed"
        assert item2.actual_result == "Actually failed"
        assert item2.timestamp is not None
    
    def test_removal_suggestion_serialization(self):
        """Test removal suggestion serialization to dictionary."""
        suggestion = RemovalSuggestion(
            file_path=Path("test.md"),
            reason="Test removal",
            confidence=0.8,
            category=Category.FEATURE_DOCS,
            replacement_files=["replacement.md"],
            backup_recommended=True,
            manual_review_required=False,
            last_modified=datetime(2023, 1, 1, 12, 0, 0),
            file_size_mb=1.5
        )
        
        data = suggestion.to_dict()
        
        assert data['file_path'] == "test.md"
        assert data['reason'] == "Test removal"
        assert data['confidence'] == 0.8
        assert data['category'] == "feature_docs"
        assert data['replacement_files'] == ["replacement.md"]
        assert data['backup_recommended'] is True
        assert data['manual_review_required'] is False
        assert data['last_modified'] == "2023-01-01T12:00:00"
        assert data['file_size_mb'] == 1.5
    
    def test_error_integration(self):
        """Test integration with error handler."""
        # Add various types of errors
        self.error_handler.handle_file_system_error(
            PermissionError("Permission denied"), Path("test1.md"), "read_file"
        )
        
        self.error_handler.handle_content_processing_error(
            UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid'), Path("test2.md"), "content"
        )
        
        # Add critical error
        critical_error = ConsolidationError(
            error_type=ErrorType.DISK_SPACE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Critical error"
        )
        self.error_handler._record_error(critical_error)
        
        file_analyses = self.create_sample_file_analyses()
        consolidation_groups = self.create_sample_consolidation_groups()
        migration_log = self.create_sample_migration_log()
        
        # Generate report with errors
        report = self.reporter.generate_consolidation_report(
            file_analyses, consolidation_groups, migration_log
        )
        
        assert "Error Summary" in report
        assert "Total Errors: 3" in report
        assert "Critical Errors: 1" in report
        
        # Generate verification checklist with errors
        structure = self.create_sample_documentation_structure()
        checklist = self.reporter.generate_verification_checklist(
            file_analyses, consolidation_groups, structure
        )
        
        # Should include error resolution items
        error_items = [item for item in checklist if item.category == "Error Resolution"]
        assert len(error_items) > 0
    
    def test_empty_inputs_handling(self):
        """Test handling of empty inputs."""
        # Test with empty lists
        empty_analyses = []
        empty_groups = []
        empty_migration_log = MigrationLog()
        
        report = self.reporter.generate_consolidation_report(
            empty_analyses, empty_groups, empty_migration_log
        )
        
        assert "Documentation Consolidation Report" in report
        assert "0 documentation files" in report
        
        # Test quality assessment with empty inputs
        assessment = self.reporter.generate_quality_assessment(empty_analyses, empty_groups)
        assert assessment['categorization_quality']['score'] == 0.0
        assert assessment['consolidation_quality']['score'] == 0.0
        
        # Test removal suggestions with empty inputs
        suggestions = self.reporter.generate_removal_suggestions(empty_analyses, empty_groups)
        assert len(suggestions) == 0


if __name__ == "__main__":
    pytest.main([__file__])