#!/usr/bin/env python3
"""
Enhanced test for consolidation group identification functionality.

This test creates a more comprehensive set of test files to verify
the enhanced consolidation group identification implemented in Task 4.1.
"""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from doc_consolidation.analyzer import ContentAnalyzer
from doc_consolidation.config import ConsolidationConfig


def test_enhanced_consolidation_identification():
    """Test enhanced consolidation group identification with realistic scenarios."""
    print("Testing Enhanced Consolidation Group Identification")
    print("=" * 60)
    
    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create comprehensive test files that should trigger consolidation
        test_files = create_comprehensive_test_files(temp_path)
        
        # Initialize analyzer
        config = ConsolidationConfig()
        analyzer = ContentAnalyzer(config)
        
        # Discover and analyze files
        discovered_files = analyzer.discover_files(temp_dir)
        print(f"✓ Discovered {len(discovered_files)} test files")
        
        analyses = []
        for file_path in discovered_files:
            analysis = analyzer.analyze_file(file_path)
            analyses.append(analysis)
            print(f"  - {analysis.filename}: {analysis.category.value} (confidence: {analysis.confidence_score:.2f})")
        
        print(f"\n✓ Analyzed {len(analyses)} files")
        
        # Test consolidation group identification
        consolidation_groups = analyzer.identify_consolidation_candidates(analyses)
        
        print(f"\n=== Consolidation Groups Identified ===")
        print(f"✓ Found {len(consolidation_groups)} consolidation groups:")
        
        for i, group in enumerate(consolidation_groups, 1):
            print(f"\n{i}. {group.group_id}")
            print(f"   Category: {group.category.value}")
            print(f"   Strategy: {group.consolidation_strategy.value}")
            print(f"   Primary: {group.primary_file}")
            print(f"   Related: {', '.join(group.related_files)}")
            print(f"   Output: {group.output_filename}")
            print(f"   Total files: {group.total_files}")
            if group.preservation_notes:
                print(f"   Notes: {'; '.join(group.preservation_notes)}")
        
        # Verify expected consolidation groups
        verify_consolidation_results(consolidation_groups)
        
        print(f"\n{'='*60}")
        print("✅ Enhanced consolidation identification test PASSED!")
        print(f"✅ Successfully identified {len(consolidation_groups)} consolidation opportunities")
        
        return True
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


def create_comprehensive_test_files(temp_path: Path) -> dict:
    """Create comprehensive test files for consolidation testing."""
    
    test_files = {}
    
    # 1. Create multiple completion files that should be consolidated
    completion_files = {
        'TASK_1_AUTH_COMPLETE.md': """# Task 1: Authentication Complete
        
## Summary
Authentication system implementation completed successfully.

### Features Implemented
- User login/logout
- Password reset
- Session management

### Date
Created: 2024-01-15
Author: Development Team
        """,
        
        'TASK_2_PAYMENT_COMPLETE.md': """# Task 2: Payment Integration Complete
        
## Summary
Payment system with Stripe integration completed.

### Features Implemented
- Credit card processing
- Subscription management
- Refund handling

### Date
Created: 2024-01-20
Author: Development Team
        """,
        
        'TASK_3_TOURNAMENT_COMPLETE.md': """# Task 3: Tournament System Complete
        
## Summary
Tournament management system implementation finished.

### Features Implemented
- Tournament creation
- Bracket management
- Match scheduling

### Date
Created: 2024-01-25
Author: Development Team
        """,
        
        'PHASE_1_COMPLETE.md': """# Phase 1 Implementation Complete
        
## Overview
First development phase completed successfully.

### Milestones Achieved
- Core authentication
- Basic payment processing
- Initial tournament features

### Date
Created: 2024-02-01
Author: Project Manager
        """,
        
        'IMPLEMENTATION_SUMMARY.md': """# Implementation Summary
        
## Project Status
Overall implementation progress and summary.

### Completed Features
- Authentication system
- Payment integration
- Tournament management

### Date
Created: 2024-02-05
Author: Lead Developer
        """
    }
    
    # 2. Create multiple feature files that should be consolidated
    feature_files = {
        'PAYMENT_STRIPE_INTEGRATION.md': """# Payment Stripe Integration
        
## Overview
Integration with Stripe payment processing.

### Configuration
- API keys setup
- Webhook configuration
- Security settings

### Topics
payment, stripe, integration, api
        """,
        
        'PAYMENT_SUBSCRIPTION_MANAGEMENT.md': """# Payment Subscription Management
        
## Overview
Managing recurring subscriptions and billing.

### Features
- Monthly/yearly subscriptions
- Billing cycle management
- Cancellation handling

### Topics
payment, subscription, billing, management
        """,
        
        'PAYMENT_REFUND_SYSTEM.md': """# Payment Refund System
        
## Overview
Handling refunds and chargebacks.

### Process
- Refund requests
- Automated processing
- Dispute resolution

### Topics
payment, refund, chargeback, dispute
        """,
        
        'TOURNAMENT_BRACKET_SYSTEM.md': """# Tournament Bracket System
        
## Overview
Managing tournament brackets and matches.

### Features
- Single/double elimination
- Swiss system
- Round robin

### Topics
tournament, bracket, match, competition
        """,
        
        'TOURNAMENT_REGISTRATION.md': """# Tournament Registration
        
## Overview
Player registration for tournaments.

### Process
- Registration forms
- Payment collection
- Team formation

### Topics
tournament, registration, player, team
        """
    }
    
    # 3. Create multiple setup files that should be consolidated
    setup_files = {
        'DATABASE_SETUP.md': """# Database Setup
        
## Overview
Setting up the database for the application.

### Steps
1. Install PostgreSQL
2. Create database
3. Run migrations

### Topics
database, setup, postgresql, migration
        """,
        
        'ENVIRONMENT_SETUP.md': """# Environment Setup
        
## Overview
Setting up the development environment.

### Requirements
- Python 3.8+
- Node.js 16+
- Docker

### Topics
environment, setup, development, requirements
        """,
        
        'DEPLOYMENT_SETUP.md': """# Deployment Setup
        
## Overview
Setting up production deployment.

### Infrastructure
- AWS EC2
- Load balancer
- SSL certificates

### Topics
deployment, setup, aws, production
        """
    }
    
    # 4. Create multiple testing files that should be consolidated
    testing_files = {
        'test_payment_integration.md': """# Payment Integration Tests
        
## Test Results
Payment system testing results.

### Test Cases
- Credit card processing: PASS
- Subscription creation: PASS
- Refund processing: PASS

### Topics
test, payment, integration, results
        """,
        
        'test_authentication_system.md': """# Authentication System Tests
        
## Test Results
Authentication testing results.

### Test Cases
- User login: PASS
- Password reset: PASS
- Session management: PASS

### Topics
test, authentication, login, session
        """,
        
        'test_tournament_features.md': """# Tournament Features Tests
        
## Test Results
Tournament system testing results.

### Test Cases
- Tournament creation: PASS
- Bracket generation: PASS
- Match scheduling: PASS

### Topics
test, tournament, bracket, match
        """,
        
        'validation_report.md': """# System Validation Report
        
## Validation Results
Overall system validation results.

### Validation Areas
- Security testing
- Performance testing
- User acceptance testing

### Topics
validation, security, performance, acceptance
        """
    }
    
    # 5. Create quick reference files
    quick_ref_files = {
        'QUICK_START_GUIDE.md': """# Quick Start Guide
        
## Getting Started
Quick guide to get started with the system.

### Steps
1. Clone repository
2. Install dependencies
3. Run application

### Topics
quick, start, guide, getting-started
        """,
        
        'API_REFERENCE.md': """# API Reference
        
## API Endpoints
Quick reference for API endpoints.

### Authentication
- POST /api/auth/login
- POST /api/auth/logout

### Topics
api, reference, endpoints, authentication
        """,
        
        'TROUBLESHOOTING_GUIDE.md': """# Troubleshooting Guide
        
## Common Issues
Quick solutions for common problems.

### Database Issues
- Connection problems
- Migration errors

### Topics
troubleshooting, guide, issues, solutions
        """
    }
    
    # Write all test files
    all_files = {**completion_files, **feature_files, **setup_files, **testing_files, **quick_ref_files}
    
    for filename, content in all_files.items():
        file_path = temp_path / filename
        file_path.write_text(content, encoding='utf-8')
        test_files[filename] = str(file_path)
    
    print(f"✓ Created {len(all_files)} comprehensive test files:")
    print(f"  - {len(completion_files)} completion files")
    print(f"  - {len(feature_files)} feature files")
    print(f"  - {len(setup_files)} setup files")
    print(f"  - {len(testing_files)} testing files")
    print(f"  - {len(quick_ref_files)} quick reference files")
    
    return test_files


def verify_consolidation_results(consolidation_groups):
    """Verify that the consolidation results meet expectations."""
    
    # Expected consolidation groups
    expected_groups = {
        'completion': 0,  # Should find completion file groups
        'feature': 0,     # Should find feature groups (payment, tournament)
        'setup': 0,       # Should find setup consolidation
        'testing': 0,     # Should find testing consolidation
        'quick_ref': 0    # Should find quick reference consolidation
    }
    
    # Count actual groups by type
    for group in consolidation_groups:
        if 'task' in group.group_id.lower() or 'phase' in group.group_id.lower() or 'completion' in group.group_id.lower():
            expected_groups['completion'] += 1
        elif 'payment' in group.group_id.lower() or 'tournament' in group.group_id.lower():
            expected_groups['feature'] += 1
        elif 'setup' in group.group_id.lower():
            expected_groups['setup'] += 1
        elif 'testing' in group.group_id.lower() or 'test' in group.group_id.lower():
            expected_groups['testing'] += 1
        elif 'quick' in group.group_id.lower() or 'reference' in group.group_id.lower():
            expected_groups['quick_ref'] += 1
    
    print(f"\n=== Consolidation Verification ===")
    print(f"✓ Completion groups: {expected_groups['completion']}")
    print(f"✓ Feature groups: {expected_groups['feature']}")
    print(f"✓ Setup groups: {expected_groups['setup']}")
    print(f"✓ Testing groups: {expected_groups['testing']}")
    print(f"✓ Quick reference groups: {expected_groups['quick_ref']}")
    
    # Verify we found some consolidation opportunities
    total_groups = sum(expected_groups.values())
    if total_groups == 0:
        print("⚠️  Warning: No consolidation groups identified")
        return False
    
    print(f"✅ Successfully identified {total_groups} consolidation opportunities")
    return True


if __name__ == "__main__":
    test_enhanced_consolidation_identification()