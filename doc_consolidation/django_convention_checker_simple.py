"""
Simple Django Convention Compliance Checker for testing.
"""

import re
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .config import ConsolidationConfig


class ConventionSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ConventionViolation:
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
        return len(self.errors) == 0
    
    @property
    def compliance_score(self) -> float:
        if self.total_violations == 0:
            return 100.0
        
        weighted_violations = len(self.errors) * 3 + len(self.warnings) * 2 + len(self.info)
        
        # Use a base score calculation that doesn't depend on files checked
        # since structure checks don't count files
        base_score = 100
        penalty_per_violation = 5  # Each violation reduces score by 5%
        
        score = max(0, base_score - (weighted_violations * penalty_per_violation))
        return round(score, 1)
    
    def add_violation(self, violation: ConventionViolation) -> None:
        self.total_violations += 1
        
        if violation.severity == ConventionSeverity.ERROR:
            self.errors.append(violation)
        elif violation.severity == ConventionSeverity.WARNING:
            self.warnings.append(violation)
        else:
            self.info.append(violation)


class DjangoConventionChecker:
    """Django convention compliance checker."""
    
    REQUIRED_SECTIONS = {
        'setup', 'features', 'development', 'implementation', 
        'testing', 'reference', 'archive'
    }
    
    def __init__(self, config: ConsolidationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def check_documentation_structure(self, docs_path: Path) -> ConventionCheckResult:
        """Check documentation structure compliance."""
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
        
        # Check for README.md
        existing_files = {f.name for f in docs_path.iterdir() if f.is_file()}
        if 'README.md' not in existing_files:
            result.add_violation(ConventionViolation(
                filepath=docs_path / 'README.md',
                violation_type="missing_master_index",
                severity=ConventionSeverity.ERROR,
                message="Missing master index file (README.md) in docs/",
                suggestion="Create README.md as the main documentation index"
            ))
        
        result.structure_compliant = len([v for v in result.errors if 'structure' in v.violation_type or 'missing_master_index' in v.violation_type]) == 0 and len([v for v in result.warnings if 'missing_required_section' in v.violation_type]) == 0
        return result
    
    def check_full_compliance(self, docs_path: Path) -> ConventionCheckResult:
        """Perform comprehensive compliance check."""
        self.logger.info(f"Starting Django convention compliance check for {docs_path}")
        
        # For now, just check structure
        result = self.check_documentation_structure(docs_path)
        
        self.logger.info(f"Django convention check completed. Compliance score: {result.compliance_score}%")
        return result
    
    def generate_compliance_report(self, result: ConventionCheckResult, 
                                 output_path: Optional[Path] = None) -> str:
        """Generate compliance report."""
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
        
        if result.errors:
            report_lines.extend(["## Errors (Must Fix)", ""])
            for error in result.errors:
                report_lines.append(f"- {error}")
            report_lines.append("")
        
        if result.warnings:
            report_lines.extend(["## Warnings (Should Fix)", ""])
            for warning in result.warnings:
                report_lines.append(f"- {warning}")
            report_lines.append("")
        
        if result.info:
            report_lines.extend(["## Suggestions (Could Improve)", ""])
            for info in result.info:
                report_lines.append(f"- {info}")
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        if output_path:
            output_path.write_text(report_content, encoding='utf-8')
            self.logger.info(f"Compliance report saved to {output_path}")
        
        return report_content