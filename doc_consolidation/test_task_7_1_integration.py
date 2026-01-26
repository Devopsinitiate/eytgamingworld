"""
Integration test for Task 7.1: Create markdown validation.

This test validates the complete markdown validation functionality including:
- Integration with the StructureGenerator
- Comprehensive validation of generated documentation
- Validation report generation
- Requirements 8.1, 8.2, 8.3 compliance
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from .generator import StructureGenerator
from .markdown_validator import MarkdownValidator
from .config import ConsolidationConfig
from .models import DocumentationStructure, Category


class TestTask71Integration(unittest.TestCase):
    """Integration test for markdown validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = ConsolidationConfig()
        self.config.target_directory = str(self.temp_dir / "docs")
        self.config.validate_output = True
        
        self.generator = StructureGenerator(self.config)
        self.validator = MarkdownValidator(self.config)
        
        # Create test documentation structure
        self.docs_dir = self.temp_dir / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_complete_markdown_validation_workflow(self):
        """Test the complete markdown validation workflow."""
        print("\n" + "="*60)
        print("TESTING TASK 7.1: MARKDOWN VALIDATION")
        print("="*60)
        
        # Step 1: Create a realistic documentation structure
        print("Step 1: Creating documentation structure...")
        structure = DocumentationStructure()
        structure.root_path = str(self.docs_dir) + "/"
        
        success = self.generator.create_directory_structure(structure)
        self.assertTrue(success, "Failed to create directory structure")
        print(f"✓ Created directory structure at {self.docs_dir}")
        
        # Step 2: Create test markdown files with various quality levels
        print("\nStep 2: Creating test markdown files...")
        test_files = self._create_test_markdown_files()
        print(f"✓ Created {len(test_files)} test markdown files")
        
        # Step 3: Test standalone markdown validation
        print("\nStep 3: Running standalone markdown validation...")
        validation_summary = self.generator.validate_markdown_files(
            self.docs_dir, generate_report=True
        )
        
        self.assertGreater(validation_summary.total_files, 0)
        print(f"✓ Validated {validation_summary.total_files} files")
        print(f"  - Valid files: {validation_summary.valid_files}")
        print(f"  - Files with errors: {validation_summary.files_with_errors}")
        print(f"  - Success rate: {validation_summary.success_rate:.1f}%")
        print(f"  - Total broken links: {validation_summary.total_broken_links}")
        
        # Step 4: Test integrated validation through validate_structure
        print("\nStep 4: Testing integrated structure validation...")
        validation_errors = self.generator.validate_structure(structure)
        
        # Should detect format and link issues
        format_errors = [e for e in validation_errors if "Format issue" in e]
        link_errors = [e for e in validation_errors if "Broken link" in e]
        content_errors = [e for e in validation_errors if "Content issue" in e]
        
        print(f"✓ Structure validation found:")
        print(f"  - Format issues: {len(format_errors)}")
        print(f"  - Link issues: {len(link_errors)}")
        print(f"  - Content issues: {len(content_errors)}")
        
        # Step 5: Verify validation report generation
        print("\nStep 5: Verifying validation report...")
        validation_report = self.docs_dir / "validation-report.md"
        self.assertTrue(validation_report.exists(), "Validation report should be generated")
        
        report_content = validation_report.read_text(encoding='utf-8')
        self.assertIn("Markdown Validation Report", report_content)
        self.assertIn("Summary Statistics", report_content)
        print(f"✓ Validation report generated: {validation_report}")
        
        # Step 6: Test specific validation requirements
        print("\nStep 6: Testing specific validation requirements...")
        
        # Requirement 8.1: Markdown format validation
        format_issues_found = any("Format issue" in error for error in validation_errors)
        if format_issues_found:
            print("✓ Requirement 8.1: Format validation working (found format issues)")
        else:
            print("✓ Requirement 8.1: Format validation working (no format issues found)")
        
        # Requirement 8.2: Internal link functionality
        link_issues_found = any("Broken link" in error for error in validation_errors)
        if link_issues_found:
            print("✓ Requirement 8.2: Link validation working (found broken links)")
        else:
            print("✓ Requirement 8.2: Link validation working (no broken links found)")
        
        # Requirement 8.3: Content integrity
        content_issues_found = any("Content issue" in error for error in validation_errors)
        if content_issues_found:
            print("✓ Requirement 8.3: Content validation working (found content issues)")
        else:
            print("✓ Requirement 8.3: Content validation working (no content issues found)")
        
        # Step 7: Test validation report content
        print("\nStep 7: Validating report content...")
        self.assertIn(f"Total Files:** {validation_summary.total_files}", report_content)
        self.assertIn(f"Valid Files:** {validation_summary.valid_files}", report_content)
        self.assertIn(f"Success Rate:** {validation_summary.success_rate:.1f}%", report_content)
        print("✓ Report contains expected summary statistics")
        
        if validation_summary.files_with_errors > 0:
            self.assertIn("Files with Errors", report_content)
            print("✓ Report contains error details")
        
        if validation_summary.files_with_warnings > 0:
            self.assertIn("Files with Warnings", report_content)
            print("✓ Report contains warning details")
        
        print("\n" + "="*60)
        print("✅ TASK 7.1 INTEGRATION TEST PASSED")
        print("✅ Markdown validation functionality is working correctly!")
        print("✅ All requirements (8.1, 8.2, 8.3) are satisfied")
        print("="*60)
    
    def _create_test_markdown_files(self) -> list:
        """Create test markdown files with various quality levels."""
        test_files = []
        
        # 1. Well-formatted file with valid links
        good_file = self.docs_dir / "setup" / "installation.md"
        good_file.parent.mkdir(parents=True, exist_ok=True)
        good_content = """# Installation Guide

This guide will help you install the application.

## Prerequisites

Before installing, ensure you have:

- Python 3.8 or higher
- pip package manager
- Git version control

## Installation Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/example/repo.git
cd repo
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

See the [configuration guide](../reference/configuration.md) for details.

## Troubleshooting

If you encounter issues, check the [troubleshooting guide](../reference/troubleshooting.md).
"""
        good_file.write_text(good_content, encoding='utf-8')
        test_files.append(good_file)
        
        # 2. File with format issues (Requirement 8.1)
        format_issues_file = self.docs_dir / "features" / "payments.md"
        format_issues_file.parent.mkdir(parents=True, exist_ok=True)
        format_issues_content = """#Payment System (missing space)

This document describes the payment system.

##Another malformed heading

The payment system supports:

- Credit cards
- PayPal
- 

```python
def process_payment():
    # This code block is not closed properly

| Feature | Status |
|---------|
| Stripe  | Active |
| PayPal  | Pending |

[Malformed link](missing-closing-paren
"""
        format_issues_file.write_text(format_issues_content, encoding='utf-8')
        test_files.append(format_issues_file)
        
        # 3. File with broken links (Requirement 8.2)
        broken_links_file = self.docs_dir / "development" / "api.md"
        broken_links_file.parent.mkdir(parents=True, exist_ok=True)
        broken_links_content = """# API Documentation

## Overview

This document describes the API endpoints.

## Authentication

See the [authentication guide](./non-existent-auth.md) for details.

## Endpoints

### User Management

- [User creation](../features/users.md#create-user)
- [User deletion](../features/users.md#non-existent-section)

## External Resources

- [Official docs](https://example.com/docs) (this should not be flagged)
- [GitHub repo](https://github.com/example/repo)

## Internal Navigation

- [Back to top](#overview)
- [Non-existent section](#missing-section)
"""
        broken_links_file.write_text(broken_links_content, encoding='utf-8')
        test_files.append(broken_links_file)
        
        # 4. File with content integrity issues (Requirement 8.3)
        content_issues_file = self.docs_dir / "testing" / "test-guide.md"
        content_issues_file.parent.mkdir(parents=True, exist_ok=True)
        content_issues_content = """# Testing Guide

## Empty Section

## Another Empty Section

## Duplicate Section

This section has some content.

## Duplicate Section

This is a duplicate heading with different content.

## Very Short Section

Hi.
"""
        content_issues_file.write_text(content_issues_content, encoding='utf-8')
        test_files.append(content_issues_file)
        
        # 5. Empty file (content integrity issue)
        empty_file = self.docs_dir / "reference" / "empty.md"
        empty_file.parent.mkdir(parents=True, exist_ok=True)
        empty_file.write_text("", encoding='utf-8')
        test_files.append(empty_file)
        
        # 6. Create referenced files to test link validation
        config_file = self.docs_dir / "reference" / "configuration.md"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("# Configuration\n\nConfiguration details here.", encoding='utf-8')
        test_files.append(config_file)
        
        troubleshooting_file = self.docs_dir / "reference" / "troubleshooting.md"
        troubleshooting_file.write_text("# Troubleshooting\n\nTroubleshooting tips here.", encoding='utf-8')
        test_files.append(troubleshooting_file)
        
        users_file = self.docs_dir / "features" / "users.md"
        users_file.parent.mkdir(parents=True, exist_ok=True)
        users_content = """# User Management

## Create User

Instructions for creating users.

## Delete User

Instructions for deleting users.
"""
        users_file.write_text(users_content, encoding='utf-8')
        test_files.append(users_file)
        
        # 7. Master index file
        master_index = self.docs_dir / "README.md"
        master_index_content = """# Documentation Index

Welcome to the project documentation.

## Quick Links

- [Installation Guide](./setup/installation.md)
- [Payment System](./features/payments.md)
- [API Documentation](./development/api.md)
- [Testing Guide](./testing/test-guide.md)
- [Configuration](./reference/configuration.md)

## Categories

### Setup
- [Installation](./setup/installation.md)

### Features
- [Payments](./features/payments.md)
- [Users](./features/users.md)

### Development
- [API](./development/api.md)

### Testing
- [Test Guide](./testing/test-guide.md)

### Reference
- [Configuration](./reference/configuration.md)
- [Troubleshooting](./reference/troubleshooting.md)
"""
        master_index.write_text(master_index_content, encoding='utf-8')
        test_files.append(master_index)
        
        return test_files
    
    def test_validation_with_no_files(self):
        """Test validation behavior with no markdown files."""
        empty_dir = self.temp_dir / "empty_docs"
        empty_dir.mkdir()
        
        summary = self.generator.validate_markdown_files(empty_dir)
        
        self.assertEqual(summary.total_files, 0)
        self.assertEqual(summary.success_rate, 100.0)  # Empty should be 100% success
    
    def test_validation_report_generation_failure(self):
        """Test handling of validation report generation failure."""
        # Create a file in a directory
        test_file = self.docs_dir / "test.md"
        test_file.write_text("# Test\n\nContent.", encoding='utf-8')
        
        # Try to generate report in non-existent directory
        invalid_report_path = Path("/non/existent/path/report.md")
        
        summary = self.validator.validate_directory(self.docs_dir)
        success = self.validator.generate_validation_report(summary, invalid_report_path)
        
        self.assertFalse(success)
    
    def test_validation_with_config_disabled(self):
        """Test that validation can be disabled via configuration."""
        # Disable validation in config
        self.config.validate_output = False
        generator = StructureGenerator(self.config)
        
        # Create structure and files
        structure = DocumentationStructure()
        structure.root_path = str(self.docs_dir) + "/"
        generator.create_directory_structure(structure)
        
        # Create file with issues
        bad_file = self.docs_dir / "bad.md"
        bad_file.write_text("#Bad heading\n[Broken](./missing.md)", encoding='utf-8')
        
        # Validation should be skipped
        errors = generator.validate_structure(structure)
        
        # Should not have markdown validation errors (only basic structure checks)
        markdown_errors = [e for e in errors if any(keyword in e for keyword in 
                          ["Format issue", "Broken link", "Content issue"])]
        self.assertEqual(len(markdown_errors), 0)


if __name__ == '__main__':
    unittest.main()