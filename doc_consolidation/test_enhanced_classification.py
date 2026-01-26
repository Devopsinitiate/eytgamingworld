#!/usr/bin/env python3
"""
Comprehensive test for enhanced pattern-based file classification (Task 2.2).

This test demonstrates the enhanced classification system working with
realistic file scenarios and edge cases.
"""

import sys
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import our modules
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from doc_consolidation.analyzer import ContentAnalyzer
from doc_consolidation.config import ConsolidationConfig
from doc_consolidation.models import Category


def test_realistic_file_scenarios():
    """Test classification with realistic file scenarios."""
    print("Testing realistic file scenarios...")
    
    config = ConsolidationConfig()
    analyzer = ContentAnalyzer(config)
    
    # Realistic file scenarios from a Django project
    realistic_files = [
        # Completion files (Task 2.2 requirement)
        ("TASK_1_AUTHENTICATION_COMPLETE.md", Category.IMPLEMENTATION_COMPLETION),
        ("TASK_2_PAYMENT_INTEGRATION_COMPLETE.md", Category.IMPLEMENTATION_COMPLETION),
        ("PHASE_1_SETUP_COMPLETE.md", Category.IMPLEMENTATION_COMPLETION),
        ("MILESTONE_BETA_COMPLETE.md", Category.IMPLEMENTATION_COMPLETION),
        
        # Feature documentation (Task 2.2 requirement)
        ("PAYMENT_STRIPE_INTEGRATION.md", Category.FEATURE_DOCS),
        ("PAYMENT_WEBHOOK_SETUP.md", Category.FEATURE_DOCS),
        ("TOURNAMENT_BRACKET_SYSTEM.md", Category.FEATURE_DOCS),
        ("TOURNAMENT_SCORING_LOGIC.md", Category.FEATURE_DOCS),
        ("AUTHENTICATION_JWT_FLOW.md", Category.FEATURE_DOCS),
        ("NOTIFICATION_EMAIL_SYSTEM.md", Category.FEATURE_DOCS),
        
        # Setup and configuration (Task 2.2 requirement)
        ("DATABASE_SETUP.md", Category.SETUP_CONFIG),
        ("REDIS_CACHE_SETUP.md", Category.SETUP_CONFIG),
        ("DOCKER_ENVIRONMENT_SETUP.md", Category.SETUP_CONFIG),
        ("PRODUCTION_DEPLOYMENT_SETUP.md", Category.SETUP_CONFIG),
        
        # Testing documentation (Task 2.2 requirement)
        ("test_payment_integration.md", Category.TESTING_VALIDATION),
        ("TESTING_STRATEGY.md", Category.TESTING_VALIDATION),
        ("PERFORMANCE_BENCHMARK_RESULTS.md", Category.TESTING_VALIDATION),
        ("QA_REGRESSION_TESTS.md", Category.TESTING_VALIDATION),
        
        # Quick references
        ("QUICK_START_GUIDE.md", Category.QUICK_REFERENCES),
        ("API_REFERENCE.md", Category.QUICK_REFERENCES),
        
        # Integration guides
        ("THIRD_PARTY_INTEGRATION.md", Category.INTEGRATION_GUIDES),
        ("DEVELOPER_ONBOARDING.md", Category.INTEGRATION_GUIDES),
    ]
    
    passed = 0
    total = len(realistic_files)
    
    for filename, expected_category in realistic_files:
        category, confidence = analyzer.classify_by_pattern(filename)
        status = "✓" if category == expected_category else "✗"
        print(f"  {status} {filename}")
        print(f"    -> {category.name} (confidence: {confidence:.2f})")
        
        if category != expected_category:
            print(f"    Expected: {expected_category.name}")
        else:
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} files classified correctly ({passed/total*100:.1f}%)")
    return passed == total


def test_edge_cases():
    """Test edge cases and ambiguous files."""
    print("\nTesting edge cases...")
    
    config = ConsolidationConfig()
    analyzer = ContentAnalyzer(config)
    
    edge_cases = [
        # Files that could match multiple categories
        ("PAYMENT_TEST_SETUP.md", "Should prioritize feature over test/setup"),
        ("TOURNAMENT_TESTING_GUIDE.md", "Should prioritize feature over testing"),
        ("AUTH_SETUP_COMPLETE.md", "Should prioritize completion over feature/setup"),
        
        # Files with unusual naming
        ("payment-integration.md", "Lowercase with dashes"),
        ("PAYMENT_integration_GUIDE.md", "Mixed case"),
        ("payment_INTEGRATION.MD", "Different extension case"),
        
        # Very specific patterns
        ("TASK_42_USER_AUTH_COMPLETE.md", "Complex task completion"),
        ("PHASE_2_TOURNAMENT_SYSTEM_COMPLETE.md", "Complex phase completion"),
    ]
    
    for filename, description in edge_cases:
        category, confidence = analyzer.classify_by_pattern(filename)
        print(f"  {filename}")
        print(f"    -> {category.name} (confidence: {confidence:.2f})")
        print(f"    Note: {description}")
        print()


def test_consolidation_grouping():
    """Test that related files are properly grouped for consolidation."""
    print("\nTesting consolidation grouping...")
    
    config = ConsolidationConfig()
    analyzer = ContentAnalyzer(config)
    
    # Create temporary files for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        test_files = [
            "TASK_1_AUTH_COMPLETE.md",
            "TASK_2_PAYMENT_COMPLETE.md", 
            "TASK_3_TOURNAMENT_COMPLETE.md",
            "PAYMENT_STRIPE_SETUP.md",
            "PAYMENT_WEBHOOK_CONFIG.md",
            "PAYMENT_TESTING_GUIDE.md",
            "TOURNAMENT_BRACKET_LOGIC.md",
            "TOURNAMENT_SCORING_SYSTEM.md",
        ]
        
        # Create actual files with minimal content
        file_analyses = []
        for filename in test_files:
            file_path = temp_path / filename
            file_path.write_text(f"# {filename}\n\nTest content for {filename}")
            
            analysis = analyzer.analyze_file(file_path)
            file_analyses.append(analysis)
        
        # Test consolidation group identification
        consolidation_groups = analyzer.identify_consolidation_candidates(file_analyses)
        
        print(f"  Created {len(file_analyses)} test files")
        print(f"  Identified {len(consolidation_groups)} consolidation groups:")
        
        for group in consolidation_groups:
            print(f"    Group: {group.group_id}")
            print(f"      Category: {group.category.name}")
            print(f"      Primary: {group.primary_file}")
            print(f"      Related: {group.related_files}")
            print(f"      Strategy: {group.consolidation_strategy.name}")
            print(f"      Output: {group.output_filename}")
            print()


def main():
    """Run all enhanced classification tests."""
    print("Enhanced Pattern-Based File Classification - Comprehensive Tests")
    print("=" * 70)
    
    success = True
    
    # Test realistic scenarios
    if not test_realistic_file_scenarios():
        success = False
    
    # Test edge cases
    test_edge_cases()
    
    # Test consolidation grouping
    test_consolidation_grouping()
    
    print("=" * 70)
    if success:
        print("✓ All comprehensive tests completed successfully!")
        print("✓ Enhanced pattern-based classification is working correctly.")
    else:
        print("✗ Some tests failed. Please review the results above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)