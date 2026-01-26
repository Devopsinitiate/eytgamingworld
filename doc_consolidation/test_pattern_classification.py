#!/usr/bin/env python3
"""
Test script for enhanced pattern-based file classification (Task 2.2).

This script tests the enhanced pattern matching functionality implemented
for the documentation consolidation system.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Now import with the package prefix
from doc_consolidation.analyzer import ContentAnalyzer
from doc_consolidation.config import ConsolidationConfig
from doc_consolidation.models import Category


def test_completion_file_patterns():
    """Test completion file pattern recognition (Task 2.2)."""
    print("Testing completion file patterns...")
    
    config = ConsolidationConfig()
    analyzer = ContentAnalyzer(config)
    
    test_files = [
        ("TASK_1_COMPLETE.md", Category.IMPLEMENTATION_COMPLETION),
        ("TASK_AUTH_COMPLETE.md", Category.IMPLEMENTATION_COMPLETION),
        ("PHASE_1_COMPLETE.md", Category.IMPLEMENTATION_COMPLETION),
        ("IMPLEMENTATION_COMPLETE.md", Category.IMPLEMENTATION_COMPLETION),
        ("PROJECT_SUMMARY.md", Category.IMPLEMENTATION_COMPLETION),
        ("Complete_Summary.md", Category.IMPLEMENTATION_COMPLETION),
        ("MILESTONE_1_COMPLETE.md", Category.IMPLEMENTATION_COMPLETION),
    ]
    
    for filename, expected_category in test_files:
        category, confidence = analyzer.classify_by_pattern(filename)
        status = "✓" if category == expected_category else "✗"
        print(f"  {status} {filename} -> {category.name} (confidence: {confidence:.2f})")
        
        if category != expected_category:
            print(f"    Expected: {expected_category.name}, Got: {category.name}")


def test_feature_documentation_patterns():
    """Test feature documentation pattern recognition (Task 2.2)."""
    print("\nTesting feature documentation patterns...")
    
    config = ConsolidationConfig()
    analyzer = ContentAnalyzer(config)
    
    test_files = [
        ("PAYMENT_INTEGRATION.md", Category.FEATURE_DOCS),
        ("PAYMENT_SETUP.md", Category.FEATURE_DOCS),
        ("TOURNAMENT_CREATION.md", Category.FEATURE_DOCS),
        ("TOURNAMENT_MANAGEMENT.md", Category.FEATURE_DOCS),
        ("AUTHENTICATION_FLOW.md", Category.FEATURE_DOCS),
        ("AUTH_SETUP.md", Category.FEATURE_DOCS),
        ("NOTIFICATION_SYSTEM.md", Category.FEATURE_DOCS),
        ("DASHBOARD_OVERVIEW.md", Category.FEATURE_DOCS),
        ("USER_PROFILE.md", Category.FEATURE_DOCS),
        ("TEAM_MANAGEMENT.md", Category.FEATURE_DOCS),
    ]
    
    for filename, expected_category in test_files:
        category, confidence = analyzer.classify_by_pattern(filename)
        status = "✓" if category == expected_category else "✗"
        print(f"  {status} {filename} -> {category.name} (confidence: {confidence:.2f})")
        
        if category != expected_category:
            print(f"    Expected: {expected_category.name}, Got: {category.name}")


def test_setup_configuration_patterns():
    """Test setup and configuration pattern recognition (Task 2.2)."""
    print("\nTesting setup and configuration patterns...")
    
    config = ConsolidationConfig()
    analyzer = ContentAnalyzer(config)
    
    test_files = [
        ("DATABASE_SETUP.md", Category.SETUP_CONFIG),
        ("REDIS_SETUP.md", Category.SETUP_CONFIG),
        ("ENVIRONMENT_SETUP.md", Category.SETUP_CONFIG),
        ("INSTALLATION_GUIDE.md", Category.SETUP_CONFIG),
        ("CONFIGURATION_MANUAL.md", Category.SETUP_CONFIG),
        ("DEPLOYMENT_SETUP.md", Category.SETUP_CONFIG),
        ("DOCKER_SETUP.md", Category.SETUP_CONFIG),
        ("REQUIREMENTS_SETUP.md", Category.SETUP_CONFIG),
    ]
    
    for filename, expected_category in test_files:
        category, confidence = analyzer.classify_by_pattern(filename)
        status = "✓" if category == expected_category else "✗"
        print(f"  {status} {filename} -> {category.name} (confidence: {confidence:.2f})")
        
        if category != expected_category:
            print(f"    Expected: {expected_category.name}, Got: {category.name}")


def test_testing_documentation_patterns():
    """Test testing documentation pattern recognition (Task 2.2)."""
    print("\nTesting testing documentation patterns...")
    
    config = ConsolidationConfig()
    analyzer = ContentAnalyzer(config)
    
    test_files = [
        ("test_authentication.md", Category.TESTING_VALIDATION),
        ("TESTING_GUIDE.md", Category.TESTING_VALIDATION),
        ("VALIDATION_REPORT.md", Category.TESTING_VALIDATION),
        ("COVERAGE_REPORT.md", Category.TESTING_VALIDATION),
        ("PERFORMANCE_TEST.md", Category.TESTING_VALIDATION),
        ("QA_CHECKLIST.md", Category.TESTING_VALIDATION),
        ("QUALITY_ASSURANCE.md", Category.TESTING_VALIDATION),
        ("BENCHMARK_RESULTS.md", Category.TESTING_VALIDATION),
    ]
    
    for filename, expected_category in test_files:
        category, confidence = analyzer.classify_by_pattern(filename)
        status = "✓" if category == expected_category else "✗"
        print(f"  {status} {filename} -> {category.name} (confidence: {confidence:.2f})")
        
        if category != expected_category:
            print(f"    Expected: {expected_category.name}, Got: {category.name}")


def test_confidence_scores():
    """Test that confidence scores are appropriate for different pattern types."""
    print("\nTesting confidence scores...")
    
    config = ConsolidationConfig()
    analyzer = ContentAnalyzer(config)
    
    # High confidence patterns (specific prefixes)
    high_confidence_files = [
        "TASK_1_COMPLETE.md",
        "PAYMENT_INTEGRATION.md",
        "TOURNAMENT_SETUP.md",
    ]
    
    # Medium confidence patterns (general patterns)
    medium_confidence_files = [
        "authentication_guide.md",
        "setup_instructions.md",
        "test_results.md",
    ]
    
    print("  High confidence patterns (should be > 0.8):")
    for filename in high_confidence_files:
        category, confidence = analyzer.classify_by_pattern(filename)
        status = "✓" if confidence > 0.8 else "✗"
        print(f"    {status} {filename} -> confidence: {confidence:.2f}")
    
    print("  Medium confidence patterns (should be 0.6-0.8):")
    for filename in medium_confidence_files:
        category, confidence = analyzer.classify_by_pattern(filename)
        status = "✓" if 0.6 <= confidence <= 0.8 else "✗"
        print(f"    {status} {filename} -> confidence: {confidence:.2f}")


def main():
    """Run all pattern classification tests."""
    print("Enhanced Pattern-Based File Classification Tests (Task 2.2)")
    print("=" * 60)
    
    test_completion_file_patterns()
    test_feature_documentation_patterns()
    test_setup_configuration_patterns()
    test_testing_documentation_patterns()
    test_confidence_scores()
    
    print("\n" + "=" * 60)
    print("Pattern classification tests completed!")


if __name__ == "__main__":
    main()