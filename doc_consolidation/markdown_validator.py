"""
Markdown Validation Module for Documentation Consolidation System.

This module implements comprehensive markdown validation functionality including:
- Markdown syntax and formatting validation
- Internal link functionality checking
- Content integrity and completeness verification

Task 7.1: Create markdown validation
Requirements: 8.1, 8.2, 8.3
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse, unquote

from .config import ConsolidationConfig
from .models import FileAnalysis, DocumentationStructure


@dataclass
class ValidationResult:
    """Result of markdown validation for a single file."""
    filepath: Path
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    format_issues: List[str] = field(default_factory=list)
    broken_links: List[str] = field(default_factory=list)
    content_issues: List[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """Add an error and mark validation as failed."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning (doesn't fail validation)."""
        self.warnings.append(message)
    
    def add_format_issue(self, message: str) -> None:
        """Add a formatting issue and mark validation as failed."""
        self.format_issues.append(message)
        self.is_valid = False
    
    def add_broken_link(self, message: str) -> None:
        """Add a broken link and mark validation as failed."""
        self.broken_links.append(message)
        self.is_valid = False
    
    def add_content_issue(self, message: str) -> None:
        """Add a content integrity issue and mark validation as failed."""
        self.content_issues.append(message)
        self.is_valid = False


@dataclass
class ValidationSummary:
    """Summary of validation results for all files."""
    total_files: int = 0
    valid_files: int = 0
    files_with_errors: int = 0
    files_with_warnings: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    total_broken_links: int = 0
    results: List[ValidationResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate validation success rate as percentage."""
        if self.total_files == 0:
            return 100.0
        return (self.valid_files / self.total_files) * 100.0


class MarkdownValidator:
    """
    Comprehensive markdown validation system.
    
    Validates markdown files for proper formatting, functional links,
    and content integrity according to requirements 8.1, 8.2, 8.3.
    """
    
    def __init__(self, config: ConsolidationConfig):
        """
        Initialize the markdown validator.
        
        Args:
            config: Configuration object with validation settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Compile regex patterns for efficiency
        self._compile_validation_patterns()
    
    def _compile_validation_patterns(self) -> None:
        """Compile regex patterns used for validation."""
        # Markdown syntax patterns
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
        self.reference_link_pattern = re.compile(r'\[([^\]]+)\]\s*:\s*([^\s]+)')
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        self.code_block_pattern = re.compile(r'```[\s\S]*?```')
        self.inline_code_pattern = re.compile(r'`[^`]+`')
        self.table_pattern = re.compile(r'\|.*\|.*\n\|[-\s|:]+\|')
        
        # Format validation patterns - more precise
        self.malformed_heading_pattern = re.compile(r'^#{1,6}[^\s#]', re.MULTILINE)  # # followed by non-space, non-#
        self.malformed_list_pattern = re.compile(r'^\s*[-*+]\s*$', re.MULTILINE)
        self.unclosed_code_pattern = re.compile(r'```[^`]*$', re.MULTILINE | re.DOTALL)
        
        # Content integrity patterns
        self.empty_section_pattern = re.compile(r'^#+\s+.+\n\s*(?=^#+|\Z)', re.MULTILINE)
        self.duplicate_heading_pattern = re.compile(r'^(#+\s+.+)$', re.MULTILINE)
    
    def validate_file(self, filepath: Path, root_path: Optional[Path] = None) -> ValidationResult:
        """
        Validate a single markdown file comprehensively.
        
        Args:
            filepath: Path to the markdown file to validate
            root_path: Root path for resolving relative links (optional)
            
        Returns:
            ValidationResult with detailed validation information
        """
        result = ValidationResult(filepath=filepath)
        
        try:
            # Read file content
            content = self._read_file_safely(filepath)
            if content is None:
                result.add_error(f"Could not read file: {filepath}")
                return result
            
            # Validate markdown formatting (Requirement 8.1)
            self._validate_markdown_format(content, result)
            
            # Validate internal links (Requirement 8.2)
            if root_path:
                self._validate_internal_links(content, filepath, root_path, result)
            
            # Validate content integrity (Requirement 8.3)
            self._validate_content_integrity(content, result)
            
            self.logger.debug(f"Validated {filepath}: {'PASS' if result.is_valid else 'FAIL'}")
            
        except Exception as e:
            result.add_error(f"Validation failed with exception: {e}")
            self.logger.error(f"Exception validating {filepath}: {e}")
        
        return result
    
    def validate_directory(self, directory_path: Path, 
                          structure: Optional[DocumentationStructure] = None) -> ValidationSummary:
        """
        Validate all markdown files in a directory structure.
        
        Args:
            directory_path: Root directory to validate
            structure: Optional DocumentationStructure for enhanced validation
            
        Returns:
            ValidationSummary with comprehensive results
        """
        self.logger.info(f"Validating markdown files in: {directory_path}")
        
        summary = ValidationSummary()
        
        # Discover all markdown files
        markdown_files = self._discover_markdown_files(directory_path)
        summary.total_files = len(markdown_files)
        
        if not markdown_files:
            self.logger.warning(f"No markdown files found in {directory_path}")
            return summary
        
        # Validate each file
        for filepath in markdown_files:
            result = self.validate_file(filepath, directory_path)
            summary.results.append(result)
            
            # Update summary statistics
            if result.is_valid:
                summary.valid_files += 1
            else:
                summary.files_with_errors += 1
            
            if result.warnings:
                summary.files_with_warnings += 1
            
            summary.total_errors += len(result.errors) + len(result.format_issues) + \
                                  len(result.broken_links) + len(result.content_issues)
            summary.total_warnings += len(result.warnings)
            summary.total_broken_links += len(result.broken_links)
        
        self.logger.info(f"Validation complete: {summary.valid_files}/{summary.total_files} files valid "
                        f"({summary.success_rate:.1f}% success rate)")
        
        return summary
    
    def _validate_markdown_format(self, content: str, result: ValidationResult) -> None:
        """
        Validate markdown formatting according to requirement 8.1.
        
        Args:
            content: Markdown content to validate
            result: ValidationResult to update with findings
        """
        # Check for malformed headings
        malformed_headings = self.malformed_heading_pattern.findall(content)
        for heading in malformed_headings:
            result.add_format_issue(f"Malformed heading (missing space after #): {heading}")
        
        # Check for unclosed code blocks - count opening and closing fences
        code_fence_count = content.count('```')
        if code_fence_count % 2 != 0:
            result.add_format_issue("Unbalanced code fences (odd number of ``` markers)")
        
        # Don't use the unclosed_code_pattern as it's too aggressive
        
        # Check for malformed lists
        malformed_lists = self.malformed_list_pattern.findall(content)
        if malformed_lists:
            result.add_format_issue("Empty list items found (list markers without content)")
        
        # Validate table formatting - be more lenient
        tables = self.table_pattern.findall(content)
        for table in tables:
            if not self._validate_table_format(table):
                result.add_warning("Table formatting could be improved")  # Warning instead of error
        
        # Check for consistent heading hierarchy
        self._validate_heading_hierarchy(content, result)
        
        # Check for proper link formatting
        self._validate_link_formatting(content, result)
    
    def _validate_internal_links(self, content: str, filepath: Path, 
                               root_path: Path, result: ValidationResult) -> None:
        """
        Validate internal link functionality according to requirement 8.2.
        
        Args:
            content: Markdown content to validate
            filepath: Path to the file being validated
            root_path: Root path for resolving relative links
            result: ValidationResult to update with findings
        """
        # Find all markdown links
        links = self.link_pattern.findall(content)
        
        for link_text, link_url in links:
            # Skip external links
            if self._is_external_link(link_url):
                continue
            
            # Skip anchor-only links (they reference sections within the same file)
            if link_url.startswith('#'):
                # Validate anchor exists in current file
                if not self._validate_anchor_exists(content, link_url[1:]):
                    result.add_broken_link(f"Anchor not found: {link_text} -> {link_url}")
                continue
            
            # Resolve relative link path
            resolved_path = self._resolve_link_path(link_url, filepath, root_path)
            
            if not resolved_path.exists():
                result.add_broken_link(f"Broken link: {link_text} -> {link_url}")
            elif resolved_path.is_file():
                # If link includes anchor, validate it exists in target file
                if '#' in link_url:
                    anchor = link_url.split('#', 1)[1]
                    target_content = self._read_file_safely(resolved_path)
                    if target_content and not self._validate_anchor_exists(target_content, anchor):
                        result.add_broken_link(f"Anchor not found in target: {link_text} -> {link_url}")
        
        # Validate reference-style links
        ref_links = self.reference_link_pattern.findall(content)
        for ref_name, ref_url in ref_links:
            if not self._is_external_link(ref_url):
                resolved_path = self._resolve_link_path(ref_url, filepath, root_path)
                if not resolved_path.exists():
                    result.add_broken_link(f"Broken reference link: [{ref_name}] -> {ref_url}")
    
    def _validate_content_integrity(self, content: str, result: ValidationResult) -> None:
        """
        Validate content integrity and completeness according to requirement 8.3.
        
        Args:
            content: Markdown content to validate
            result: ValidationResult to update with findings
        """
        # Check for empty content
        if not content.strip():
            result.add_content_issue("File is empty or contains only whitespace")
            return
        
        # Check for empty sections (headings with no content)
        empty_sections = self.empty_section_pattern.findall(content)
        for section in empty_sections:
            result.add_content_issue(f"Empty section found: {section}")
        
        # Check for duplicate headings (potential content duplication)
        headings = self.duplicate_heading_pattern.findall(content)
        heading_counts = {}
        for heading in headings:
            heading_text = heading.strip('#').strip()
            heading_counts[heading_text] = heading_counts.get(heading_text, 0) + 1
        
        for heading_text, count in heading_counts.items():
            if count > 1:
                result.add_warning(f"Duplicate heading found: {heading_text} (appears {count} times)")
        
        # Check for minimum content requirements
        word_count = len(content.split())
        if word_count < 10:
            result.add_content_issue(f"Content too short: only {word_count} words")
        
        # Check for proper document structure
        if not self.heading_pattern.search(content):
            result.add_warning("No headings found - document may lack structure")
        
        # Validate image references exist
        images = self.image_pattern.findall(content)
        for alt_text, image_url in images:
            if not self._is_external_link(image_url):
                # For now, just warn about local images as they may be relative to different paths
                result.add_warning(f"Local image reference found: {alt_text} -> {image_url}")
    
    def _validate_table_format(self, table_content: str) -> bool:
        """
        Validate table formatting.
        
        Args:
            table_content: Table content to validate
            
        Returns:
            True if table is properly formatted
        """
        lines = table_content.strip().split('\n')
        if len(lines) < 2:
            return False
        
        # Check that all rows have the same number of columns
        column_counts = []
        for line in lines:
            if '|' in line:
                # Count columns (number of | minus 1, accounting for leading/trailing |)
                columns = len([col for col in line.split('|') if col.strip()])
                column_counts.append(columns)
        
        # All rows should have the same number of columns
        return len(set(column_counts)) <= 1
    
    def _validate_heading_hierarchy(self, content: str, result: ValidationResult) -> None:
        """
        Validate heading hierarchy is logical.
        
        Args:
            content: Markdown content to validate
            result: ValidationResult to update with findings
        """
        headings = self.heading_pattern.findall(content)
        if not headings:
            return
        
        prev_level = 0
        for heading_hashes, heading_text in headings:
            current_level = len(heading_hashes)
            
            # Check for skipped heading levels (e.g., h1 -> h3)
            if prev_level > 0 and current_level > prev_level + 1:
                result.add_warning(f"Heading level skipped: {heading_text} "
                                 f"(level {current_level} after level {prev_level})")
            
            prev_level = current_level
    
    def _validate_link_formatting(self, content: str, result: ValidationResult) -> None:
        """
        Validate link formatting is correct.
        
        Args:
            content: Markdown content to validate
            result: ValidationResult to update with findings
        """
        # Check for malformed links (missing closing brackets/parentheses)
        malformed_patterns = [
            r'\[[^\]]*\([^)]*$',  # Missing closing parenthesis
            r'\[[^\]]*$',         # Missing closing bracket
            r'\([^)]*\]',         # Brackets in wrong order
        ]
        
        for pattern in malformed_patterns:
            if re.search(pattern, content, re.MULTILINE):
                result.add_format_issue("Malformed link syntax detected")
                break
    
    def _validate_anchor_exists(self, content: str, anchor: str) -> bool:
        """
        Check if an anchor (heading) exists in the content.
        
        Args:
            content: Content to search for anchor
            anchor: Anchor name to find
            
        Returns:
            True if anchor exists
        """
        # Convert anchor to expected heading format
        anchor_text = unquote(anchor).replace('-', ' ').replace('_', ' ').lower()
        
        # Find all headings and check for match
        headings = self.heading_pattern.findall(content)
        for _, heading_text in headings:
            # Normalize heading text for comparison
            normalized_heading = re.sub(r'[^\w\s]', '', heading_text).lower().strip()
            if normalized_heading == anchor_text:
                return True
        
        return False
    
    def _resolve_link_path(self, link_url: str, current_file: Path, root_path: Path) -> Path:
        """
        Resolve a relative link path to an absolute path.
        
        Args:
            link_url: URL to resolve
            current_file: Current file path (for relative resolution)
            root_path: Root path for absolute resolution
            
        Returns:
            Resolved Path object
        """
        # Remove anchor if present
        clean_url = link_url.split('#')[0]
        
        # Handle different link formats
        if clean_url.startswith('./'):
            # Relative to current directory
            return current_file.parent / clean_url[2:]
        elif clean_url.startswith('../'):
            # Relative to parent directory
            return current_file.parent / clean_url
        elif clean_url.startswith('/'):
            # Absolute from root
            return root_path / clean_url[1:]
        else:
            # Relative to current directory (no prefix)
            return current_file.parent / clean_url
    
    def _is_external_link(self, url: str) -> bool:
        """
        Check if a URL is an external link.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is external
        """
        return url.startswith(('http://', 'https://', 'ftp://', 'mailto:', 'tel:'))
    
    def _discover_markdown_files(self, directory: Path) -> List[Path]:
        """
        Discover all markdown files in a directory recursively.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of markdown file paths
        """
        markdown_files = []
        
        for extension in self.config.file_extensions:
            pattern = f"**/*{extension}"
            markdown_files.extend(directory.glob(pattern))
        
        # Filter out excluded files
        filtered_files = []
        for file_path in markdown_files:
            if self._should_include_file(file_path):
                filtered_files.append(file_path)
        
        return sorted(filtered_files)
    
    def _should_include_file(self, file_path: Path) -> bool:
        """
        Check if a file should be included based on exclude patterns.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be included
        """
        # Convert to string with forward slashes for consistent pattern matching
        file_str = str(file_path).replace('\\', '/')
        
        for pattern in self.config.exclude_patterns:
            # Convert pattern to regex, handling both * and ** wildcards
            regex_pattern = pattern.replace('**', '.*').replace('*', '[^/]*')
            if re.search(regex_pattern, file_str):
                return False
        
        return True
    
    def _read_file_safely(self, filepath: Path) -> Optional[str]:
        """
        Safely read a file with encoding detection.
        
        Args:
            filepath: Path to file to read
            
        Returns:
            File content as string, or None if reading failed
        """
        encodings_to_try = [
            self.config.encoding,
            'utf-8',
            'utf-8-sig',
            'latin-1',
            'cp1252'
        ]
        
        for encoding in encodings_to_try:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                self.logger.error(f"Error reading {filepath}: {e}")
                return None
        
        self.logger.error(f"Could not read {filepath} with any encoding")
        return None
    
    def generate_validation_report(self, summary: ValidationSummary, output_path: Path) -> bool:
        """
        Generate a comprehensive validation report.
        
        Args:
            summary: ValidationSummary with results
            output_path: Path where to save the report
            
        Returns:
            True if report was generated successfully
        """
        try:
            sections = []
            
            # Header
            sections.append("# Markdown Validation Report")
            sections.append("")
            sections.append(f"**Generated:** {Path().cwd()}")
            sections.append(f"**Total Files:** {summary.total_files}")
            sections.append(f"**Valid Files:** {summary.valid_files}")
            sections.append(f"**Success Rate:** {summary.success_rate:.1f}%")
            sections.append("")
            
            # Summary Statistics
            sections.append("## Summary Statistics")
            sections.append("")
            sections.append(f"- **Files with Errors:** {summary.files_with_errors}")
            sections.append(f"- **Files with Warnings:** {summary.files_with_warnings}")
            sections.append(f"- **Total Errors:** {summary.total_errors}")
            sections.append(f"- **Total Warnings:** {summary.total_warnings}")
            sections.append(f"- **Broken Links:** {summary.total_broken_links}")
            sections.append("")
            
            # Detailed Results
            if summary.files_with_errors > 0:
                sections.append("## Files with Errors")
                sections.append("")
                
                for result in summary.results:
                    if not result.is_valid:
                        sections.append(f"### {result.filepath}")
                        sections.append("")
                        
                        if result.errors:
                            sections.append("**Errors:**")
                            for error in result.errors:
                                sections.append(f"- {error}")
                            sections.append("")
                        
                        if result.format_issues:
                            sections.append("**Format Issues:**")
                            for issue in result.format_issues:
                                sections.append(f"- {issue}")
                            sections.append("")
                        
                        if result.broken_links:
                            sections.append("**Broken Links:**")
                            for link in result.broken_links:
                                sections.append(f"- {link}")
                            sections.append("")
                        
                        if result.content_issues:
                            sections.append("**Content Issues:**")
                            for issue in result.content_issues:
                                sections.append(f"- {issue}")
                            sections.append("")
            
            # Warnings
            if summary.files_with_warnings > 0:
                sections.append("## Files with Warnings")
                sections.append("")
                
                for result in summary.results:
                    if result.warnings:
                        sections.append(f"### {result.filepath}")
                        sections.append("")
                        sections.append("**Warnings:**")
                        for warning in result.warnings:
                            sections.append(f"- {warning}")
                        sections.append("")
            
            # Write report
            report_content = "\n".join(sections)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"Validation report generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate validation report: {e}")
            return False