#!/usr/bin/env python3
"""
Comprehensive test for the complete file analysis functionality (Task 3).

This test validates that the file analysis system works correctly end-to-end,
including file discovery, classification, metadata extraction, and consolidation
group identification.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import our modules
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from doc_consolidation.analyzer import ContentAnalyzer
from doc_consolidation.config import ConsolidationConfig
from doc_consolidation.models import Category, ContentType, Priority


class TestComprehensiveAnalysis(unittest.TestCase):
    """Comprehensive test for file analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = ConsolidationConfig()
        self.config.source_directory = self.temp_dir
        self.analyzer = ContentAnalyzer(self.config)
        
        # Create realistic test files with content
        self.test_files = {
            "TASK_1_AUTH_COMPLETE.md": """# Task 1: Authentication System Complete

**Author**: Development Team
**Date**: 2024-01-15

## Summary

The authentication system has been successfully implemented with the following features:

- JWT token-based authentication
- User registration and login
- Password reset functionality
- Session management

## Implementation Details

### Components Implemented

1. **User Model**: Extended Django's User model
2. **Authentication Views**: Login, logout, register views
3. **JWT Integration**: Token generation and validation
4. **Middleware**: Authentication middleware for protected routes

### Testing

All authentication tests are passing:
- Unit tests: 15/15 passed
- Integration tests: 8/8 passed
- Security tests: 5/5 passed

## Next Steps

- Implement OAuth integration
- Add two-factor authentication
- Performance optimization

[Link to auth documentation](AUTH_SYSTEM_GUIDE.md)
""",
            
            "PAYMENT_STRIPE_INTEGRATION.md": """# Payment System - Stripe Integration

This document describes the Stripe payment integration for the tournament platform.

## Overview

The payment system handles:
- Tournament entry fees
- Subscription payments
- Refund processing
- Webhook handling

## Configuration

```python
STRIPE_PUBLISHABLE_KEY = "pk_test_..."
STRIPE_SECRET_KEY = "sk_test_..."
STRIPE_WEBHOOK_SECRET = "whsec_..."
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/payments/create/` | POST | Create payment intent |
| `/api/payments/confirm/` | POST | Confirm payment |
| `/api/payments/refund/` | POST | Process refund |

## Webhook Events

The system handles these Stripe webhook events:
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `invoice.payment_succeeded`

![Payment Flow](payment_flow.png)

## Testing

Use Stripe's test cards for testing:
- Success: 4242424242424242
- Decline: 4000000000000002
""",
            
            "DATABASE_SETUP.md": """# Database Setup Guide

## Prerequisites

- PostgreSQL 13+
- Redis 6+
- Python 3.9+

## Installation Steps

1. Install PostgreSQL
2. Create database
3. Configure settings
4. Run migrations

## Configuration

```bash
# .env file
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
```

## Troubleshooting

Common issues and solutions...
""",
            
            "test_payment_integration.md": """# Payment Integration Test Results

**Test Date**: 2024-01-20
**Test Environment**: Staging

## Test Summary

- Total Tests: 25
- Passed: 23
- Failed: 2
- Coverage: 92%

## Failed Tests

1. `test_refund_processing` - Timeout issue
2. `test_webhook_validation` - Signature mismatch

## Performance Metrics

- Average response time: 150ms
- Peak load handled: 1000 concurrent requests
- Memory usage: 256MB

## Recommendations

- Fix timeout in refund processing
- Update webhook signature validation
""",
            
            "QUICK_START_GUIDE.md": """# Quick Start Guide

Get up and running in 5 minutes!

## 1. Clone Repository
```bash
git clone https://github.com/project/repo.git
```

## 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

## 4. Run Migrations
```bash
python manage.py migrate
```

## 5. Start Server
```bash
python manage.py runserver
```

That's it! Visit http://localhost:8000
""",
            
            "DEVELOPER_INTEGRATION.md": """# Developer Integration Guide

## API Documentation

### Authentication
All API requests require authentication via JWT token.

### Rate Limiting
- 1000 requests per hour for authenticated users
- 100 requests per hour for anonymous users

### Error Handling
Standard HTTP status codes are used.

## SDK Integration

### Python SDK
```python
from tournament_api import TournamentClient

client = TournamentClient(api_key="your_key")
tournaments = client.tournaments.list()
```

### JavaScript SDK
```javascript
import { TournamentAPI } from 'tournament-js-sdk';

const api = new TournamentAPI('your_key');
const tournaments = await api.tournaments.list();
```

## Webhooks

Configure webhooks to receive real-time updates.
""",
            
            "old_migration_notes.md": """# Old Migration Notes (Deprecated)

These are old migration notes from 2022. 
This information is outdated and should not be used.

Use the new migration guide instead.
""",
            
            "README.md": """# Tournament Platform

A comprehensive tournament management system.

## Features
- User management
- Tournament creation
- Payment processing
- Real-time updates

## Quick Links
- [Setup Guide](DATABASE_SETUP.md)
- [API Documentation](DEVELOPER_INTEGRATION.md)
- [Payment Integration](PAYMENT_STRIPE_INTEGRATION.md)
"""
        }
        
        # Create the test files
        for filename, content in self.test_files.items():
            file_path = Path(self.temp_dir) / filename
            file_path.write_text(content, encoding='utf-8')
    
    def test_complete_file_discovery(self):
        """Test complete file discovery process."""
        print("\n=== Testing File Discovery ===")
        
        # Discover files
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        
        # Validate discovery
        self.assertEqual(len(discovered_files), len(self.test_files))
        
        discovered_names = [f.name for f in discovered_files]
        for expected_file in self.test_files.keys():
            self.assertIn(expected_file, discovered_names)
        
        print(f"✓ Discovered {len(discovered_files)} files correctly")
    
    def test_complete_file_analysis(self):
        """Test complete file analysis process."""
        print("\n=== Testing File Analysis ===")
        
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = []
        
        for file_path in discovered_files:
            analysis = self.analyzer.analyze_file(file_path)
            analyses.append(analysis)
            
            # Validate analysis structure
            self.assertIsNotNone(analysis.category)
            self.assertIsNotNone(analysis.content_type)
            self.assertIsNotNone(analysis.preservation_priority)
            self.assertGreaterEqual(analysis.confidence_score, 0.0)
            self.assertLessEqual(analysis.confidence_score, 1.0)
            
            print(f"✓ {analysis.filename}: {analysis.category.value} "
                  f"(confidence: {analysis.confidence_score:.2f})")
        
        # Validate specific classifications
        analysis_by_name = {a.filename: a for a in analyses}
        
        # Check completion file
        task_analysis = analysis_by_name["TASK_1_AUTH_COMPLETE.md"]
        self.assertEqual(task_analysis.category, Category.IMPLEMENTATION_COMPLETION)
        self.assertEqual(task_analysis.content_type, ContentType.COMPLETION_SUMMARY)
        self.assertGreater(task_analysis.confidence_score, 0.8)
        
        # Check feature file
        payment_analysis = analysis_by_name["PAYMENT_STRIPE_INTEGRATION.md"]
        self.assertEqual(payment_analysis.category, Category.FEATURE_DOCS)
        self.assertEqual(payment_analysis.content_type, ContentType.FEATURE_GUIDE)
        
        # Check setup file
        setup_analysis = analysis_by_name["DATABASE_SETUP.md"]
        self.assertEqual(setup_analysis.category, Category.SETUP_CONFIG)
        self.assertEqual(setup_analysis.content_type, ContentType.SETUP_PROCEDURE)
        
        # Check test file
        test_analysis = analysis_by_name["test_payment_integration.md"]
        self.assertEqual(test_analysis.category, Category.TESTING_VALIDATION)
        self.assertEqual(test_analysis.content_type, ContentType.TEST_REPORT)
        
        # Check quick reference
        quick_analysis = analysis_by_name["QUICK_START_GUIDE.md"]
        self.assertEqual(quick_analysis.category, Category.QUICK_REFERENCES)
        self.assertEqual(quick_analysis.content_type, ContentType.QUICK_REFERENCE)
        
        # Check integration guide
        dev_analysis = analysis_by_name["DEVELOPER_INTEGRATION.md"]
        self.assertEqual(dev_analysis.category, Category.INTEGRATION_GUIDES)
        self.assertEqual(dev_analysis.content_type, ContentType.INTEGRATION_GUIDE)
        
        print(f"✓ All {len(analyses)} files analyzed correctly")
        return analyses
    
    def test_metadata_extraction(self):
        """Test metadata extraction functionality."""
        print("\n=== Testing Metadata Extraction ===")
        
        # Test with the payment file (has rich content)
        payment_file = Path(self.temp_dir) / "PAYMENT_STRIPE_INTEGRATION.md"
        analysis = self.analyzer.analyze_file(payment_file)
        metadata = analysis.metadata
        
        # Check basic metadata
        self.assertGreater(metadata.word_count, 0)
        self.assertGreater(len(metadata.headings), 0)
        self.assertGreater(metadata.code_blocks, 0)
        self.assertTrue(metadata.has_tables)
        self.assertTrue(metadata.has_images)
        
        # Check links
        self.assertGreater(len(metadata.internal_links), 0)
        
        # Check key topics
        self.assertGreater(len(metadata.key_topics), 0)
        
        print(f"✓ Metadata extracted: {metadata.word_count} words, "
              f"{len(metadata.headings)} headings, {metadata.code_blocks} code blocks")
        
        # Test with completion file (has author and date)
        task_file = Path(self.temp_dir) / "TASK_1_AUTH_COMPLETE.md"
        task_analysis = self.analyzer.analyze_file(task_file)
        task_metadata = task_analysis.metadata
        
        # Should extract author and date
        self.assertIsNotNone(task_metadata.author)
        self.assertIsNotNone(task_metadata.creation_date)
        
        print(f"✓ Author extracted: {task_metadata.author}")
        print(f"✓ Date extracted: {task_metadata.creation_date}")
    
    def test_consolidation_group_identification(self):
        """Test consolidation group identification."""
        print("\n=== Testing Consolidation Group Identification ===")
        
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = [self.analyzer.analyze_file(f) for f in discovered_files]
        
        # Identify consolidation groups
        groups = self.analyzer.identify_consolidation_candidates(analyses)
        
        print(f"✓ Identified {len(groups)} consolidation groups:")
        
        for group in groups:
            print(f"  - {group.group_id}: {group.primary_file} + "
                  f"{len(group.related_files)} related files")
            print(f"    Strategy: {group.consolidation_strategy.value}")
            print(f"    Output: {group.output_filename}")
        
        # Should have at least some groups (depends on test data)
        # For our test data, we might not have enough similar files to group
        # but the function should run without errors
        self.assertIsInstance(groups, list)
    
    def test_validation_functionality(self):
        """Test file validation functionality."""
        print("\n=== Testing File Validation ===")
        
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        
        # Test file validation
        validation_results = self.analyzer.validate_discovered_files(discovered_files)
        
        # All our test files should be valid
        self.assertEqual(len(validation_results['valid_files']), len(self.test_files))
        self.assertEqual(len(validation_results['missing_files']), 0)
        self.assertEqual(len(validation_results['permission_errors']), 0)
        self.assertEqual(len(validation_results['binary_files']), 0)
        
        print(f"✓ Validated {len(validation_results['valid_files'])} files successfully")
        
        # Test analysis validation
        for file_path in discovered_files:
            analysis = self.analyzer.analyze_file(file_path)
            errors = self.analyzer.validate_analysis(analysis)
            self.assertEqual(len(errors), 0, f"Analysis validation failed for {file_path}: {errors}")
        
        print("✓ All analysis results validated successfully")
    
    def test_error_handling(self):
        """Test error handling for edge cases."""
        print("\n=== Testing Error Handling ===")
        
        # Test with non-existent file
        non_existent = Path(self.temp_dir) / "non_existent.md"
        analysis = self.analyzer.analyze_file(non_existent)
        
        # Should return a valid analysis with error notes
        self.assertEqual(analysis.category, Category.UNCATEGORIZED)
        self.assertEqual(analysis.confidence_score, 0.0)
        self.assertGreater(len(analysis.processing_notes), 0)
        
        print("✓ Non-existent file handled gracefully")
        
        # Test with empty file
        empty_file = Path(self.temp_dir) / "empty.md"
        empty_file.write_text("", encoding='utf-8')
        
        empty_analysis = self.analyzer.analyze_file(empty_file)
        self.assertIsNotNone(empty_analysis)
        self.assertEqual(empty_analysis.metadata.word_count, 0)
        
        print("✓ Empty file handled gracefully")
        
        # Test with malformed content
        malformed_file = Path(self.temp_dir) / "malformed.md"
        malformed_file.write_text("# Heading\n\n```\nUnclosed code block\n", encoding='utf-8')
        
        malformed_analysis = self.analyzer.analyze_file(malformed_file)
        self.assertIsNotNone(malformed_analysis)
        
        print("✓ Malformed content handled gracefully")
    
    def test_performance_characteristics(self):
        """Test performance characteristics of the analysis."""
        print("\n=== Testing Performance Characteristics ===")
        
        start_time = datetime.now()
        
        # Analyze all files
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = [self.analyzer.analyze_file(f) for f in discovered_files]
        groups = self.analyzer.identify_consolidation_candidates(analyses)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete reasonably quickly
        self.assertLess(duration, 5.0, "Analysis took too long")
        
        files_per_second = len(discovered_files) / duration if duration > 0 else float('inf')
        
        print(f"✓ Analyzed {len(discovered_files)} files in {duration:.2f} seconds")
        print(f"✓ Performance: {files_per_second:.1f} files/second")
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        print("Comprehensive File Analysis Test Suite")
        print("=" * 50)
        
        try:
            self.test_complete_file_discovery()
            analyses = self.test_complete_file_analysis()
            self.test_metadata_extraction()
            self.test_consolidation_group_identification()
            self.test_validation_functionality()
            self.test_error_handling()
            self.test_performance_characteristics()
            
            print("\n" + "=" * 50)
            print("✅ ALL TESTS PASSED - File analysis system is working correctly!")
            print("✅ The system successfully:")
            print("   - Discovers markdown files")
            print("   - Classifies files by category and content type")
            print("   - Extracts comprehensive metadata")
            print("   - Identifies consolidation opportunities")
            print("   - Handles errors gracefully")
            print("   - Performs efficiently")
            
            return True
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Run the comprehensive test suite."""
    test_suite = TestComprehensiveAnalysis()
    test_suite.setUp()
    
    try:
        success = test_suite.run_all_tests()
        return 0 if success else 1
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_suite.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())