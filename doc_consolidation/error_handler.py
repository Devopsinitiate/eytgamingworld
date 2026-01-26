"""
Error handling and edge case management for the Documentation Consolidation System.

This module implements comprehensive error handling for file system errors,
content processing errors, and categorization errors as specified in Task 8.1.
"""

import os
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from .models import FileAnalysis, Category, Priority
from .config import ConsolidationConfig


class ErrorType(Enum):
    """Types of errors that can occur during consolidation."""
    FILE_SYSTEM_ERROR = "file_system_error"
    PERMISSION_ERROR = "permission_error"
    DISK_SPACE_ERROR = "disk_space_error"
    ENCODING_ERROR = "encoding_error"
    CONTENT_PROCESSING_ERROR = "content_processing_error"
    CATEGORIZATION_ERROR = "categorization_error"
    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    CRITICAL = "critical"      # System cannot continue
    HIGH = "high"             # Major functionality affected
    MEDIUM = "medium"         # Some functionality affected
    LOW = "low"              # Minor issues, system can continue
    WARNING = "warning"       # Potential issues, no immediate impact


@dataclass
class ConsolidationError:
    """Represents an error that occurred during consolidation."""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    file_path: Optional[Path] = None
    operation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    exception: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_suggestions: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        """String representation of the error."""
        parts = [
            f"[{self.severity.value.upper()}]",
            f"{self.error_type.value}:",
            self.message
        ]
        
        if self.file_path:
            parts.append(f"(file: {self.file_path})")
        
        if self.operation:
            parts.append(f"(operation: {self.operation})")
        
        return " ".join(parts)


class ErrorHandler:
    """
    Comprehensive error handler for the Documentation Consolidation System.
    
    Handles file system errors, content processing errors, categorization errors,
    and provides recovery mechanisms and user guidance.
    """
    
    def __init__(self, config: ConsolidationConfig):
        """Initialize the error handler with configuration."""
        self.config = config
        self.logger = logging.getLogger('doc_consolidation.error_handler')
        
        # Error tracking
        self.errors: List[ConsolidationError] = []
        self.error_counts: Dict[ErrorType, int] = {}
        self.critical_errors: List[ConsolidationError] = []
        
        # Recovery state
        self.recovery_attempted: Set[str] = set()
        self.failed_files: Set[Path] = set()
        self.skipped_operations: List[str] = []
        
        # Disk space monitoring
        self.min_free_space_mb = 100  # Minimum free space required
        self.space_check_interval = 10  # Check every 10 operations
        self.operation_count = 0
    
    def handle_file_system_error(self, error: Exception, file_path: Path, 
                                operation: str) -> ConsolidationError:
        """
        Handle file system errors (permissions, missing files, disk space).
        
        Args:
            error: The exception that occurred
            file_path: Path to the file that caused the error
            operation: Operation being performed when error occurred
            
        Returns:
            ConsolidationError object with details and recovery suggestions
        """
        error_type = self._classify_file_system_error(error)
        severity = self._determine_error_severity(error_type, file_path)
        
        # Create error object
        consolidation_error = ConsolidationError(
            error_type=error_type,
            severity=severity,
            message=str(error),
            file_path=file_path,
            operation=operation,
            exception=error,
            context={
                'file_exists': file_path.exists() if file_path else False,
                'file_size': self._safe_get_file_size(file_path),
                'parent_exists': file_path.parent.exists() if file_path else False,
                'permissions': self._safe_get_permissions(file_path)
            }
        )
        
        # Add recovery suggestions based on error type
        consolidation_error.recovery_suggestions = self._get_file_system_recovery_suggestions(
            error_type, file_path, error
        )
        
        # Attempt automatic recovery if appropriate
        if severity != ErrorSeverity.CRITICAL:
            recovery_success = self._attempt_file_system_recovery(
                error_type, file_path, operation, error
            )
            consolidation_error.context['recovery_attempted'] = recovery_success
        
        self._record_error(consolidation_error)
        return consolidation_error
    
    def handle_content_processing_error(self, error: Exception, file_path: Path, 
                                      content: Optional[str] = None) -> ConsolidationError:
        """
        Handle content processing errors (malformed markdown, encoding issues).
        
        Args:
            error: The exception that occurred
            file_path: Path to the file being processed
            content: File content if available
            
        Returns:
            ConsolidationError object with details and recovery suggestions
        """
        error_type = self._classify_content_processing_error(error, content)
        severity = self._determine_content_error_severity(error_type, file_path)
        
        consolidation_error = ConsolidationError(
            error_type=error_type,
            severity=severity,
            message=f"Content processing failed: {str(error)}",
            file_path=file_path,
            operation="content_processing",
            exception=error,
            context={
                'content_length': len(content) if content else 0,
                'content_preview': content[:200] if content else None,
                'encoding_detected': self._detect_file_encoding(file_path),
                'file_size': self._safe_get_file_size(file_path)
            }
        )
        
        # Add recovery suggestions
        consolidation_error.recovery_suggestions = self._get_content_processing_recovery_suggestions(
            error_type, file_path, error
        )
        
        # Attempt automatic recovery
        if severity in [ErrorSeverity.MEDIUM, ErrorSeverity.LOW]:
            recovery_result = self._attempt_content_processing_recovery(
                error_type, file_path, error
            )
            consolidation_error.context['recovery_result'] = recovery_result
        
        self._record_error(consolidation_error)
        return consolidation_error
    
    def handle_categorization_error(self, file_path: Path, 
                                  ambiguous_categories: List[Tuple[Category, float]],
                                  confidence_scores: Dict[Category, float]) -> ConsolidationError:
        """
        Handle categorization errors and ambiguous classifications.
        
        Args:
            file_path: Path to the file with categorization issues
            ambiguous_categories: List of possible categories with confidence scores
            confidence_scores: All category confidence scores
            
        Returns:
            ConsolidationError object with details and recovery suggestions
        """
        # Determine if this is truly ambiguous or just low confidence
        max_confidence = max(confidence_scores.values()) if confidence_scores else 0.0
        is_ambiguous = len([c for c in confidence_scores.values() if c > 0.5]) > 1
        
        if is_ambiguous:
            error_type = ErrorType.CATEGORIZATION_ERROR
            message = f"Ambiguous categorization: multiple categories with high confidence"
        else:
            error_type = ErrorType.CATEGORIZATION_ERROR
            message = f"Low confidence categorization: max confidence {max_confidence:.2f}"
        
        severity = ErrorSeverity.MEDIUM if is_ambiguous else ErrorSeverity.LOW
        
        consolidation_error = ConsolidationError(
            error_type=error_type,
            severity=severity,
            message=message,
            file_path=file_path,
            operation="categorization",
            context={
                'ambiguous_categories': [(cat.value, conf) for cat, conf in ambiguous_categories],
                'all_confidence_scores': {cat.value: conf for cat, conf in confidence_scores.items()},
                'max_confidence': max_confidence,
                'is_ambiguous': is_ambiguous,
                'file_size': self._safe_get_file_size(file_path),
                'file_extension': file_path.suffix if file_path else None
            }
        )
        
        # Add recovery suggestions
        consolidation_error.recovery_suggestions = self._get_categorization_recovery_suggestions(
            file_path, ambiguous_categories, confidence_scores
        )
        
        # Attempt automatic resolution
        resolution_result = self._attempt_categorization_resolution(
            file_path, ambiguous_categories, confidence_scores
        )
        consolidation_error.context['resolution_result'] = resolution_result
        
        self._record_error(consolidation_error)
        return consolidation_error
    
    def check_disk_space(self, required_space_mb: Optional[float] = None) -> bool:
        """
        Check available disk space and handle disk space errors.
        
        Args:
            required_space_mb: Required space in MB (uses default if None)
            
        Returns:
            True if sufficient space available, False otherwise
        """
        try:
            # Get disk usage for the target directory
            target_path = Path(self.config.target_directory)
            if not target_path.exists():
                target_path = target_path.parent
            
            disk_usage = shutil.disk_usage(target_path)
            free_space_mb = disk_usage.free / (1024 * 1024)
            
            required_mb = required_space_mb or self.min_free_space_mb
            
            if free_space_mb < required_mb:
                error = ConsolidationError(
                    error_type=ErrorType.DISK_SPACE_ERROR,
                    severity=ErrorSeverity.CRITICAL,
                    message=f"Insufficient disk space: {free_space_mb:.1f}MB available, "
                           f"{required_mb:.1f}MB required",
                    operation="disk_space_check",
                    context={
                        'free_space_mb': free_space_mb,
                        'required_space_mb': required_mb,
                        'total_space_mb': disk_usage.total / (1024 * 1024),
                        'used_space_mb': disk_usage.used / (1024 * 1024)
                    },
                    recovery_suggestions=[
                        "Free up disk space by deleting unnecessary files",
                        "Move the target directory to a location with more space",
                        "Reduce the scope of consolidation to require less space",
                        "Clean up temporary files and caches"
                    ]
                )
                self._record_error(error)
                return False
            
            return True
            
        except Exception as e:
            error = ConsolidationError(
                error_type=ErrorType.FILE_SYSTEM_ERROR,
                severity=ErrorSeverity.HIGH,
                message=f"Failed to check disk space: {str(e)}",
                operation="disk_space_check",
                exception=e,
                recovery_suggestions=[
                    "Check file system permissions",
                    "Verify target directory path is valid",
                    "Run with elevated permissions if necessary"
                ]
            )
            self._record_error(error)
            return False
    
    def validate_configuration(self) -> List[ConsolidationError]:
        """
        Validate configuration and return any configuration errors.
        
        Returns:
            List of configuration errors found
        """
        config_errors = []
        
        # Validate source directory
        if not os.path.exists(self.config.source_directory):
            error = ConsolidationError(
                error_type=ErrorType.CONFIGURATION_ERROR,
                severity=ErrorSeverity.CRITICAL,
                message=f"Source directory does not exist: {self.config.source_directory}",
                operation="configuration_validation",
                recovery_suggestions=[
                    "Create the source directory",
                    "Update configuration with correct source directory path",
                    "Check for typos in the directory path"
                ]
            )
            config_errors.append(error)
        
        # Validate target directory parent exists
        target_parent = Path(self.config.target_directory).parent
        if not target_parent.exists():
            error = ConsolidationError(
                error_type=ErrorType.CONFIGURATION_ERROR,
                severity=ErrorSeverity.HIGH,
                message=f"Target directory parent does not exist: {target_parent}",
                operation="configuration_validation",
                recovery_suggestions=[
                    "Create the parent directory",
                    "Update configuration with valid target directory path"
                ]
            )
            config_errors.append(error)
        
        # Validate file size limits
        if self.config.max_file_size_mb <= 0:
            error = ConsolidationError(
                error_type=ErrorType.CONFIGURATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=f"Invalid max file size: {self.config.max_file_size_mb}MB",
                operation="configuration_validation",
                recovery_suggestions=[
                    "Set max_file_size_mb to a positive value",
                    "Use default value of 10MB if unsure"
                ]
            )
            config_errors.append(error)
        
        # Validate confidence score
        if not (0.0 <= self.config.min_confidence_score <= 1.0):
            error = ConsolidationError(
                error_type=ErrorType.CONFIGURATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=f"Invalid confidence score: {self.config.min_confidence_score}",
                operation="configuration_validation",
                recovery_suggestions=[
                    "Set min_confidence_score between 0.0 and 1.0",
                    "Use default value of 0.7 if unsure"
                ]
            )
            config_errors.append(error)
        
        # Record all configuration errors
        for error in config_errors:
            self._record_error(error)
        
        return config_errors
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all errors encountered.
        
        Returns:
            Dictionary with error statistics and summaries
        """
        total_errors = len(self.errors)
        critical_count = len(self.critical_errors)
        
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = len([
                e for e in self.errors if e.severity == severity
            ])
        
        type_counts = {}
        for error_type in ErrorType:
            type_counts[error_type.value] = self.error_counts.get(error_type, 0)
        
        return {
            'total_errors': total_errors,
            'critical_errors': critical_count,
            'severity_breakdown': severity_counts,
            'error_type_breakdown': type_counts,
            'failed_files_count': len(self.failed_files),
            'skipped_operations_count': len(self.skipped_operations),
            'recovery_attempts': len(self.recovery_attempted),
            'has_critical_errors': critical_count > 0,
            'can_continue': critical_count == 0
        }
    
    def get_failed_files(self) -> List[Path]:
        """Get list of files that failed processing."""
        return list(self.failed_files)
    
    def get_critical_errors(self) -> List[ConsolidationError]:
        """Get list of critical errors that prevent continuation."""
        return self.critical_errors.copy()
    
    def should_continue_processing(self) -> bool:
        """
        Determine if processing should continue based on error state.
        
        Returns:
            True if processing can continue, False if critical errors prevent continuation
        """
        return len(self.critical_errors) == 0
    
    def generate_error_report(self) -> str:
        """
        Generate a comprehensive error report.
        
        Returns:
            Formatted error report as string
        """
        if not self.errors:
            return "No errors encountered during consolidation."
        
        report_lines = [
            "# Documentation Consolidation Error Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Total errors: {len(self.errors)}",
            f"- Critical errors: {len(self.critical_errors)}",
            f"- Failed files: {len(self.failed_files)}",
            f"- Can continue: {'Yes' if self.should_continue_processing() else 'No'}",
            ""
        ]
        
        # Add severity breakdown
        severity_counts = {}
        for error in self.errors:
            severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1
        
        if severity_counts:
            report_lines.extend([
                "## Error Breakdown by Severity",
                ""
            ])
            for severity, count in sorted(severity_counts.items(), 
                                        key=lambda x: list(ErrorSeverity).index(x[0])):
                report_lines.append(f"- {severity.value.title()}: {count}")
            report_lines.append("")
        
        # Add critical errors section
        if self.critical_errors:
            report_lines.extend([
                "## Critical Errors (Must be resolved)",
                ""
            ])
            for i, error in enumerate(self.critical_errors, 1):
                report_lines.extend([
                    f"### {i}. {error.error_type.value.replace('_', ' ').title()}",
                    f"**File:** {error.file_path or 'N/A'}",
                    f"**Message:** {error.message}",
                    f"**Operation:** {error.operation or 'N/A'}",
                    ""
                ])
                if error.recovery_suggestions:
                    report_lines.append("**Recovery Suggestions:**")
                    for suggestion in error.recovery_suggestions:
                        report_lines.append(f"- {suggestion}")
                    report_lines.append("")
        
        # Add failed files section
        if self.failed_files:
            report_lines.extend([
                "## Failed Files",
                ""
            ])
            for file_path in sorted(self.failed_files):
                report_lines.append(f"- {file_path}")
            report_lines.append("")
        
        # Add recovery suggestions
        report_lines.extend([
            "## General Recovery Recommendations",
            "",
            "1. **For file system errors:** Check file permissions and disk space",
            "2. **For encoding errors:** Verify file encoding or use fallback encoding",
            "3. **For categorization errors:** Review ambiguous files manually",
            "4. **For critical errors:** Resolve before continuing consolidation",
            ""
        ])
        
        return "\n".join(report_lines)
    
    # Private helper methods
    
    def _classify_file_system_error(self, error: Exception) -> ErrorType:
        """Classify file system errors by type."""
        if isinstance(error, PermissionError):
            return ErrorType.PERMISSION_ERROR
        elif isinstance(error, FileNotFoundError):
            return ErrorType.FILE_SYSTEM_ERROR
        elif isinstance(error, OSError) and "No space left" in str(error):
            return ErrorType.DISK_SPACE_ERROR
        elif isinstance(error, OSError):
            return ErrorType.FILE_SYSTEM_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _classify_content_processing_error(self, error: Exception, 
                                         content: Optional[str]) -> ErrorType:
        """Classify content processing errors by type."""
        if isinstance(error, UnicodeDecodeError):
            return ErrorType.ENCODING_ERROR
        elif isinstance(error, UnicodeError):
            return ErrorType.ENCODING_ERROR
        else:
            return ErrorType.CONTENT_PROCESSING_ERROR
    
    def _determine_error_severity(self, error_type: ErrorType, file_path: Path) -> ErrorSeverity:
        """Determine error severity based on type and context."""
        if error_type == ErrorType.DISK_SPACE_ERROR:
            return ErrorSeverity.CRITICAL
        elif error_type == ErrorType.PERMISSION_ERROR:
            return ErrorSeverity.HIGH
        elif error_type == ErrorType.FILE_SYSTEM_ERROR:
            return ErrorSeverity.MEDIUM
        elif error_type == ErrorType.ENCODING_ERROR:
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.MEDIUM
    
    def _determine_content_error_severity(self, error_type: ErrorType, 
                                        file_path: Path) -> ErrorSeverity:
        """Determine content processing error severity."""
        if error_type == ErrorType.ENCODING_ERROR:
            return ErrorSeverity.LOW  # Can often be recovered
        else:
            return ErrorSeverity.MEDIUM
    
    def _get_file_system_recovery_suggestions(self, error_type: ErrorType, 
                                            file_path: Path, error: Exception) -> List[str]:
        """Get recovery suggestions for file system errors."""
        suggestions = []
        
        if error_type == ErrorType.PERMISSION_ERROR:
            suggestions.extend([
                "Check file and directory permissions",
                "Run with elevated privileges if necessary",
                "Ensure the user has read/write access to the file",
                "Check if the file is locked by another process"
            ])
        elif error_type == ErrorType.DISK_SPACE_ERROR:
            suggestions.extend([
                "Free up disk space",
                "Move to a location with more available space",
                "Clean up temporary files",
                "Reduce the scope of the consolidation operation"
            ])
        elif error_type == ErrorType.FILE_SYSTEM_ERROR:
            suggestions.extend([
                "Verify the file path is correct",
                "Check if the file exists",
                "Ensure parent directories exist",
                "Check file system integrity"
            ])
        
        return suggestions
    
    def _get_content_processing_recovery_suggestions(self, error_type: ErrorType,
                                                   file_path: Path, error: Exception) -> List[str]:
        """Get recovery suggestions for content processing errors."""
        suggestions = []
        
        if error_type == ErrorType.ENCODING_ERROR:
            suggestions.extend([
                "Try different text encodings (utf-8, latin-1, cp1252)",
                "Use binary mode with error handling",
                "Check if the file is actually a text file",
                "Convert file encoding using external tools"
            ])
        else:
            suggestions.extend([
                "Check if the file is corrupted",
                "Verify the file format is supported",
                "Try processing with different settings",
                "Skip the file and process manually later"
            ])
        
        return suggestions
    
    def _get_categorization_recovery_suggestions(self, file_path: Path,
                                               ambiguous_categories: List[Tuple[Category, float]],
                                               confidence_scores: Dict[Category, float]) -> List[str]:
        """Get recovery suggestions for categorization errors."""
        suggestions = [
            "Review the file content manually to determine appropriate category",
            "Check filename patterns for categorization clues",
            "Consider the file's context within the project structure"
        ]
        
        if ambiguous_categories:
            top_categories = [cat.value for cat, _ in ambiguous_categories[:2]]
            suggestions.append(f"Consider categories: {', '.join(top_categories)}")
        
        suggestions.extend([
            "Add the file to manual review list for later processing",
            "Use the highest confidence category as fallback",
            "Create a new category if none fit appropriately"
        ])
        
        return suggestions
    
    def _attempt_file_system_recovery(self, error_type: ErrorType, file_path: Path,
                                    operation: str, error: Exception) -> bool:
        """Attempt automatic recovery for file system errors."""
        recovery_key = f"{error_type.value}_{file_path}_{operation}"
        
        if recovery_key in self.recovery_attempted:
            return False  # Already tried recovery for this specific case
        
        self.recovery_attempted.add(recovery_key)
        
        try:
            if error_type == ErrorType.FILE_SYSTEM_ERROR and operation == "create_directory":
                # Try to create parent directories
                file_path.parent.mkdir(parents=True, exist_ok=True)
                return True
            elif error_type == ErrorType.PERMISSION_ERROR and operation == "read_file":
                # Try to change permissions (if we have the right to do so)
                try:
                    file_path.chmod(0o644)
                    return True
                except:
                    pass
        except Exception as recovery_error:
            self.logger.debug(f"Recovery attempt failed: {recovery_error}")
        
        return False
    
    def _attempt_content_processing_recovery(self, error_type: ErrorType,
                                           file_path: Path, error: Exception) -> Dict[str, Any]:
        """Attempt automatic recovery for content processing errors."""
        recovery_result = {
            'success': False,
            'method': None,
            'content': None,
            'encoding_used': None
        }
        
        if error_type == ErrorType.ENCODING_ERROR:
            # Try different encodings
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    recovery_result.update({
                        'success': True,
                        'method': 'encoding_fallback',
                        'content': content,
                        'encoding_used': encoding
                    })
                    break
                except:
                    continue
            
            # If all encodings failed, try binary read with error handling
            if not recovery_result['success']:
                try:
                    with open(file_path, 'rb') as f:
                        raw_content = f.read()
                    content = raw_content.decode('utf-8', errors='ignore')
                    
                    recovery_result.update({
                        'success': True,
                        'method': 'binary_with_ignore',
                        'content': content,
                        'encoding_used': 'utf-8_ignore'
                    })
                except:
                    pass
        
        return recovery_result
    
    def _attempt_categorization_resolution(self, file_path: Path,
                                         ambiguous_categories: List[Tuple[Category, float]],
                                         confidence_scores: Dict[Category, float]) -> Dict[str, Any]:
        """Attempt automatic resolution of categorization ambiguity."""
        resolution_result = {
            'resolved': False,
            'chosen_category': None,
            'method': None,
            'confidence': 0.0
        }
        
        if not ambiguous_categories:
            return resolution_result
        
        # Method 1: Use highest confidence if significantly higher
        sorted_categories = sorted(ambiguous_categories, key=lambda x: x[1], reverse=True)
        if len(sorted_categories) >= 2:
            highest = sorted_categories[0]
            second_highest = sorted_categories[1]
            
            if highest[1] - second_highest[1] > 0.15:  # Significant difference
                resolution_result.update({
                    'resolved': True,
                    'chosen_category': highest[0],
                    'method': 'highest_confidence',
                    'confidence': highest[1]
                })
                return resolution_result
        
        # Method 2: Use category priority for ties
        category_priorities = {
            Category.IMPLEMENTATION_COMPLETION: 10,
            Category.SETUP_CONFIG: 9,
            Category.FEATURE_DOCS: 8,
            Category.TESTING_VALIDATION: 7,
            Category.INTEGRATION_GUIDES: 6,
            Category.QUICK_REFERENCES: 5,
            Category.HISTORICAL_ARCHIVE: 4,
            Category.UNCATEGORIZED: 1
        }
        
        # Find highest priority category among ambiguous ones
        best_priority = -1
        best_category = None
        best_confidence = 0.0
        
        for category, confidence in ambiguous_categories:
            priority = category_priorities.get(category, 0)
            if priority > best_priority and confidence > 0.4:  # Minimum threshold
                best_priority = priority
                best_category = category
                best_confidence = confidence
        
        if best_category:
            resolution_result.update({
                'resolved': True,
                'chosen_category': best_category,
                'method': 'priority_based',
                'confidence': best_confidence
            })
        
        return resolution_result
    
    def _record_error(self, error: ConsolidationError) -> None:
        """Record an error in the error tracking system."""
        self.errors.append(error)
        
        # Update error counts
        self.error_counts[error.error_type] = self.error_counts.get(error.error_type, 0) + 1
        
        # Track critical errors separately
        if error.severity == ErrorSeverity.CRITICAL:
            self.critical_errors.append(error)
        
        # Track failed files
        if error.file_path:
            self.failed_files.add(error.file_path)
        
        # Log the error
        log_level = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING
        }.get(error.severity, logging.WARNING)
        
        self.logger.log(log_level, str(error))
    
    def _safe_get_file_size(self, file_path: Path) -> Optional[int]:
        """Safely get file size without raising exceptions."""
        try:
            return file_path.stat().st_size if file_path and file_path.exists() else None
        except:
            return None
    
    def _safe_get_permissions(self, file_path: Path) -> Optional[str]:
        """Safely get file permissions without raising exceptions."""
        try:
            if file_path and file_path.exists():
                return oct(file_path.stat().st_mode)[-3:]
            return None
        except:
            return None
    
    def _detect_file_encoding(self, file_path: Path) -> Optional[str]:
        """Attempt to detect file encoding."""
        try:
            # Try to read a small sample with different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            with open(file_path, 'rb') as f:
                sample = f.read(1024)
            
            for encoding in encodings:
                try:
                    sample.decode(encoding)
                    return encoding
                except UnicodeDecodeError:
                    continue
            
            return None
        except:
            return None