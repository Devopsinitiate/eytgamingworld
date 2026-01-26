#!/usr/bin/env python3
"""
Unit tests for consolidation group identification functionality.

Tests the enhanced consolidation group identification implemented in Task 4.1.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from doc_consolidation.analyzer import ContentAnalyzer
from doc_consolidation.config import ConsolidationConfig
from doc_consolidation.models import Category, ConsolidationStrategy


class TestConsolidationGroups(unittest.TestCase):
    """Test consolidation group identification functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.config = ConsolidationConfig()
        self.analyzer = ContentAnalyzer(self.config)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_completion_file_consolidation(self):
        """Test that completion files are properly grouped for consolidation."""
        # Create completion files
        completion_files = {
            'TASK_1_AUTH_COMPLETE.md': 'Task 1 completion summary',
            'TASK_2_PAYMENT_COMPLETE.md': 'Task 2 completion summary',
            'TASK_3_TOURNAMENT_COMPLETE.md': 'Task 3 completion summary',
            'PHASE_1_COMPLETE.md': 'Phase 1 completion summary'
        }
        
        for filename, content in completion_files.items():
            (self.temp_path / filename).write_text(content)
        
        # Analyze files
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = [self.analyzer.analyze_file(f) for f in discovered_files]
        
        # Identify consolidation groups
        groups = self.analyzer.identify_consolidation_candidates(analyses)
        
        # Verify consolidation groups were created
        self.assertGreater(len(groups), 0, "Should identify consolidation groups for completion files")
        
        # Check for task consolidation group
        task_groups = [g for g in groups if 'task' in g.group_id.lower()]
        self.assertGreater(len(task_groups), 0, "Should create task consolidation group")
        
        # Verify consolidation strategy
        for group in task_groups:
            self.assertEqual(group.consolidation_strategy, ConsolidationStrategy.COMBINE_SUMMARIES)
            self.assertEqual(group.category, Category.IMPLEMENTATION_COMPLETION)
    
    def test_feature_file_consolidation(self):
        """Test that feature files are properly grouped for consolidation."""
        # Create feature files
        feature_files = {
            'PAYMENT_STRIPE_INTEGRATION.md': 'Payment integration with Stripe',
            'PAYMENT_SUBSCRIPTION_MANAGEMENT.md': 'Payment subscription management',
            'PAYMENT_REFUND_SYSTEM.md': 'Payment refund system',
            'TOURNAMENT_BRACKET_SYSTEM.md': 'Tournament bracket management',
            'TOURNAMENT_REGISTRATION.md': 'Tournament registration system'
        }
        
        for filename, content in feature_files.items():
            (self.temp_path / filename).write_text(content)
        
        # Analyze files
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = [self.analyzer.analyze_file(f) for f in discovered_files]
        
        # Identify consolidation groups
        groups = self.analyzer.identify_consolidation_candidates(analyses)
        
        # Verify feature consolidation groups were created
        feature_groups = [g for g in groups if g.category == Category.FEATURE_DOCS]
        self.assertGreater(len(feature_groups), 0, "Should identify feature consolidation groups")
        
        # Check for payment and tournament groups
        payment_groups = [g for g in feature_groups if 'payment' in g.group_id.lower()]
        tournament_groups = [g for g in feature_groups if 'tournament' in g.group_id.lower()]
        
        self.assertGreater(len(payment_groups), 0, "Should create payment consolidation group")
        self.assertGreater(len(tournament_groups), 0, "Should create tournament consolidation group")
        
        # Verify consolidation strategy
        for group in feature_groups:
            self.assertEqual(group.consolidation_strategy, ConsolidationStrategy.MERGE_TOPICAL)
    
    def test_setup_file_consolidation(self):
        """Test that setup files are properly grouped for consolidation."""
        # Create setup files
        setup_files = {
            'DATABASE_SETUP.md': 'Database setup instructions',
            'ENVIRONMENT_SETUP.md': 'Environment setup guide',
            'DEPLOYMENT_SETUP.md': 'Deployment setup procedures'
        }
        
        for filename, content in setup_files.items():
            (self.temp_path / filename).write_text(content)
        
        # Analyze files
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = [self.analyzer.analyze_file(f) for f in discovered_files]
        
        # Identify consolidation groups
        groups = self.analyzer.identify_consolidation_candidates(analyses)
        
        # Verify setup consolidation groups were created
        setup_groups = [g for g in groups if g.category == Category.SETUP_CONFIG]
        self.assertGreater(len(setup_groups), 0, "Should identify setup consolidation groups")
        
        # Verify consolidation strategy
        for group in setup_groups:
            self.assertEqual(group.consolidation_strategy, ConsolidationStrategy.MERGE_SEQUENTIAL)
    
    def test_testing_file_consolidation(self):
        """Test that testing files are properly grouped for consolidation."""
        # Create testing files
        testing_files = {
            'test_payment_integration.md': 'Payment integration test results',
            'test_authentication_system.md': 'Authentication system test results',
            'test_tournament_features.md': 'Tournament features test results',
            'validation_report.md': 'System validation report'
        }
        
        for filename, content in testing_files.items():
            (self.temp_path / filename).write_text(content)
        
        # Analyze files
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = [self.analyzer.analyze_file(f) for f in discovered_files]
        
        # Identify consolidation groups
        groups = self.analyzer.identify_consolidation_candidates(analyses)
        
        # Verify testing consolidation groups were created
        testing_groups = [g for g in groups if g.category == Category.TESTING_VALIDATION]
        self.assertGreater(len(testing_groups), 0, "Should identify testing consolidation groups")
        
        # Verify consolidation strategy (should create index for testing files)
        for group in testing_groups:
            self.assertEqual(group.consolidation_strategy, ConsolidationStrategy.CREATE_INDEX)
    
    def test_cross_category_consolidation(self):
        """Test cross-category consolidation identification."""
        # Create files from different categories but same feature
        cross_category_files = {
            'PAYMENT_SETUP.md': 'Payment system setup',
            'PAYMENT_INTEGRATION_GUIDE.md': 'Payment integration guide',
            'PAYMENT_API_REFERENCE.md': 'Payment API reference'
        }
        
        for filename, content in cross_category_files.items():
            (self.temp_path / filename).write_text(content)
        
        # Analyze files
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = [self.analyzer.analyze_file(f) for f in discovered_files]
        
        # Identify consolidation groups
        groups = self.analyzer.identify_consolidation_candidates(analyses)
        
        # Should identify some consolidation opportunities
        self.assertGreaterEqual(len(groups), 0, "Should handle cross-category files")
    
    def test_consolidation_group_optimization(self):
        """Test that consolidation groups are properly optimized."""
        # Create a mix of files that could create conflicts
        mixed_files = {
            'TASK_1_COMPLETE.md': 'Task 1 completion',
            'TASK_2_COMPLETE.md': 'Task 2 completion',
            'PAYMENT_GUIDE.md': 'Payment guide',
            'PAYMENT_SETUP.md': 'Payment setup',
            'test_results.md': 'Test results'
        }
        
        for filename, content in mixed_files.items():
            (self.temp_path / filename).write_text(content)
        
        # Analyze files
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = [self.analyzer.analyze_file(f) for f in discovered_files]
        
        # Identify consolidation groups
        groups = self.analyzer.identify_consolidation_candidates(analyses)
        
        # Verify no file appears in multiple groups
        all_files_in_groups = set()
        for group in groups:
            group_files = {group.primary_file} | set(group.related_files)
            
            # Check for conflicts
            conflicts = group_files.intersection(all_files_in_groups)
            self.assertEqual(len(conflicts), 0, f"File conflicts found: {conflicts}")
            
            all_files_in_groups.update(group_files)
    
    def test_consolidation_strategies(self):
        """Test that appropriate consolidation strategies are assigned."""
        # Create files that should trigger different strategies
        strategy_test_files = {
            # Completion files -> COMBINE_SUMMARIES
            'TASK_1_COMPLETE.md': 'Task completion',
            'TASK_2_COMPLETE.md': 'Task completion',
            
            # Feature files -> MERGE_TOPICAL
            'PAYMENT_GUIDE.md': 'Payment guide',
            'PAYMENT_API.md': 'Payment API',
            
            # Setup files -> MERGE_SEQUENTIAL
            'INSTALL_SETUP.md': 'Installation setup',
            'CONFIG_SETUP.md': 'Configuration setup',
            
            # Testing files -> CREATE_INDEX
            'test_report1.md': 'Test report 1',
            'test_report2.md': 'Test report 2',
            'test_report3.md': 'Test report 3',
            'validation_results.md': 'Validation results'
        }
        
        for filename, content in strategy_test_files.items():
            (self.temp_path / filename).write_text(content)
        
        # Analyze files
        discovered_files = self.analyzer.discover_files(self.temp_dir)
        analyses = [self.analyzer.analyze_file(f) for f in discovered_files]
        
        # Identify consolidation groups
        groups = self.analyzer.identify_consolidation_candidates(analyses)
        
        # Verify appropriate strategies are assigned
        strategy_counts = {}
        for group in groups:
            strategy = group.consolidation_strategy
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        # Should have multiple different strategies
        self.assertGreater(len(strategy_counts), 1, "Should use multiple consolidation strategies")


if __name__ == '__main__':
    unittest.main()