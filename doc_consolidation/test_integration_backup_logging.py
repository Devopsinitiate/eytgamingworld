"""
Integration test for backup and migration logging with consolidation functionality.

This test verifies that the enhanced backup and migration logging works correctly
with the existing consolidation engine functionality.
"""

import tempfile
import unittest
from pathlib import Path

from .config import ConsolidationConfig
from .engine import ConsolidationEngine
from .models import (
    MigrationLog, FileAnalysis, ConsolidationGroup, Category, ContentType, 
    Priority, ContentMetadata, ConsolidationStrategy
)


class TestIntegrationBackupLogging(unittest.TestCase):
    """Integration test for backup and migration logging."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = ConsolidationConfig()
        self.config.create_backups = True
        self.engine = ConsolidationEngine(self.config)
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test files with realistic content
        self.test_files = {}
        
        # Create completion summary files
        completion_content = """# Task 1 Completion Summary

## Overview
This task involved implementing user authentication functionality.

## Key Achievements
- Implemented login/logout functionality
- Added password reset capability
- Created user registration system

## Technical Details
- Used Django's built-in authentication
- Added custom user model
- Implemented OAuth integration

## Testing
- Unit tests: 15 tests passing
- Integration tests: 8 tests passing
- Manual testing completed

## Completion Date
2024-01-15
"""
        
        completion_file = self.temp_path / "TASK_1_COMPLETE.md"
        completion_file.write_text(completion_content, encoding='utf-8')
        self.test_files['completion'] = str(completion_file)
        
        # Create feature documentation
        feature_content = """# Payment System Documentation

## Overview
The payment system handles all financial transactions in the application.

## Features
- Credit card processing
- Subscription management
- Invoice generation
- Payment history

## Integration
- Stripe API integration
- PayPal support
- Bank transfer capability

## Security
- PCI compliance
- Encrypted data storage
- Secure API endpoints
"""
        
        feature_file = self.temp_path / "PAYMENT_SYSTEM.md"
        feature_file.write_text(feature_content, encoding='utf-8')
        self.test_files['feature'] = str(feature_file)
        
        # Create setup guide
        setup_content = """# Setup Guide

## Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+

## Installation Steps
1. Clone the repository
2. Install dependencies
3. Configure database
4. Run migrations
5. Start the server

## Configuration
- Environment variables
- Database settings
- Cache configuration
"""
        
        setup_file = self.temp_path / "SETUP_GUIDE.md"
        setup_file.write_text(setup_content, encoding='utf-8')
        self.test_files['setup'] = str(setup_file)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_consolidation_with_backup_and_logging(self):
        """Test complete consolidation workflow with backup and migration logging."""
        migration_log = MigrationLog()
        
        # Step 1: Create backups
        backup_dir = self.temp_path / "backups"
        source_files = list(self.test_files.values())
        
        success, backup_path = self.engine.create_backup(
            source_files,
            str(backup_dir),
            migration_log
        )
        
        self.assertTrue(success)
        self.assertTrue(backup_path)
        
        # Step 2: Create file analyses (simulated)
        file_analyses = {}
        
        for file_type, file_path in self.test_files.items():
            path_obj = Path(file_path)
            metadata = ContentMetadata(
                word_count=len(path_obj.read_text().split()),
                key_topics=[file_type, 'documentation', 'system'],
                headings=['Overview', 'Features', 'Integration']
            )
            
            if file_type == 'completion':
                category = Category.IMPLEMENTATION_COMPLETION
                content_type = ContentType.COMPLETION_SUMMARY
            elif file_type == 'feature':
                category = Category.FEATURE_DOCS
                content_type = ContentType.FEATURE_GUIDE
            else:
                category = Category.SETUP_CONFIG
                content_type = ContentType.SETUP_PROCEDURE
            
            analysis = FileAnalysis(
                filepath=path_obj,
                filename=path_obj.name,
                category=category,
                content_type=content_type,
                metadata=metadata,
                preservation_priority=Priority.HIGH
            )
            
            file_analyses[path_obj.name] = analysis
        
        # Step 3: Create consolidation groups
        completion_group = ConsolidationGroup(
            group_id="completion_summaries",
            category=Category.IMPLEMENTATION_COMPLETION,
            primary_file="TASK_1_COMPLETE.md",
            consolidation_strategy=ConsolidationStrategy.COMBINE_SUMMARIES,
            output_filename="consolidated_completions.md"
        )
        
        feature_group = ConsolidationGroup(
            group_id="feature_docs",
            category=Category.FEATURE_DOCS,
            primary_file="PAYMENT_SYSTEM.md",
            consolidation_strategy=ConsolidationStrategy.MERGE_TOPICAL,
            output_filename="consolidated_features.md"
        )
        
        # Step 4: Perform consolidation with logging
        consolidated_files = {}
        operations_to_log = []
        
        # Consolidate completion summaries
        completion_content = self.engine.consolidate_group(completion_group, file_analyses)
        if completion_content:
            consolidated_files[completion_group.output_filename] = completion_content
            
            # Prepare operation for logging
            operations_to_log.append({
                'type': 'file_consolidation',
                'source': completion_group.primary_file,
                'destination': completion_group.output_filename,
                'details': f"Strategy: {completion_group.consolidation_strategy.value}"
            })
        
        # Consolidate feature documentation
        feature_content = self.engine.consolidate_group(feature_group, file_analyses)
        if feature_content:
            consolidated_files[feature_group.output_filename] = feature_content
            
            # Prepare operation for logging
            operations_to_log.append({
                'type': 'file_consolidation',
                'source': feature_group.primary_file,
                'destination': feature_group.output_filename,
                'details': f"Strategy: {feature_group.consolidation_strategy.value}"
            })
        
        # Log all consolidation operations
        if operations_to_log:
            self.engine.log_operations(operations_to_log, migration_log)
        
        # Step 5: Track file transformations
        self.engine.track_file_transformations(
            source_files,
            consolidated_files,
            migration_log
        )
        
        # Step 6: Verify backup integrity
        verification_success, verification_issues = self.engine.verify_backup_integrity(
            backup_path,
            migration_log
        )
        
        self.assertTrue(verification_success)
        self.assertEqual(len(verification_issues), 0)
        
        # Step 7: Create comprehensive migration log
        log_file = self.temp_path / "migration_log.md"
        log_success = self.engine.create_comprehensive_migration_log(
            migration_log,
            str(log_file)
        )
        
        self.assertTrue(log_success)
        self.assertTrue(log_file.exists())
        
        # Verify the migration log content
        log_content = log_file.read_text(encoding='utf-8')
        
        # Check that all major sections are present
        self.assertIn("# Documentation Consolidation Migration Log", log_content)
        self.assertIn("## Executive Summary", log_content)
        self.assertIn("## Operation Timeline", log_content)
        self.assertIn("## File Movements and Transformations", log_content)
        self.assertIn("## Verification and Integrity", log_content)
        
        # Check that operations were logged
        self.assertIn("file_consolidation", log_content)
        self.assertIn("file_transformation", log_content)
        self.assertIn("backup_verification", log_content)
        
        # Check that file names appear in the log
        self.assertIn("TASK_1_COMPLETE.md", log_content)
        self.assertIn("PAYMENT_SYSTEM.md", log_content)
        self.assertIn("consolidated_completions.md", log_content)
        self.assertIn("consolidated_features.md", log_content)
        
        # Verify consolidated content was created
        self.assertEqual(len(consolidated_files), 2)
        self.assertIn("consolidated_completions.md", consolidated_files)
        self.assertIn("consolidated_features.md", consolidated_files)
        
        # Check that consolidated content contains expected information
        completion_consolidated = consolidated_files["consolidated_completions.md"]
        self.assertIn("TASK 1 COMPLETE", completion_consolidated)
        self.assertIn("login/logout functionality", completion_consolidated)
        self.assertIn("Key Points", completion_consolidated)
        
        feature_consolidated = consolidated_files["consolidated_features.md"]
        self.assertIn("Payment System", feature_consolidated)
        self.assertIn("Credit card processing", feature_consolidated)
        self.assertIn("Stripe API", feature_consolidated)
        
        # Verify migration log statistics
        self.assertGreater(migration_log.files_processed, 0)
        self.assertGreater(len(migration_log.operations), 5)  # Should have multiple operations
        
        # Check for specific operation types
        operation_types = [op.get('type', '') for op in migration_log.operations]
        self.assertIn('file_backup', operation_types)
        self.assertIn('backup_completed', operation_types)
        self.assertIn('file_consolidation', operation_types)
        self.assertIn('file_transformation', operation_types)
        self.assertIn('backup_verification', operation_types)
        
        print(f"✅ Integration test completed successfully!")
        print(f"   - Backed up {len(source_files)} source files")
        print(f"   - Created {len(consolidated_files)} consolidated files")
        print(f"   - Logged {len(migration_log.operations)} operations")
        print(f"   - Migration log: {log_file}")
        print(f"   - Backup location: {backup_path}")


if __name__ == '__main__':
    unittest.main()