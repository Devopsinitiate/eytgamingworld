"""
Integration tests for error handling and reporting systems.

Tests the integration between error handling and reporting components
to ensure they work together correctly.
"""

import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timedelta

from .error_handler import ErrorHandler, ConsolidationError, ErrorType, ErrorSeverity
from .reporting import ConsolidationReporter
from .config import ConsolidationConfig
from .models import (
    FileAnalysis, ConsolidationGroup, DocumentationStructure, 
    Category, Priority, ContentMetadata, MigrationLog, ConsolidationStrategy, ContentType
)


class TestErrorReportingIntegration:
    """Test integration between error handling and reporting systems."""
    
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
    
    def test_error_integration_in_consolidation_report(self):
        """Test that errors are properly integrated into consolidation reports."""
        # Create sample data
        file_analyses = [
            FileAnalysis(
                filepath=Path("test.md"),
                filename="test.md",
                category=Category.FEATURE_DOCS,
                content_type=ContentType.FEATURE_GUIDE,
                metadata=ContentMetadata(word_count=100),
                preservation_priority=Priority.MEDIUM,
                confidence_score=0.8
            )
        ]
        
        consolidation_groups = []
        migration_log = MigrationLog()
        
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
            message="Insufficient disk space"
        )
        self.error_handler._record_error(critical_error)
        
        # Generate report
        report = self.reporter.generate_consolidation_report(
            file_analyses, consolidation_groups, migration_log
        )
        
        # Verify error information is included
        assert "Error Summary" in report
        assert "**Total Errors:** 3" in report
        assert "**Critical Errors:** 1" in report
        assert "**Can Continue:** No" in report
        assert "Critical errors detected" in report
    
    def test_error_integration_in_verification_checklist(self):
        """Test that errors generate appropriate verification items."""
        # Create sample data
        file_analyses = [
            FileAnalysis(
                filepath=Path("test.md"),
                filename="test.md",
                category=Category.FEATURE_DOCS,
                content_type=ContentType.FEATURE_GUIDE,
                metadata=ContentMetadata(word_count=100),
                preservation_priority=Priority.MEDIUM,
                confidence_score=0.8
            )
        ]
        
        consolidation_groups = []
        structure = DocumentationStructure(root_path="docs/")
        
        # Add errors that should generate verification items
        self.error_handler.handle_file_system_error(
            PermissionError("Permission denied"), Path("failed1.md"), "read_file"
        )
        
        self.error_handler.handle_file_system_error(
            FileNotFoundError("File not found"), Path("failed2.md"), "read_file"
        )
        
        # Add critical error
        critical_error = ConsolidationError(
            error_type=ErrorType.DISK_SPACE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Critical disk space error"
        )
        self.error_handler._record_error(critical_error)
        
        # Generate verification checklist
        checklist = self.reporter.generate_verification_checklist(
            file_analyses, consolidation_groups, structure
        )
        
        # Check for error resolution verification items
        error_items = [item for item in checklist if item.category == "Error Resolution"]
        assert len(error_items) >= 2  # Should have items for critical errors and failed files
        
        # Check for critical error resolution item
        critical_items = [item for item in error_items if "critical" in item.description.lower()]
        assert len(critical_items) > 0
        assert critical_items[0].priority == Priority.CRITICAL
        
        # Check for failed files resolution item
        failed_items = [item for item in error_items if "failed" in item.description.lower()]
        assert len(failed_items) > 0
        assert failed_items[0].priority == Priority.HIGH
    
    def test_error_integration_in_quality_assessment(self):
        """Test that errors affect quality assessment metrics."""
        # Create sample data with some low confidence files
        file_analyses = [
            FileAnalysis(
                filepath=Path("good.md"),
                filename="good.md",
                category=Category.FEATURE_DOCS,
                content_type=ContentType.FEATURE_GUIDE,
                metadata=ContentMetadata(word_count=100),
                preservation_priority=Priority.MEDIUM,
                confidence_score=0.9
            ),
            FileAnalysis(
                filepath=Path("bad.md"),
                filename="bad.md",
                category=Category.UNCATEGORIZED,
                content_type=ContentType.GENERAL_DOC,
                metadata=ContentMetadata(word_count=50),
                preservation_priority=Priority.LOW,
                confidence_score=0.3
            )
        ]
        
        consolidation_groups = []
        
        # Add errors
        self.error_handler.handle_file_system_error(
            PermissionError("Permission denied"), Path("error.md"), "read_file"
        )
        
        # Generate quality assessment
        assessment = self.reporter.generate_quality_assessment(
            file_analyses, consolidation_groups
        )
        
        # Check that error rate is calculated
        assert 'error_rate' in assessment
        assert assessment['error_rate'] > 0  # Should have non-zero error rate
        
        # Check that recommendations include error-related items
        recommendations = assessment['recommendations']
        assert any("error" in rec.lower() for rec in recommendations)
    
    def test_complete_reports_bundle_with_errors(self):
        """Test that complete reports bundle includes error information."""
        # Create sample data
        file_analyses = [
            FileAnalysis(
                filepath=Path("test.md"),
                filename="test.md",
                category=Category.FEATURE_DOCS,
                content_type=ContentType.FEATURE_GUIDE,
                metadata=ContentMetadata(word_count=100),
                preservation_priority=Priority.MEDIUM,
                confidence_score=0.8
            )
        ]
        
        consolidation_groups = []
        migration_log = MigrationLog()
        structure = DocumentationStructure(root_path="docs/")
        
        # Add errors
        self.error_handler.handle_file_system_error(
            PermissionError("Permission denied"), Path("error.md"), "read_file"
        )
        
        critical_error = ConsolidationError(
            error_type=ErrorType.DISK_SPACE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Critical error"
        )
        self.error_handler._record_error(critical_error)
        
        # Export complete reports bundle
        output_dir = self.temp_dir / "reports_with_errors"
        report_paths = self.reporter.export_reports_bundle(
            file_analyses, consolidation_groups, migration_log, structure, output_dir
        )
        
        # Should include error report
        assert 'error_report' in report_paths
        assert report_paths['error_report'].exists()
        
        # Check consolidation report includes error summary
        consolidation_report_path = report_paths['consolidation_report']
        with open(consolidation_report_path, 'r', encoding='utf-8') as f:
            consolidation_content = f.read()
        
        assert "Error Summary" in consolidation_content
        assert "**Critical Errors:** 1" in consolidation_content
        
        # Check verification checklist includes error resolution items
        verification_checklist_path = report_paths['verification_checklist']
        with open(verification_checklist_path, 'r', encoding='utf-8') as f:
            verification_content = f.read()
        
        assert "Error Resolution" in verification_content
        assert "critical errors" in verification_content.lower()
        
        # Check that index mentions error report
        index_path = report_paths['index']
        with open(index_path, 'r', encoding='utf-8') as f:
            index_content = f.read()
        
        assert "Error Report" in index_content
    
    def test_error_recovery_reporting(self):
        """Test that error recovery attempts are properly reported."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("test content")
        
        # Handle an error that might have recovery attempted
        error = self.error_handler.handle_content_processing_error(
            UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid'), test_file, "content"
        )
        
        # Check that recovery information is included in the error
        assert 'recovery_result' in error.context
        
        # Generate error report
        error_report = self.error_handler.generate_error_report()
        
        # Should include information about recovery attempts
        assert "recovery" in error_report.lower() or "attempt" in error_report.lower()
    
    def test_error_statistics_in_reports(self):
        """Test that error statistics are properly included in reports."""
        # Create sample data
        file_analyses = [
            FileAnalysis(
                filepath=Path("test1.md"),
                filename="test1.md",
                category=Category.FEATURE_DOCS,
                content_type=ContentType.FEATURE_GUIDE,
                metadata=ContentMetadata(word_count=100),
                preservation_priority=Priority.MEDIUM,
                confidence_score=0.8
            ),
            FileAnalysis(
                filepath=Path("test2.md"),
                filename="test2.md",
                category=Category.SETUP_CONFIG,
                content_type=ContentType.SETUP_PROCEDURE,
                metadata=ContentMetadata(word_count=200),
                preservation_priority=Priority.HIGH,
                confidence_score=0.9
            )
        ]
        
        consolidation_groups = []
        migration_log = MigrationLog()
        
        # Add multiple errors
        for i in range(3):
            self.error_handler.handle_file_system_error(
                PermissionError(f"Permission denied {i}"), Path(f"error{i}.md"), "read_file"
            )
        
        # Generate report
        report = self.reporter.generate_consolidation_report(
            file_analyses, consolidation_groups, migration_log
        )
        
        # Check error statistics
        assert "**Total Errors:** 3" in report
        assert "Error Rate:" in report
        
        # Get error summary from error handler
        error_summary = self.error_handler.get_error_summary()
        
        # Verify statistics are consistent
        assert error_summary['total_errors'] == 3
        assert error_summary['failed_files_count'] == 3  # Each error affects a different file
        assert not error_summary['can_continue']  # No critical errors, so should be able to continue
    
    def test_no_errors_reporting(self):
        """Test reporting when no errors occur."""
        # Create sample data
        file_analyses = [
            FileAnalysis(
                filepath=Path("test.md"),
                filename="test.md",
                category=Category.FEATURE_DOCS,
                content_type=ContentType.FEATURE_GUIDE,
                metadata=ContentMetadata(word_count=100),
                preservation_priority=Priority.MEDIUM,
                confidence_score=0.8
            )
        ]
        
        consolidation_groups = []
        migration_log = MigrationLog()
        structure = DocumentationStructure(root_path="docs/")
        
        # Don't add any errors
        
        # Generate reports
        report = self.reporter.generate_consolidation_report(
            file_analyses, consolidation_groups, migration_log
        )
        
        checklist = self.reporter.generate_verification_checklist(
            file_analyses, consolidation_groups, structure
        )
        
        # Should not have error sections when no errors
        assert "Error Summary" not in report or "No errors encountered" in report
        
        # Should not have error resolution items in checklist
        error_items = [item for item in checklist if item.category == "Error Resolution"]
        assert len(error_items) == 0
        
        # Export bundle should not include error report
        output_dir = self.temp_dir / "reports_no_errors"
        report_paths = self.reporter.export_reports_bundle(
            file_analyses, consolidation_groups, migration_log, structure, output_dir
        )
        
        assert 'error_report' not in report_paths


if __name__ == "__main__":
    pytest.main([__file__])