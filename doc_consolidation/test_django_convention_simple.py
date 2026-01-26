"""
Simple test for Django Convention Compliance Checker.
"""

import pytest
import tempfile
from pathlib import Path

from .django_convention_checker_simple import (
    DjangoConventionChecker,
    ConventionViolation,
    ConventionCheckResult,
    ConventionSeverity
)
from .config import ConsolidationConfig


def test_django_convention_checker_basic():
    """Test basic Django convention checker functionality."""
    config = ConsolidationConfig()
    checker = DjangoConventionChecker(config)
    
    # Test with non-existent directory
    non_existent_path = Path("/non/existent/docs")
    result = checker.check_documentation_structure(non_existent_path)
    
    assert not result.structure_compliant
    assert len(result.errors) == 1
    assert result.errors[0].violation_type == "missing_docs_directory"


def test_django_convention_checker_with_temp_dir():
    """Test Django convention checker with temporary directory."""
    config = ConsolidationConfig()
    checker = DjangoConventionChecker(config)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_path = Path(temp_dir) / "docs"
        docs_path.mkdir()
        
        # Test with empty docs directory
        result = checker.check_documentation_structure(docs_path)
        
        # Should have warnings for missing sections and error for missing README
        assert not result.structure_compliant
        assert len(result.warnings) == 7  # 7 missing sections
        assert len(result.errors) == 1    # missing README.md
        
        # Create README.md
        (docs_path / "README.md").write_text("# Documentation\n\nMaster index.")
        
        # Create all required sections
        for section in checker.REQUIRED_SECTIONS:
            (docs_path / section).mkdir()
        
        # Test again - should be compliant now
        result = checker.check_documentation_structure(docs_path)
        assert result.structure_compliant
        assert len(result.errors) == 0


def test_convention_violation_str():
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


def test_convention_check_result_compliance_score():
    """Test compliance score calculation."""
    result = ConventionCheckResult()
    result.total_files_checked = 10
    
    # No violations = 100% score
    assert result.compliance_score == 100.0
    
    # Add some violations
    result.add_violation(ConventionViolation(
        filepath=Path("test.md"),
        violation_type="test",
        severity=ConventionSeverity.ERROR,
        message="Error"
    ))
    
    result.add_violation(ConventionViolation(
        filepath=Path("test.md"),
        violation_type="test",
        severity=ConventionSeverity.WARNING,
        message="Warning"
    ))
    
    # Score should be less than 100
    assert result.compliance_score < 100.0
    assert result.compliance_score >= 0.0


def test_full_compliance_check():
    """Test full compliance check integration."""
    config = ConsolidationConfig()
    checker = DjangoConventionChecker(config)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_path = Path(temp_dir) / "docs"
        docs_path.mkdir()
        
        # Create complete structure
        for section in checker.REQUIRED_SECTIONS:
            (docs_path / section).mkdir()
        
        (docs_path / "README.md").write_text("# Documentation\n\nComplete structure.")
        
        result = checker.check_full_compliance(docs_path)
        
        assert result.structure_compliant
        assert result.is_compliant
        assert result.compliance_score == 100.0


def test_compliance_report_generation():
    """Test compliance report generation."""
    config = ConsolidationConfig()
    checker = DjangoConventionChecker(config)
    
    # Create a result with some violations
    result = ConventionCheckResult()
    result.total_files_checked = 5
    
    result.add_violation(ConventionViolation(
        filepath=Path("test.md"),
        violation_type="test_error",
        severity=ConventionSeverity.ERROR,
        message="Test error message"
    ))
    
    result.add_violation(ConventionViolation(
        filepath=Path("test.md"),
        violation_type="test_warning",
        severity=ConventionSeverity.WARNING,
        message="Test warning message"
    ))
    
    report = checker.generate_compliance_report(result)
    
    assert "# Django Convention Compliance Report" in report
    assert "Overall Compliance Score:" in report
    assert "**Files Checked:** 5" in report
    assert "**Total Violations:** 2" in report
    assert "## Errors (Must Fix)" in report
    assert "## Warnings (Should Fix)" in report
    assert "Test error message" in report
    assert "Test warning message" in report


if __name__ == "__main__":
    pytest.main([__file__])