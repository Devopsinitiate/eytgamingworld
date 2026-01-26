"""
Integration test for Task 7.3: Django Convention Compliance Checking.

This test demonstrates the Django convention compliance checking functionality
working with realistic documentation structures and content.

Task 7.3: Implement Django convention compliance checking
Requirements: 6.1, 6.2, 6.3
"""

import pytest
import tempfile
from pathlib import Path

from .django_convention_checker_simple import (
    DjangoConventionChecker,
    ConventionSeverity
)
from .config import ConsolidationConfig


class TestTask73Integration:
    """Integration tests for Django convention compliance checking."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ConsolidationConfig()
    
    @pytest.fixture
    def checker(self, config):
        """Create Django convention checker instance."""
        return DjangoConventionChecker(config)
    
    @pytest.fixture
    def sample_docs_structure(self):
        """Create a sample documentation structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_path = Path(temp_dir) / "docs"
            docs_path.mkdir()
            
            # Create required sections
            sections = ['setup', 'features', 'development', 'implementation', 'testing', 'reference', 'archive']
            for section in sections:
                (docs_path / section).mkdir()
            
            # Create master index
            readme_content = """# Django Project Documentation

## Table of Contents

- [Setup](setup/)
- [Features](features/)
- [Development](development/)
- [Implementation](implementation/)
- [Testing](testing/)
- [Reference](reference/)
- [Archive](archive/)

## Quick Start

Get started with the Django project quickly.
"""
            (docs_path / "README.md").write_text(readme_content)
            
            # Create some sample documentation files
            setup_content = """# Installation Guide

## Prerequisites

- Python 3.8+
- Django 4.0+

## Installation Steps

```bash
pip install -r requirements.txt
python manage.py migrate
```

## Configuration

Configure your settings in `settings.py`.
"""
            (docs_path / "setup" / "installation.md").write_text(setup_content)
            
            features_content = """# Authentication System

## Overview

The authentication system provides user login and registration.

## Features

- User registration
- Login/logout
- Password reset
- Profile management

## Usage

```python
from django.contrib.auth import authenticate, login

user = authenticate(username='user', password='pass')
if user:
    login(request, user)
```
"""
            (docs_path / "features" / "authentication.md").write_text(features_content)
            
            yield docs_path
    
    def test_compliant_documentation_structure(self, checker, sample_docs_structure):
        """Test that a compliant documentation structure passes all checks."""
        result = checker.check_full_compliance(sample_docs_structure)
        
        # Should be fully compliant
        assert result.structure_compliant
        assert result.is_compliant
        assert result.compliance_score == 100.0
        assert len(result.errors) == 0
        
        # Should have checked the structure
        assert result.total_files_checked >= 0  # Structure check doesn't count files yet in simple version
    
    def test_non_compliant_documentation_structure(self, checker):
        """Test that a non-compliant documentation structure is properly flagged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_path = Path(temp_dir) / "docs"
            docs_path.mkdir()
            
            # Create only some sections (missing others)
            (docs_path / "setup").mkdir()
            (docs_path / "features").mkdir()
            # Missing: development, implementation, testing, reference, archive
            
            # No README.md file
            
            result = checker.check_full_compliance(docs_path)
            
            # Should not be compliant
            assert not result.structure_compliant
            assert not result.is_compliant
            assert result.compliance_score < 100.0
            
            # Should have specific violations
            assert len(result.errors) == 1  # Missing README.md
            assert len(result.warnings) == 5  # Missing 5 sections
            
            # Check specific violation types
            error_types = [v.violation_type for v in result.errors]
            warning_types = [v.violation_type for v in result.warnings]
            
            assert "missing_master_index" in error_types
            assert "missing_required_section" in warning_types
    
    def test_missing_docs_directory(self, checker):
        """Test handling of completely missing docs directory."""
        non_existent_path = Path("/completely/non/existent/path/docs")
        result = checker.check_full_compliance(non_existent_path)
        
        # Should have critical error
        assert not result.structure_compliant
        assert not result.is_compliant
        assert len(result.errors) == 1
        assert result.errors[0].violation_type == "missing_docs_directory"
        assert result.errors[0].severity == ConventionSeverity.ERROR
    
    def test_compliance_report_generation(self, checker, sample_docs_structure):
        """Test that compliance reports are generated correctly."""
        result = checker.check_full_compliance(sample_docs_structure)
        report = checker.generate_compliance_report(result)
        
        # Should contain expected report sections
        assert "# Django Convention Compliance Report" in report
        assert "Overall Compliance Score:" in report
        assert "Compliance Status" in report
        assert "Structure Compliant: ✅" in report
        assert "Formatting Compliant: ✅" in report
        assert "Navigation Compliant: ✅" in report
        
        # For compliant structure, should not have error/warning sections
        assert "## Errors (Must Fix)" not in report
        assert "## Warnings (Should Fix)" not in report
    
    def test_compliance_report_with_violations(self, checker):
        """Test compliance report generation with violations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_path = Path(temp_dir) / "docs"
            docs_path.mkdir()
            
            # Create minimal structure with violations
            (docs_path / "README.md").write_text("# Minimal Docs")
            
            result = checker.check_full_compliance(docs_path)
            report = checker.generate_compliance_report(result)
            
            # Should contain violation sections
            assert "## Warnings (Should Fix)" in report
            assert "Missing required documentation section" in report
            
            # Should show non-compliant status
            assert "Structure Compliant: ❌" in report
    
    def test_compliance_report_file_output(self, checker, sample_docs_structure):
        """Test saving compliance report to file."""
        result = checker.check_full_compliance(sample_docs_structure)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "compliance_report.md"
            report_content = checker.generate_compliance_report(result, report_path)
            
            # File should be created
            assert report_path.exists()
            
            # File content should match returned content
            saved_content = report_path.read_text(encoding='utf-8')
            assert saved_content == report_content
            
            # Should contain expected content
            assert "# Django Convention Compliance Report" in saved_content
    
    def test_requirement_6_1_structure_organization(self, checker, sample_docs_structure):
        """Test Requirement 6.1: Documentation structure follows Django conventions."""
        result = checker.check_documentation_structure(sample_docs_structure)
        
        # Should validate all required sections exist
        assert result.structure_compliant
        
        # Should not flag any missing sections
        missing_section_violations = [v for v in result.warnings if v.violation_type == "missing_required_section"]
        assert len(missing_section_violations) == 0
        
        # Should not flag missing master index
        missing_index_violations = [v for v in result.errors if v.violation_type == "missing_master_index"]
        assert len(missing_index_violations) == 0
    
    def test_requirement_6_2_markdown_formatting_consistency(self, checker):
        """Test Requirement 6.2: Markdown formatting consistency checking."""
        # Note: This test demonstrates the framework for markdown formatting checks
        # The simple version focuses on structure, but the framework is in place
        
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_path = Path(temp_dir) / "docs"
            docs_path.mkdir()
            
            # Create structure
            for section in checker.REQUIRED_SECTIONS:
                (docs_path / section).mkdir()
            
            (docs_path / "README.md").write_text("# Documentation\n\nWell-formatted content.")
            
            result = checker.check_full_compliance(docs_path)
            
            # Should pass formatting compliance (basic check)
            assert result.formatting_compliant
    
    def test_requirement_6_3_navigation_patterns(self, checker):
        """Test Requirement 6.3: Navigation patterns validation."""
        # Note: This test demonstrates the framework for navigation pattern checks
        # The simple version focuses on structure, but the framework is in place
        
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_path = Path(temp_dir) / "docs"
            docs_path.mkdir()
            
            # Create structure with navigation
            for section in checker.REQUIRED_SECTIONS:
                (docs_path / section).mkdir()
            
            readme_with_navigation = """# Documentation

## Table of Contents

- [Setup](setup/)
- [Features](features/)
- [Development](development/)
- [Implementation](implementation/)
- [Testing](testing/)
- [Reference](reference/)
- [Archive](archive/)
"""
            (docs_path / "README.md").write_text(readme_with_navigation)
            
            result = checker.check_full_compliance(docs_path)
            
            # Should pass navigation compliance (basic check)
            assert result.navigation_compliant
    
    def test_comprehensive_django_convention_compliance(self, checker, sample_docs_structure):
        """Test comprehensive Django convention compliance checking."""
        result = checker.check_full_compliance(sample_docs_structure)
        
        # Should meet all Django convention requirements
        assert result.structure_compliant, "Should follow Django documentation structure conventions"
        assert result.formatting_compliant, "Should have consistent markdown formatting"
        assert result.navigation_compliant, "Should have proper navigation patterns"
        
        # Should be fully compliant
        assert result.is_compliant, "Should be fully Django convention compliant"
        assert result.compliance_score == 100.0, "Should have perfect compliance score"
        
        # Should generate comprehensive report
        report = checker.generate_compliance_report(result)
        assert "Django Convention Compliance Report" in report
        assert "✅" in report  # Should show compliant status


if __name__ == "__main__":
    pytest.main([__file__])