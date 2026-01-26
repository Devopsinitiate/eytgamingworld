"""
Unit tests for Django Convention Compliance Checker.

Tests the Django convention compliance checking functionality including:
- Documentation structure validation
- Markdown formatting consistency
- Navigation patterns validation

Task 7.3: Implement Django convention compliance checking
Requirements: 6.1, 6.2, 6.3
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from django_convention_checker import (
    DjangoConventionChecker,
    ConventionViolation,
    ConventionCheckResult,
    ConventionSeverity
)
from config import ConsolidationConfig


class TestDjangoConventionChecker:
    """Test suite for Django convention compliance checker."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ConsolidationConfig()
    
    @pytest.fixture
    def checker(self, config):
        """Create Django convention checker instance."""
        return DjangoConventionChecker(config)
    
    @pytest.fixture
    def temp_docs_dir(self):
        """Create temporary docs directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_path = Path(temp_dir) / "docs"
            docs_path.mkdir()
            yield docs_path
    
    def test_convention_violation_str_representation(self):
        """Test ConventionViolation string representation."""
        violation = ConventionViolation(
            filepath=Path("test.md"),
            violation_type="test_violation",
            severity=ConventionSeverity.ERROR,
            message="Test message",
            line_number=10,
            suggestion="Test suggestion"
        )
        
        expected = "[ERROR] test.md:10: Test message"
        assert str(violation) == expected
    
    def test_convention_check_result_compliance_score(self):
        """Test compliance score calculation."""
        result = ConventionCheckResult()
        result.total_files_checked = 10
        
        # No violations = 100% score
        assert result.compliance_score == 100.0
        
        # Add some violations
        result.errors = [Mock()] * 2  # 2 errors
        result.warnings = [Mock()] * 3  # 3 warnings
        result.info = [Mock()] * 1  # 1 info
        result.total_violations = 6
        
        # Score should be less than 100
        assert result.compliance_score < 100.0
        assert result.compliance_score >= 0.0
    
    def test_convention_check_result_is_compliant(self):
        """Test compliance status checking."""
        result = ConventionCheckResult()
        
        # No errors = compliant
        assert result.is_compliant is True
        
        # Add error = not compliant
        result.errors = [Mock()]
        assert result.is_compliant is False
    
    def test_add_violation_categorization(self):
        """Test violation categorization when adding to result."""
        result = ConventionCheckResult()
        
        error_violation = ConventionViolation(
            filepath=Path("test.md"),
            violation_type="test",
            severity=ConventionSeverity.ERROR,
            message="Error message"
        )
        
        warning_violation = ConventionViolation(
            filepath=Path("test.md"),
            violation_type="test",
            severity=ConventionSeverity.WARNING,
            message="Warning message"
        )
        
        info_violation = ConventionViolation(
            filepath=Path("test.md"),
            violation_type="test",
            severity=ConventionSeverity.INFO,
            message="Info message"
        )
        
        result.add_violation(error_violation)
        result.add_violation(warning_violation)
        result.add_violation(info_violation)
        
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.info) == 1
        assert result.total_violations == 3


class TestDocumentationStructureChecking:
    """Test documentation structure validation."""
    
    @pytest.fixture
    def config(self):
        return ConsolidationConfig()
    
    @pytest.fixture
    def checker(self, config):
        return DjangoConventionChecker(config)
    
    def test_missing_docs_directory(self, checker):
        """Test handling of missing docs directory."""
        non_existent_path = Path("/non/existent/docs")
        result = checker.check_documentation_structure(non_existent_path)
        
        assert not result.structure_compliant
        assert len(result.errors) == 1
        assert result.errors[0].violation_type == "missing_docs_directory"
    
    def test_missing_required_sections(self, checker, temp_docs_dir):
        """Test detection of missing required sections."""
        # Create only some required sections
        (temp_docs_dir / "setup").mkdir()
        (temp_docs_dir / "features").mkdir()
        # Missing: development, implementation, testing, reference, archive
        
        result = checker.check_documentation_structure(temp_docs_dir)
        
        missing_sections = [v for v in result.warnings if v.violation_type == "missing_required_section"]
        assert len(missing_sections) == 5  # 5 missing sections
    
    def test_missing_master_index(self, checker, temp_docs_dir):
        """Test detection of missing README.md."""
        # Create required sections but no README.md
        for section in checker.REQUIRED_SECTIONS:
            (temp_docs_dir / section).mkdir()
        
        result = checker.check_documentation_structure(temp_docs_dir)
        
        readme_errors = [v for v in result.errors if v.violation_type == "missing_master_index"]
        assert len(readme_errors) == 1
    
    def test_complete_structure_compliance(self, checker, temp_docs_dir):
        """Test fully compliant documentation structure."""
        # Create all required sections
        for section in checker.REQUIRED_SECTIONS:
            (temp_docs_dir / section).mkdir()
        
        # Create master index
        (temp_docs_dir / "README.md").write_text("# Documentation\n\nMaster index content.")
        
        result = checker.check_documentation_structure(temp_docs_dir)
        
        assert result.structure_compliant
        assert len(result.errors) == 0
    
    def test_excessive_directory_depth(self, checker, temp_docs_dir):
        """Test detection of excessive directory depth."""
        # Create deeply nested structure
        deep_path = temp_docs_dir / "features" / "auth" / "advanced" / "oauth" / "providers"
        deep_path.mkdir(parents=True)
        
        result = checker.check_documentation_structure(temp_docs_dir)
        
        depth_warnings = [v for v in result.warnings if v.violation_type == "excessive_directory_depth"]
        assert len(depth_warnings) > 0


class TestMarkdownFormattingChecking:
    """Test markdown formatting validation."""
    
    @pytest.fixture
    def config(self):
        return ConsolidationConfig()
    
    @pytest.fixture
    def checker(self, config):
        return DjangoConventionChecker(config)
    
    def test_non_markdown_file_skipped(self, checker):
        """Test that non-markdown files are skipped."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("Not a markdown file")
            
            result = checker.check_markdown_formatting(temp_path)
            
            assert result.total_files_checked == 1
            assert len(result.errors) == 0
            assert len(result.warnings) == 0
            
            temp_path.unlink()
    
    def test_encoding_error_detection(self, checker):
        """Test detection of encoding issues."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            # Write binary data that's not valid UTF-8
            with open(temp_path, 'wb') as f:
                f.write(b'\xff\xfe# Invalid UTF-8\n')
            
            result = checker.check_markdown_formatting(temp_path)
            
            encoding_errors = [v for v in result.errors if v.violation_type == "encoding_issue"]
            assert len(encoding_errors) == 1
            
            temp_path.unlink()
    
    def test_missing_title_heading(self, checker):
        """Test detection of missing H1 heading."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("## Section\n\nContent without main title.")
            
            result = checker.check_markdown_formatting(temp_path)
            
            title_warnings = [v for v in result.warnings if v.violation_type == "missing_title_heading"]
            assert len(title_warnings) == 1
            
            temp_path.unlink()
    
    def test_multiple_title_headings(self, checker):
        """Test detection of multiple H1 headings."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("# First Title\n\n# Second Title\n\nContent.")
            
            result = checker.check_markdown_formatting(temp_path)
            
            title_warnings = [v for v in result.warnings if v.violation_type == "multiple_title_headings"]
            assert len(title_warnings) == 1
            
            temp_path.unlink()
    
    def test_heading_hierarchy_skip(self, checker):
        """Test detection of heading hierarchy skips."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("# Title\n\n#### Subsection\n\nSkipped H2 and H3.")
            
            result = checker.check_markdown_formatting(temp_path)
            
            hierarchy_info = [v for v in result.info if v.violation_type == "heading_hierarchy_skip"]
            assert len(hierarchy_info) == 1
            
            temp_path.unlink()
    
    def test_unlabeled_code_block(self, checker):
        """Test detection of unlabeled code blocks."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("# Title\n\n```\ncode without language\n```")
            
            result = checker.check_markdown_formatting(temp_path)
            
            code_info = [v for v in result.info if v.violation_type == "unlabeled_code_block"]
            assert len(code_info) == 1
            
            temp_path.unlink()
    
    def test_inconsistent_list_markers(self, checker):
        """Test detection of inconsistent list markers."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("# Title\n\n- Item 1\n* Item 2\n- Item 3")
            
            result = checker.check_markdown_formatting(temp_path)
            
            list_info = [v for v in result.info if v.violation_type == "inconsistent_list_markers"]
            assert len(list_info) == 1
            
            temp_path.unlink()
    
    def test_empty_link_text(self, checker):
        """Test detection of empty link text."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("# Title\n\n[](http://example.com)")
            
            result = checker.check_markdown_formatting(temp_path)
            
            link_warnings = [v for v in result.warnings if v.violation_type == "empty_link_text"]
            assert len(link_warnings) == 1
            
            temp_path.unlink()
    
    def test_long_lines_detection(self, checker):
        """Test detection of long lines."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            long_line = "# Title\n\n" + "This is a very long line that exceeds the Django documentation guideline of 79 characters per line and should be flagged."
            temp_path.write_text(long_line)
            
            result = checker.check_markdown_formatting(temp_path)
            
            long_line_info = [v for v in result.info if v.violation_type == "long_lines"]
            assert len(long_line_info) == 1
            
            temp_path.unlink()
    
    def test_well_formatted_document(self, checker):
        """Test well-formatted document passes all checks."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            content = """# Main Title

## Section One

This is well-formatted content with proper headings.

### Subsection

```python
# Properly labeled code block
def example():
    return "Hello, Django!"
```

- Consistent list item
- Another consistent item

[Proper link](http://example.com)
"""
            temp_path.write_text(content)
            
            result = checker.check_markdown_formatting(temp_path)
            
            assert result.formatting_compliant
            assert len(result.errors) == 0
            
            temp_path.unlink()


class TestNavigationPatternChecking:
    """Test navigation pattern validation."""
    
    @pytest.fixture
    def config(self):
        return ConsolidationConfig()
    
    @pytest.fixture
    def checker(self, config):
        return DjangoConventionChecker(config)
    
    def test_missing_docs_directory_navigation(self, checker):
        """Test navigation check with missing docs directory."""
        non_existent_path = Path("/non/existent/docs")
        result = checker.check_navigation_patterns(non_existent_path)
        
        assert len(result.errors) == 0  # Should handle gracefully
        assert len(result.warnings) == 0
    
    def test_incomplete_master_index_navigation(self, checker, temp_docs_dir):
        """Test detection of incomplete master index navigation."""
        readme_content = """# Documentation

This is a basic README without proper section links.
"""
        (temp_docs_dir / "README.md").write_text(readme_content)
        
        result = checker.check_navigation_patterns(temp_docs_dir)
        
        incomplete_warnings = [v for v in result.warnings if v.violation_type == "incomplete_master_index"]
        assert len(incomplete_warnings) == 1
    
    def test_missing_table_of_contents_in_master_index(self, checker, temp_docs_dir):
        """Test detection of missing TOC in master index."""
        readme_content = """# Documentation

## Setup
Links to setup documentation.

## Features  
Links to features documentation.
"""
        (temp_docs_dir / "README.md").write_text(readme_content)
        
        result = checker.check_navigation_patterns(temp_docs_dir)
        
        toc_info = [v for v in result.info if v.violation_type == "missing_table_of_contents"]
        assert len(toc_info) == 1
    
    def test_broken_internal_links(self, checker, temp_docs_dir):
        """Test detection of broken internal links."""
        # Create a file with broken internal link
        content_with_broken_link = """# Test Document

See [missing document](missing.md) for more info.
"""
        test_file = temp_docs_dir / "test.md"
        test_file.write_text(content_with_broken_link)
        
        result = checker.check_navigation_patterns(temp_docs_dir)
        
        broken_link_errors = [v for v in result.errors if v.violation_type == "broken_internal_link"]
        assert len(broken_link_errors) == 1
    
    def test_missing_toc_in_long_document(self, checker, temp_docs_dir):
        """Test detection of missing TOC in long documents."""
        long_content = """# Long Document

## Section 1
Content

## Section 2  
Content

## Section 3
Content

## Section 4
Content

## Section 5
Content

## Section 6
Content
"""
        long_file = temp_docs_dir / "long.md"
        long_file.write_text(long_content)
        
        result = checker.check_navigation_patterns(temp_docs_dir)
        
        long_doc_info = [v for v in result.info if v.violation_type == "missing_toc_in_long_document"]
        assert len(long_doc_info) == 1
    
    def test_good_navigation_patterns(self, checker, temp_docs_dir):
        """Test well-structured navigation passes checks."""
        # Create master index with proper navigation
        readme_content = """# Documentation

## Table of Contents

- [Setup](setup/)
- [Features](features/)
- [Development](development/)
- [Implementation](implementation/)
- [Testing](testing/)
- [Reference](reference/)
- [Archive](archive/)
"""
        (temp_docs_dir / "README.md").write_text(readme_content)
        
        # Create a document with working internal links
        setup_dir = temp_docs_dir / "setup"
        setup_dir.mkdir()
        (setup_dir / "installation.md").write_text("# Installation\n\nInstallation guide.")
        
        test_content = """# Test Document

See [installation guide](setup/installation.md) for setup info.
"""
        (temp_docs_dir / "test.md").write_text(test_content)
        
        result = checker.check_navigation_patterns(temp_docs_dir)
        
        assert result.navigation_compliant
        assert len(result.errors) == 0


class TestFullComplianceChecking:
    """Test comprehensive compliance checking."""
    
    @pytest.fixture
    def config(self):
        return ConsolidationConfig()
    
    @pytest.fixture
    def checker(self, config):
        return DjangoConventionChecker(config)
    
    def test_full_compliance_check_integration(self, checker, temp_docs_dir):
        """Test full compliance check integrates all components."""
        # Create a complete, compliant documentation structure
        
        # Required sections
        for section in checker.REQUIRED_SECTIONS:
            (temp_docs_dir / section).mkdir()
        
        # Master index with proper navigation
        readme_content = """# Documentation

## Table of Contents

- [Setup](setup/)
- [Features](features/)
- [Development](development/)
- [Implementation](implementation/)
- [Testing](testing/)
- [Reference](reference/)
- [Archive](archive/)

## Quick Start

Get started with the project quickly.
"""
        (temp_docs_dir / "README.md").write_text(readme_content)
        
        # Well-formatted document
        setup_content = """# Setup Guide

## Installation

Follow these steps to install the project.

### Prerequisites

- Python 3.8+
- Django 4.0+

```python
# Install dependencies
pip install -r requirements.txt
```

## Configuration

Configure your settings properly.
"""
        (temp_docs_dir / "setup" / "installation.md").write_text(setup_content)
        
        result = checker.check_full_compliance(temp_docs_dir)
        
        assert result.total_files_checked == 2  # README.md + installation.md
        assert result.structure_compliant
        assert result.formatting_compliant
        assert result.navigation_compliant
        assert result.is_compliant
        assert result.compliance_score > 90.0
    
    def test_compliance_report_generation(self, checker, temp_docs_dir):
        """Test compliance report generation."""
        # Create minimal structure with some violations
        (temp_docs_dir / "README.md").write_text("# Docs\n\nMinimal content.")
        
        result = checker.check_full_compliance(temp_docs_dir)
        report = checker.generate_compliance_report(result)
        
        assert "# Django Convention Compliance Report" in report
        assert "Overall Compliance Score:" in report
        assert "Files Checked:" in report
        assert "Compliance Status" in report
        
        # Should contain recommendations
        assert "## Recommendations" in report
        assert "Django documentation conventions" in report
    
    def test_compliance_report_file_output(self, checker, temp_docs_dir):
        """Test compliance report file output."""
        (temp_docs_dir / "README.md").write_text("# Docs\n\nMinimal content.")
        
        result = checker.check_full_compliance(temp_docs_dir)
        report_path = temp_docs_dir / "compliance_report.md"
        
        report_content = checker.generate_compliance_report(result, report_path)
        
        assert report_path.exists()
        saved_content = report_path.read_text()
        assert saved_content == report_content
        assert "# Django Convention Compliance Report" in saved_content


if __name__ == "__main__":
    pytest.main([__file__])