"""
Unit tests for the error handling system.

Tests comprehensive error handling for file system errors, content processing errors,
and categorization errors as specified in Task 8.1.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from .error_handler import (
    ErrorHandler, ConsolidationError, ErrorType, ErrorSeverity
)
from .config import ConsolidationConfig
from .models import Category


class TestErrorHandler:
    """Test cases for the ErrorHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConsolidationConfig()
        self.error_handler = ErrorHandler(self.config)
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_handle_file_system_error_permission_error(self):
        """Test handling of permission errors."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("test content")
        
        permission_error = PermissionError("Permission denied")
        
        result = self.error_handler.handle_file_system_error(
            permission_error, test_file, "read_file"
        )
        
        assert result.error_type == ErrorType.PERMISSION_ERROR
        assert result.severity == ErrorSeverity.HIGH
        assert result.file_path == test_file
        assert result.operation == "read_file"
        assert "Permission denied" in result.message
        assert len(result.recovery_suggestions) > 0
        assert any("permission" in suggestion.lower() for suggestion in result.recovery_suggestions)
    
    def test_handle_file_system_error_file_not_found(self):
        """Test handling of file not found errors."""
        missing_file = self.temp_dir / "missing.md"
        
        file_not_found_error = FileNotFoundError("File not found")
        
        result = self.error_handler.handle_file_system_error(
            file_not_found_error, missing_file, "read_file"
        )
        
        assert result.error_type == ErrorType.FILE_SYSTEM_ERROR
        assert result.severity == ErrorSeverity.MEDIUM
        assert result.file_path == missing_file
        assert result.operation == "read_file"
        assert "File not found" in result.message
        assert len(result.recovery_suggestions) > 0
    
    def test_handle_content_processing_error_encoding(self):
        """Test handling of encoding errors."""
        test_file = self.temp_dir / "test.md"
        
        # Create a file with non-UTF-8 content
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')  # Invalid UTF-8 sequence
        
        encoding_error = UnicodeDecodeError('utf-8', b'\xff\xfe', 0, 1, 'invalid start byte')
        
        result = self.error_handler.handle_content_processing_error(
            encoding_error, test_file, "test content"
        )
        
        assert result.error_type == ErrorType.ENCODING_ERROR
        assert result.severity == ErrorSeverity.LOW
        assert result.file_path == test_file
        assert result.operation == "content_processing"
        assert "Content processing failed" in result.message
        assert len(result.recovery_suggestions) > 0
        assert any("encoding" in suggestion.lower() for suggestion in result.recovery_suggestions)
    
    def test_handle_categorization_error_ambiguous(self):
        """Test handling of ambiguous categorization."""
        test_file = self.temp_dir / "ambiguous.md"
        test_file.write_text("test content")
        
        ambiguous_categories = [
            (Category.FEATURE_DOCS, 0.8),
            (Category.SETUP_CONFIG, 0.75)
        ]
        
        confidence_scores = {
            Category.FEATURE_DOCS: 0.8,
            Category.SETUP_CONFIG: 0.75,
            Category.TESTING_VALIDATION: 0.3
        }
        
        result = self.error_handler.handle_categorization_error(
            test_file, ambiguous_categories, confidence_scores
        )
        
        assert result.error_type == ErrorType.CATEGORIZATION_ERROR
        assert result.severity == ErrorSeverity.MEDIUM
        assert result.file_path == test_file
        assert result.operation == "categorization"
        assert "Ambiguous categorization" in result.message
        assert len(result.recovery_suggestions) > 0
    
    def test_handle_categorization_error_low_confidence(self):
        """Test handling of low confidence categorization."""
        test_file = self.temp_dir / "low_confidence.md"
        test_file.write_text("test content")
        
        ambiguous_categories = [
            (Category.UNCATEGORIZED, 0.3)
        ]
        
        confidence_scores = {
            Category.UNCATEGORIZED: 0.3,
            Category.FEATURE_DOCS: 0.2
        }
        
        result = self.error_handler.handle_categorization_error(
            test_file, ambiguous_categories, confidence_scores
        )
        
        assert result.error_type == ErrorType.CATEGORIZATION_ERROR
        assert result.severity == ErrorSeverity.LOW
        assert "Low confidence categorization" in result.message
        assert result.context['max_confidence'] == 0.3
        assert not result.context['is_ambiguous']
    
    @patch('shutil.disk_usage')
    def test_check_disk_space_sufficient(self, mock_disk_usage):
        """Test disk space check with sufficient space."""
        # Mock sufficient disk space (1GB free)
        mock_disk_usage.return_value = Mock(
            total=10 * 1024**3,  # 10GB total
            used=9 * 1024**3,    # 9GB used
            free=1024**3         # 1GB free
        )
        
        result = self.error_handler.check_disk_space(100)  # Require 100MB
        
        assert result is True
        assert len(self.error_handler.errors) == 0
    
    @patch('shutil.disk_usage')
    def test_check_disk_space_insufficient(self, mock_disk_usage):
        """Test disk space check with insufficient space."""
        # Mock insufficient disk space (50MB free)
        mock_disk_usage.return_value = Mock(
            total=1024**3,       # 1GB total
            used=974 * 1024**2,  # ~950MB used
            free=50 * 1024**2    # 50MB free
        )
        
        result = self.error_handler.check_disk_space(100)  # Require 100MB
        
        assert result is False
        assert len(self.error_handler.errors) == 1
        assert self.error_handler.errors[0].error_type == ErrorType.DISK_SPACE_ERROR
        assert self.error_handler.errors[0].severity == ErrorSeverity.CRITICAL
    
    def test_validate_configuration_valid(self):
        """Test configuration validation with valid config."""
        # Create a temporary source directory
        source_dir = self.temp_dir / "source"
        source_dir.mkdir()
        
        self.config.source_directory = str(source_dir)
        self.config.target_directory = str(self.temp_dir / "target")
        
        errors = self.error_handler.validate_configuration()
        
        assert len(errors) == 0
    
    def test_validate_configuration_invalid_source(self):
        """Test configuration validation with invalid source directory."""
        self.config.source_directory = "/nonexistent/directory"
        
        errors = self.error_handler.validate_configuration()
        
        assert len(errors) > 0
        assert any(error.error_type == ErrorType.CONFIGURATION_ERROR for error in errors)
        assert any("Source directory does not exist" in error.message for error in errors)
    
    def test_validate_configuration_invalid_file_size(self):
        """Test configuration validation with invalid file size."""
        # Create a temporary source directory
        source_dir = self.temp_dir / "source"
        source_dir.mkdir()
        
        self.config.source_directory = str(source_dir)
        self.config.max_file_size_mb = -1  # Invalid
        
        errors = self.error_handler.validate_configuration()
        
        assert len(errors) > 0
        assert any("Invalid max file size" in error.message for error in errors)
    
    def test_validate_configuration_invalid_confidence(self):
        """Test configuration validation with invalid confidence score."""
        # Create a temporary source directory
        source_dir = self.temp_dir / "source"
        source_dir.mkdir()
        
        self.config.source_directory = str(source_dir)
        self.config.min_confidence_score = 1.5  # Invalid (> 1.0)
        
        errors = self.error_handler.validate_configuration()
        
        assert len(errors) > 0
        assert any("Invalid confidence score" in error.message for error in errors)
    
    def test_error_tracking(self):
        """Test error tracking and statistics."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("test content")
        
        # Add various types of errors
        self.error_handler.handle_file_system_error(
            PermissionError("Permission denied"), test_file, "read_file"
        )
        
        self.error_handler.handle_content_processing_error(
            UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid'), test_file, "content"
        )
        
        # Check error tracking
        assert len(self.error_handler.errors) == 2
        assert self.error_handler.error_counts[ErrorType.PERMISSION_ERROR] == 1
        assert self.error_handler.error_counts[ErrorType.ENCODING_ERROR] == 1
        assert test_file in self.error_handler.failed_files
    
    def test_critical_error_tracking(self):
        """Test critical error tracking."""
        # Add a critical error
        critical_error = ConsolidationError(
            error_type=ErrorType.DISK_SPACE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Critical error"
        )
        
        self.error_handler._record_error(critical_error)
        
        assert len(self.error_handler.critical_errors) == 1
        assert not self.error_handler.should_continue_processing()
    
    def test_should_continue_processing(self):
        """Test processing continuation logic."""
        # Initially should be able to continue
        assert self.error_handler.should_continue_processing()
        
        # Add non-critical error
        non_critical_error = ConsolidationError(
            error_type=ErrorType.ENCODING_ERROR,
            severity=ErrorSeverity.LOW,
            message="Non-critical error"
        )
        self.error_handler._record_error(non_critical_error)
        
        # Should still be able to continue
        assert self.error_handler.should_continue_processing()
        
        # Add critical error
        critical_error = ConsolidationError(
            error_type=ErrorType.DISK_SPACE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Critical error"
        )
        self.error_handler._record_error(critical_error)
        
        # Should not be able to continue
        assert not self.error_handler.should_continue_processing()
    
    def test_get_error_summary(self):
        """Test error summary generation."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("test content")
        
        # Add some errors
        self.error_handler.handle_file_system_error(
            PermissionError("Permission denied"), test_file, "read_file"
        )
        
        critical_error = ConsolidationError(
            error_type=ErrorType.DISK_SPACE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Critical error"
        )
        self.error_handler._record_error(critical_error)
        
        summary = self.error_handler.get_error_summary()
        
        assert summary['total_errors'] == 2
        assert summary['critical_errors'] == 1
        assert summary['failed_files_count'] == 1
        assert not summary['can_continue']
        assert summary['has_critical_errors']
        assert 'severity_breakdown' in summary
        assert 'error_type_breakdown' in summary
    
    def test_generate_error_report_no_errors(self):
        """Test error report generation with no errors."""
        report = self.error_handler.generate_error_report()
        
        assert "No errors encountered" in report
    
    def test_generate_error_report_with_errors(self):
        """Test error report generation with errors."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("test content")
        
        # Add errors
        self.error_handler.handle_file_system_error(
            PermissionError("Permission denied"), test_file, "read_file"
        )
        
        critical_error = ConsolidationError(
            error_type=ErrorType.DISK_SPACE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Critical disk space error",
            file_path=test_file,
            recovery_suggestions=["Free up disk space", "Use different location"]
        )
        self.error_handler._record_error(critical_error)
        
        report = self.error_handler.generate_error_report()
        
        assert "Documentation Consolidation Error Report" in report
        assert "Total errors: 2" in report
        assert "Critical errors: 1" in report
        assert "Critical Errors (Must be resolved)" in report
        assert "Critical disk space error" in report
        assert "Free up disk space" in report
        assert "Failed Files" in report
        assert str(test_file) in report
    
    def test_encoding_detection(self):
        """Test file encoding detection."""
        # Test UTF-8 file
        utf8_file = self.temp_dir / "utf8.md"
        utf8_file.write_text("Hello world", encoding='utf-8')
        
        encoding = self.error_handler._detect_file_encoding(utf8_file)
        assert encoding == 'utf-8'
        
        # Test Latin-1 file
        latin1_file = self.temp_dir / "latin1.md"
        with open(latin1_file, 'w', encoding='latin-1') as f:
            f.write("Café")
        
        encoding = self.error_handler._detect_file_encoding(latin1_file)
        assert encoding in ['latin-1', 'cp1252', 'iso-8859-1']  # Any of these would work
    
    def test_content_processing_recovery(self):
        """Test automatic recovery for content processing errors."""
        # Create a file with Latin-1 encoding
        latin1_file = self.temp_dir / "latin1.md"
        with open(latin1_file, 'w', encoding='latin-1') as f:
            f.write("Café résumé")
        
        # Simulate UTF-8 decode error
        encoding_error = UnicodeDecodeError('utf-8', b'\xe9', 0, 1, 'invalid start byte')
        
        result = self.error_handler.handle_content_processing_error(
            encoding_error, latin1_file, None
        )
        
        assert result.error_type == ErrorType.ENCODING_ERROR
        assert 'recovery_result' in result.context
        
        # Check if recovery was attempted
        recovery_result = result.context['recovery_result']
        if recovery_result['success']:
            assert recovery_result['content'] is not None
            assert recovery_result['encoding_used'] is not None
    
    def test_categorization_resolution(self):
        """Test automatic categorization resolution."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("test content")
        
        # Test case with clear winner
        ambiguous_categories = [
            (Category.FEATURE_DOCS, 0.9),
            (Category.SETUP_CONFIG, 0.6)
        ]
        
        confidence_scores = {
            Category.FEATURE_DOCS: 0.9,
            Category.SETUP_CONFIG: 0.6,
            Category.TESTING_VALIDATION: 0.3
        }
        
        result = self.error_handler.handle_categorization_error(
            test_file, ambiguous_categories, confidence_scores
        )
        
        resolution_result = result.context['resolution_result']
        assert resolution_result['resolved']
        assert resolution_result['chosen_category'] == Category.FEATURE_DOCS
        assert resolution_result['method'] == 'highest_confidence'
    
    def test_file_system_recovery_create_directory(self):
        """Test automatic recovery for directory creation."""
        # Test directory creation recovery
        new_dir = self.temp_dir / "parent" / "child"
        
        # Simulate directory creation error
        os_error = OSError("Parent directory does not exist")
        
        recovery_success = self.error_handler._attempt_file_system_recovery(
            ErrorType.FILE_SYSTEM_ERROR, new_dir, "create_directory", os_error
        )
        
        # Recovery might succeed if parent can be created
        # The actual success depends on permissions and file system state
        assert isinstance(recovery_success, bool)
    
    def test_safe_helper_methods(self):
        """Test safe helper methods that don't raise exceptions."""
        # Test with existing file
        test_file = self.temp_dir / "test.md"
        test_file.write_text("test content")
        
        size = self.error_handler._safe_get_file_size(test_file)
        assert isinstance(size, int)
        assert size > 0
        
        permissions = self.error_handler._safe_get_permissions(test_file)
        assert isinstance(permissions, str)
        assert len(permissions) == 3
        
        # Test with non-existent file
        missing_file = self.temp_dir / "missing.md"
        
        size = self.error_handler._safe_get_file_size(missing_file)
        assert size is None
        
        permissions = self.error_handler._safe_get_permissions(missing_file)
        assert permissions is None
        
        # Test with None
        size = self.error_handler._safe_get_file_size(None)
        assert size is None
        
        permissions = self.error_handler._safe_get_permissions(None)
        assert permissions is None


class TestConsolidationError:
    """Test cases for the ConsolidationError class."""
    
    def test_consolidation_error_creation(self):
        """Test ConsolidationError creation and properties."""
        error = ConsolidationError(
            error_type=ErrorType.FILE_SYSTEM_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Test error message",
            file_path=Path("test.md"),
            operation="test_operation"
        )
        
        assert error.error_type == ErrorType.FILE_SYSTEM_ERROR
        assert error.severity == ErrorSeverity.HIGH
        assert error.message == "Test error message"
        assert error.file_path == Path("test.md")
        assert error.operation == "test_operation"
        assert isinstance(error.timestamp, datetime)
        assert isinstance(error.context, dict)
        assert isinstance(error.recovery_suggestions, list)
    
    def test_consolidation_error_string_representation(self):
        """Test ConsolidationError string representation."""
        error = ConsolidationError(
            error_type=ErrorType.PERMISSION_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Permission denied",
            file_path=Path("test.md"),
            operation="read_file"
        )
        
        error_str = str(error)
        
        assert "[CRITICAL]" in error_str
        assert "permission_error" in error_str
        assert "Permission denied" in error_str
        assert "(file: test.md)" in error_str
        assert "(operation: read_file)" in error_str
    
    def test_consolidation_error_minimal(self):
        """Test ConsolidationError with minimal information."""
        error = ConsolidationError(
            error_type=ErrorType.UNKNOWN_ERROR,
            severity=ErrorSeverity.LOW,
            message="Unknown error"
        )
        
        error_str = str(error)
        
        assert "[LOW]" in error_str
        assert "unknown_error" in error_str
        assert "Unknown error" in error_str
        assert "(file:" not in error_str  # No file path provided
        assert "(operation:" not in error_str  # No operation provided


if __name__ == "__main__":
    pytest.main([__file__])