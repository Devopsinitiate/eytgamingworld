"""
Django Convention Compliance Checker for Documentation Consolidation System.

This module implements Django-specific convention compliance checking including:
- Documentation structure validation following Django project conventions
- Markdown formatting consistency checking
- Navigation patterns validation

Task 7.3: Implement Django convention compliance checking
Requirements: 6.1, 6.2, 6.3
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    from .config import ConsolidationConfig
except ImportError:
    from config import ConsolidationConfig


class ConventionSeverity(Enum):
    """Severity levels for convention violations."""
    ERROR = "error"      # Must be fixed - breaks Django conventions
    WARNING = "warning"  # Should be fixed - deviates from best practices
    INFO = "info"       # Could be improved - minor style issues


@dataclass
class ConventionViolation:
    """Represents a Django convention violation."""
    filepath: Optional[Path]
    violation_type: str
    severity: ConventionSeverity
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        location = f"{self.filepath}:{self.line_number}" if self.line_number else str(self.filepath)
        return f"[{self.severity.value.upper()}] {location}: {self.message}"


@dataclass
class ConventionCheckResult:
    """Result of Django convention compliance checking."""
    total_files_checked: int = 0
    total_violations: int = 0
    errors: List[ConventionViolation] = field(default_factory=list)
    warnings: List[ConventionViolation] = field(default_factory=list)
    info: List[ConventionViolation] = field(default_factory=list)
    structure_compliant: bool = True
    formatting_compliant: bool = True
    navigation_compliant: bool = True
    
    @property
    def is_compliant(self) -> bool:
        """Check if documentation is fully Django convention compliant."""
        return len(self.errors) == 0
    
    @property
    def compliance_score(self) -> float:
        """Calculate compliance score as percentage (0-100)."""
        if self.total_violations == 0:
            return 100.0
        
        # Weight errors more heavily than warnings
        weighted_violations = len(self.errors) * 3 + len(self.warnings) * 2 + len(self.info)
        max_possible_score = self.total_files_checked * 10  # Assume max 10 violations per file
        
        if max_possible_score == 0:
            return 100.0
        
        score = max(0, 100 - (weighted_violations / max_possible_score * 100))
        return round(score, 1)
    
    def add_violation(self, violation: ConventionViolation) -> None:
        """Add a violation to the appropriate category."""
        self.total_violations += 1
        
        if violation.severity == ConventionSeverity.ERROR:
            self.errors.append(violation)
        elif violation.severity == ConventionSeverity.WARNING:
            self.warnings.append(violation)
        else:
            self.info.append(violation)


class DjangoConventionChecker:
    """
    Django convention compliance checker for documentation.
    
    Validates documentation against Django project conventions including:
    - Structure organization (Requirement 6.1)
    - Markdown formatting consistency (Requirement 6.2) 
    - Navigation patterns (Requirement 6.3)
    """
    
    # Django documentation structure conventions
    REQUIRED_SECTIONS = {
        'setup', 'features', 'development', 'implementation', 
        'testing', 'reference', 'archive'
    }
    
    STANDARD_FILES = {
        'README.md',           # Master index
        'CHANGELOG.md',        # Version history
        'CONTRIBUTING.md',     # Contribution guidelines
        'LICENSE',             # License information
    }
    
    # Django documentation naming conventions
    PREFERRED_FILENAMES = {
        'installation.md': 'setup/',
        'configuration.md': 'setup/',
        'troubleshooting.md': 'setup/',
        'quick-start.md': 'development/',
        'testing-guide.md': 'development/',
        'api-reference.md': 'development/',
        'glossary.md': 'reference/',
    }
    
    # Django markdown formatting conventions
    HEADING_PATTERNS = {
        'title': re.compile(r'^# .+$', re.MULTILINE),           # H1 for document title
        'section': re.compile(r'^## .+$', re.MULTILINE),       # H2 for main sections
        'subsection': re.compile(r'^### .+$', re.MULTILINE),   # H3 for subsections
    }
    
    # Django navigation patterns
    NAVIGATION_PATTERNS = {
        'toc': re.compile(r'## Table of Contents|## Contents', re.IGNORECASE),
        'breadcrumb': re.compile(r'Home\s*>\s*\w+|[A-Z]\w+\s*>\s*\w+'),
        'cross_reference': re.compile(r'\[.+?\]\(.+?\.md.*?\)'),
        'section_link': re.compile(r'\[.+?\]\(#.+?\)'),
    }
    
    def __init__(self, config: ConsolidationConfig):
        """
        Initialize the Django convention checker.
        
        Args:
            config: Configuration object with checking settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Compile additional patterns for efficiency
        self._compile_convention_patterns()
    
    def _compile_convention_patterns(self) -> None:
        """Compile regex patterns used for convention checking."""
        # Django-style code block patterns
        self.django_code_pattern = re.compile(
            r'```(?:python|django|bash|shell|sql)\n.*?```', 
            re.DOTALL | re.IGNORECASE
        )
        
        # Django-style admonition patterns (note, warning, etc.)
        self.admonition_pattern = re.compile(
            r'^\s*(?:!!! |> |\*\*Note:\*\*|\*\*Warning:\*\*|\*\*Important:\*\*)',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Django URL pattern references
        self.url_pattern = re.compile(r'urls\.py|urlpatterns|path\(|re_path\(')
        
        # Django model/view/template references
        self.django_component_pattern = re.compile(
            r'\b(?:models?|views?|templates?|forms?|admin|settings)\.py\b',
            re.IGNORECASE
        )
    
    def check_documentation_structure(self, docs_path: Path) -> ConventionCheckResult:
        """
        Check if documentation structure follows Django conventions.
        
        Args:
            docs_path: Path to the docs directory
            
        Returns:
            ConventionCheckResult with structure compliance findings
        """
        result = ConventionCheckResult()
        
        if not docs_path.exists():
            result.add_violation(ConventionViolation(
                filepath=docs_path,
                violation_type="missing_docs_directory",
                severity=ConventionSeverity.ERROR,
                message="Documentation directory 'docs/' does not exist",
                suggestion="Create docs/ directory with proper structure"
            ))
            result.structure_compliant = False
            return result
        
        # Check for required sections
        existing_sections = {d.name for d in docs_path.iterdir() if d.is_dir()}
        missing_sections = self.REQUIRED_SECTIONS - existing_sections
        
        for section in missing_sections:
            result.add_violation(ConventionViolation(
                filepath=docs_path / section,
                violation_type="missing_required_section",
                severity=ConventionSeverity.WARNING,
                message=f"Missing required documentation section: {section}/",
                suggestion=f"Create {section}/ directory for {section} documentation"
            ))
        
        # Check for standard files
        existing_files = {f.name for f in docs_path.iterdir() if f.is_file()}
        
        if 'README.md' not in existing_files:
            result.add_violation(ConventionViolation(
                filepath=docs_path / 'README.md',
                violation_type="missing_master_index",
                severity=ConventionSeverity.ERROR,
                message="Missing master index file (README.md) in docs/",
                suggestion="Create README.md as the main documentation index"
            ))
        
        # Check directory structure depth (Django prefers shallow hierarchies)
        self._check_directory_depth(docs_path, result, max_depth=3)
        
        # Update compliance status
        result.structure_compliant = len([v for v in result.errors if 'structure' in v.violation_type]) == 0
        
        return result
    
    def _check_directory_depth(self, path: Path, result: ConventionCheckResult, 
                              current_depth: int = 0, max_depth: int = 3) -> None:
        """Check directory structure doesn't exceed Django recommended depth."""
        if current_depth > max_depth:
            result.add_violation(ConventionViolation(
                filepath=path,
                violation_type="excessive_directory_depth",
                severity=ConventionSeverity.WARNING,
                message=f"Directory structure too deep ({current_depth} levels). Django prefers shallow hierarchies.",
                suggestion=f"Consider flattening directory structure to {max_depth} levels or fewer"
            ))
            return
        
        for item in path.iterdir():
            if item.is_dir():
                self._check_directory_depth(item, result, current_depth + 1, max_depth)
    
    def check_markdown_formatting(self, file_path: Path) -> ConventionCheckResult:
        """
        Check markdown formatting consistency against Django conventions.
        
        Args:
            file_path: Path to markdown file to check
            
        Returns:
            ConventionCheckResult with formatting compliance findings
        """
        result = ConventionCheckResult()
        result.total_files_checked = 1
        
        if not file_path.exists() or not file_path.suffix == '.md':
            return result
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            result.add_violation(ConventionViolation(
                filepath=file_path,
                violation_type="encoding_issue",
                severity=ConventionSeverity.ERROR,
                message="File encoding is not UTF-8",
                suggestion="Convert file to UTF-8 encoding"
            ))
            return result
        
        lines = content.split('\n')
        
        # Check heading structure
        self._check_heading_structure(file_path, content, lines, result)
        
        # Check code block formatting
        self._check_code_blocks(file_path, content, result)
        
        # Check list formatting
        self._check_list_formatting(file_path, lines, result)
        
        # Check link formatting
        self._check_link_formatting(file_path, content, result)
        
        # Check line length (Django prefers 79 characters for docs)
        self._check_line_length(file_path, lines, result, max_length=79)
        
        # Update compliance status
        result.formatting_compliant = len([v for v in result.errors if 'formatting' in v.violation_type]) == 0
        
        return result
    
    def _check_heading_structure(self, file_path: Path, content: str, 
                                lines: List[str], result: ConventionCheckResult) -> None:
        """Check heading structure follows Django conventions."""
        h1_count = len(self.HEADING_PATTERNS['title'].findall(content))
        
        if h1_count == 0:
            result.add_violation(ConventionViolation(
                filepath=file_path,
                violation_type="missing_title_heading",
                severity=ConventionSeverity.WARNING,
                message="Document missing main title (H1 heading)",
                suggestion="Add a main title using # heading syntax"
            ))
        elif h1_count > 1:
            result.add_violation(ConventionViolation(
                filepath=file_path,
                violation_type="multiple_title_headings",
                severity=ConventionSeverity.WARNING,
                message=f"Document has {h1_count} H1 headings. Django docs typically use one main title.",
                suggestion="Use only one H1 heading for the document title"
            ))
        
        # Check for proper heading hierarchy
        prev_level = 0
        for i, line in enumerate(lines, 1):
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if level > prev_level + 1:
                    result.add_violation(ConventionViolation(
                        filepath=file_path,
                        violation_type="heading_hierarchy_skip",
                        severity=ConventionSeverity.INFO,
                        message=f"Heading hierarchy skip at line {i}: H{prev_level} to H{level}",
                        line_number=i,
                        suggestion="Use sequential heading levels (H1, H2, H3, etc.)"
                    ))
                prev_level = level
    
    def _check_code_blocks(self, file_path: Path, content: str, result: ConventionCheckResult) -> None:
        """Check code block formatting follows Django conventions."""
        # Find all code blocks
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)
        
        for i, (language, code) in enumerate(code_blocks):
            if not language:
                result.add_violation(ConventionViolation(
                    filepath=file_path,
                    violation_type="unlabeled_code_block",
                    severity=ConventionSeverity.INFO,
                    message=f"Code block {i+1} missing language specification",
                    suggestion="Add language label to code blocks (e.g., ```python)"
                ))
            
            # Check for Django-specific patterns
            if 'python' in language.lower() and self.django_component_pattern.search(code):
                # This is good - Django code is properly labeled
                continue
    
    def _check_list_formatting(self, file_path: Path, lines: List[str], result: ConventionCheckResult) -> None:
        """Check list formatting consistency."""
        in_list = False
        list_marker = None
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if re.match(r'^[-*+]\s', stripped):
                current_marker = stripped[0]
                if not in_list:
                    in_list = True
                    list_marker = current_marker
                elif list_marker != current_marker:
                    result.add_violation(ConventionViolation(
                        filepath=file_path,
                        violation_type="inconsistent_list_markers",
                        severity=ConventionSeverity.INFO,
                        message=f"Inconsistent list marker at line {i}: using '{current_marker}' but list started with '{list_marker}'",
                        line_number=i,
                        suggestion="Use consistent list markers throughout the document"
                    ))
            elif re.match(r'^\d+\.\s', stripped):
                # Numbered list - check for proper numbering
                if not in_list:
                    in_list = True
                    list_marker = 'numbered'
            elif stripped == '':
                continue
            else:
                in_list = False
                list_marker = None
    
    def _check_link_formatting(self, file_path: Path, content: str, result: ConventionCheckResult) -> None:
        """Check link formatting follows Django conventions."""
        # Find all markdown links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        for link_text, link_url in links:
            # Check for empty link text
            if not link_text.strip():
                result.add_violation(ConventionViolation(
                    filepath=file_path,
                    violation_type="empty_link_text",
                    severity=ConventionSeverity.WARNING,
                    message="Link with empty text found",
                    suggestion="Provide descriptive text for all links"
                ))
            
            # Check for relative links to .md files (should work after consolidation)
            if link_url.endswith('.md') and not link_url.startswith('http'):
                # This is good - internal documentation link
                continue
    
    def _check_line_length(self, file_path: Path, lines: List[str], 
                          result: ConventionCheckResult, max_length: int = 79) -> None:
        """Check line length follows Django documentation guidelines."""
        long_lines = []
        
        for i, line in enumerate(lines, 1):
            # Skip code blocks and tables
            if line.strip().startswith('```') or '|' in line:
                continue
                
            if len(line) > max_length:
                long_lines.append(i)
        
        if long_lines:
            result.add_violation(ConventionViolation(
                filepath=file_path,
                violation_type="long_lines",
                severity=ConventionSeverity.INFO,
                message=f"{len(long_lines)} lines exceed {max_length} characters",
                suggestion=f"Consider wrapping long lines to {max_length} characters or fewer"
            ))
    
    def check_navigation_patterns(self, docs_path: Path) -> ConventionCheckResult:
        """
        Check navigation patterns follow Django conventions.
        
        Args:
            docs_path: Path to the docs directory
            
        Returns:
            ConventionCheckResult with navigation compliance findings
        """
        result = ConventionCheckResult()
        
        if not docs_path.exists():
            return result
        
        # Check master index navigation
        readme_path = docs_path / 'README.md'
        if readme_path.exists():
            self._check_master_index_navigation(readme_path, result)
        
        # Check cross-references between documents
        self._check_cross_references(docs_path, result)
        
        # Check for table of contents in longer documents
        self._check_table_of_contents(docs_path, result)
        
        # Update compliance status
        result.navigation_compliant = len([v for v in result.errors if 'navigation' in v.violation_type]) == 0
        
        return result
    
    def _check_master_index_navigation(self, readme_path: Path, result: ConventionCheckResult) -> None:
        """Check master index has proper navigation structure."""
        try:
            content = readme_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return
        
        # Check for section organization
        sections_found = []
        for section in self.REQUIRED_SECTIONS:
            if section in content.lower():
                sections_found.append(section)
        
        missing_sections = self.REQUIRED_SECTIONS - set(sections_found)
        if missing_sections:
            result.add_violation(ConventionViolation(
                filepath=readme_path,
                violation_type="incomplete_master_index",
                severity=ConventionSeverity.WARNING,
                message=f"Master index missing links to sections: {', '.join(missing_sections)}",
                suggestion="Add navigation links to all documentation sections"
            ))
        
        # Check for table of contents
        if not self.NAVIGATION_PATTERNS['toc'].search(content):
            result.add_violation(ConventionViolation(
                filepath=readme_path,
                violation_type="missing_table_of_contents",
                severity=ConventionSeverity.INFO,
                message="Master index missing table of contents",
                suggestion="Add a table of contents for better navigation"
            ))
    
    def _check_cross_references(self, docs_path: Path, result: ConventionCheckResult) -> None:
        """Check cross-references between documents are properly formatted."""
        md_files = list(docs_path.rglob('*.md'))
        result.total_files_checked += len(md_files)
        
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Find all internal links
                internal_links = self.NAVIGATION_PATTERNS['cross_reference'].findall(content)
                
                for link in internal_links:
                    # Extract the URL part
                    url_match = re.search(r'\]\(([^)]+)\)', link)
                    if url_match:
                        url = url_match.group(1)
                        
                        # Check if internal .md link exists
                        if url.endswith('.md') and not url.startswith('http'):
                            target_path = (md_file.parent / url).resolve()
                            if not target_path.exists():
                                result.add_violation(ConventionViolation(
                                    filepath=md_file,
                                    violation_type="broken_internal_link",
                                    severity=ConventionSeverity.ERROR,
                                    message=f"Broken internal link: {url}",
                                    suggestion="Update link path or create missing target file"
                                ))
                
            except UnicodeDecodeError:
                continue
    
    def _check_table_of_contents(self, docs_path: Path, result: ConventionCheckResult) -> None:
        """Check for table of contents in longer documents."""
        md_files = list(docs_path.rglob('*.md'))
        
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Count headings
                heading_count = len([line for line in lines if line.startswith('#')])
                
                # If document has many sections but no TOC, suggest adding one
                if heading_count > 5 and not self.NAVIGATION_PATTERNS['toc'].search(content):
                    result.add_violation(ConventionViolation(
                        filepath=md_file,
                        violation_type="missing_toc_in_long_document",
                        severity=ConventionSeverity.INFO,
                        message=f"Document with {heading_count} headings missing table of contents",
                        suggestion="Consider adding a table of contents for better navigation"
                    ))
                
            except UnicodeDecodeError:
                continue
    
    def check_full_compliance(self, docs_path: Path) -> ConventionCheckResult:
        """
        Perform comprehensive Django convention compliance check.
        
        Args:
            docs_path: Path to the docs directory
            
        Returns:
            ConventionCheckResult with complete compliance analysis
        """
        self.logger.info(f"Starting Django convention compliance check for {docs_path}")
        
        # Initialize combined result
        combined_result = ConventionCheckResult()
        
        # Check documentation structure
        structure_result = self.check_documentation_structure(docs_path)
        self._merge_results(combined_result, structure_result)
        
        # Check navigation patterns
        navigation_result = self.check_navigation_patterns(docs_path)
        self._merge_results(combined_result, navigation_result)
        
        # Check markdown formatting for all files
        if docs_path.exists():
            md_files = list(docs_path.rglob('*.md'))
            combined_result.total_files_checked = len(md_files)
            
            for md_file in md_files:
                formatting_result = self.check_markdown_formatting(md_file)
                self._merge_results(combined_result, formatting_result, increment_file_count=False)
        
        # Set overall compliance flags
        combined_result.structure_compliant = structure_result.structure_compliant
        combined_result.navigation_compliant = navigation_result.navigation_compliant
        combined_result.formatting_compliant = len([v for v in combined_result.errors 
                                                   if 'formatting' in v.violation_type]) == 0
        
        self.logger.info(f"Django convention check completed. "
                        f"Compliance score: {combined_result.compliance_score}%")
        
        return combined_result
    
    def _merge_results(self, target: ConventionCheckResult, source: ConventionCheckResult, 
                      increment_file_count: bool = True) -> None:
        """Merge source result into target result."""
        if increment_file_count:
            target.total_files_checked += source.total_files_checked
        target.total_violations += source.total_violations
        target.errors.extend(source.errors)
        target.warnings.extend(source.warnings)
        target.info.extend(source.info)
    
    def generate_compliance_report(self, result: ConventionCheckResult, 
                                 output_path: Optional[Path] = None) -> str:
        """
        Generate a detailed compliance report.
        
        Args:
            result: ConventionCheckResult to generate report for
            output_path: Optional path to save report file
            
        Returns:
            String containing the formatted report
        """
        report_lines = [
            "# Django Convention Compliance Report",
            "",
            f"**Overall Compliance Score:** {result.compliance_score}%",
            f"**Files Checked:** {result.total_files_checked}",
            f"**Total Violations:** {result.total_violations}",
            "",
            "## Compliance Status",
            f"- Structure Compliant: {'✅' if result.structure_compliant else '❌'}",
            f"- Formatting Compliant: {'✅' if result.formatting_compliant else '❌'}",
            f"- Navigation Compliant: {'✅' if result.navigation_compliant else '❌'}",
            "",
        ]
        
        # Add violations by severity
        if result.errors:
            report_lines.extend([
                "## Errors (Must Fix)",
                ""
            ])
            for error in result.errors:
                report_lines.append(f"- {error}")
            report_lines.append("")
        
        if result.warnings:
            report_lines.extend([
                "## Warnings (Should Fix)",
                ""
            ])
            for warning in result.warnings:
                report_lines.append(f"- {warning}")
            report_lines.append("")
        
        if result.info:
            report_lines.extend([
                "## Suggestions (Could Improve)",
                ""
            ])
            for info in result.info:
                report_lines.append(f"- {info}")
            report_lines.append("")
        
        # Add recommendations
        report_lines.extend([
            "## Recommendations",
            "",
            "1. Fix all ERROR level violations first - these break Django conventions",
            "2. Address WARNING level violations to improve compliance",
            "3. Consider INFO level suggestions for better documentation quality",
            "",
            "For more information on Django documentation conventions, see:",
            "- https://docs.djangoproject.com/en/stable/internals/contributing/writing-documentation/",
            "- https://github.com/django/django/tree/main/docs",
        ])
        
        report_content = "\n".join(report_lines)
        
        # Save to file if path provided
        if output_path:
            output_path.write_text(report_content, encoding='utf-8')
            self.logger.info(f"Compliance report saved to {output_path}")
        
        return report_content