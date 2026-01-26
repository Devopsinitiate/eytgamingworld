#!/usr/bin/env python3
"""
Comprehensive test for Task 4.2: Content Merging and Deduplication.

This test verifies all the enhanced functionality implemented in Task 4.2:
- Enhanced content merging with chronological preservation
- Advanced duplicate content detection and elimination
- Preservation of unique insights while removing redundancy
- Cross-reference generation between consolidated documents
"""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from doc_consolidation.analyzer import ContentAnalyzer
from doc_consolidation.engine import ConsolidationEngine
from doc_consolidation.config import ConsolidationConfig
from doc_consolidation.models import ConsolidationGroup, ConsolidationStrategy, Category


def test_task_4_2_complete():
    """Comprehensive test for Task 4.2 implementation."""
    print("Testing Task 4.2: Content Merging and Deduplication")
    print("=" * 80)
    
    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create realistic test scenario
        test_files = create_realistic_test_scenario(temp_path)
        
        # Initialize components
        config = ConsolidationConfig()
        analyzer = ContentAnalyzer(config)
        engine = ConsolidationEngine(config)
        
        # Discover and analyze files
        discovered_files = analyzer.discover_files(temp_dir)
        print(f"✓ Discovered {len(discovered_files)} test files")
        
        analyses = {}
        for file_path in discovered_files:
            analysis = analyzer.analyze_file(file_path)
            analyses[analysis.filename] = analysis
        
        # Test all Task 4.2 requirements
        test_results = {}
        
        # Requirement 3.3: Preserve chronological order
        test_results['chronological_preservation'] = test_chronological_preservation(engine, analyses, temp_path)
        
        # Requirement 3.4: Eliminate duplicate content
        test_results['duplicate_elimination'] = test_duplicate_elimination(engine, analyses, temp_path)
        
        # Requirement 3.5: Generate cross-references
        test_results['cross_reference_generation'] = test_cross_reference_generation(engine, analyses, temp_path)
        
        # Integration test: Full consolidation workflow
        test_results['full_workflow'] = test_full_consolidation_workflow(analyzer, engine, analyses, temp_path)
        
        # Report results
        print(f"\n{'='*80}")
        print("TASK 4.2 IMPLEMENTATION RESULTS:")
        print("=" * 80)
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            if not result:
                all_passed = False
        
        print("=" * 80)
        if all_passed:
            print("🎉 TASK 4.2: CONTENT MERGING AND DEDUPLICATION - COMPLETE!")
            print("✅ All requirements successfully implemented and tested")
        else:
            print("⚠️  TASK 4.2: Some tests failed - review implementation")
        
        return all_passed
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


def create_realistic_test_scenario(temp_path: Path) -> dict:
    """Create a realistic test scenario with overlapping documentation."""
    
    test_files = {}
    
    # Realistic scenario: Multiple completion files with overlapping content
    scenario_files = {
        'TASK_1_USER_AUTH_COMPLETE.md': """# Task 1: User Authentication System Complete

## Implementation Summary
Successfully implemented comprehensive user authentication system.

## Features Completed
- User registration with email verification
- Secure login/logout functionality
- Password reset with email tokens
- Session management using JWT
- Basic user profile management

## Technical Implementation
- Database: Users table with encrypted passwords
- Security: bcrypt password hashing, CSRF protection
- Frontend: Login/register forms with validation
- Backend: Express.js authentication middleware

## Testing Results
- Unit tests: 45 tests passing
- Integration tests: 12 tests passing
- Security audit: No critical issues found

## Performance Metrics
- Login response time: 150ms average
- Registration process: 300ms average
- Concurrent users tested: 100

## Date Completed
January 15, 2024

## Next Steps
- Implement two-factor authentication
- Add OAuth integration
- Enhance security monitoring
        """,
        
        'TASK_2_ENHANCED_AUTH_COMPLETE.md': """# Task 2: Enhanced Authentication Features Complete

## Implementation Summary
Enhanced the existing authentication system with advanced security features.

## Features Completed
- Two-factor authentication (TOTP)
- OAuth integration (Google, GitHub)
- Advanced session management
- User profile management with avatars
- Account lockout protection
- Password strength validation

## Technical Implementation
- Database: Extended users table, added oauth_tokens table
- Security: Enhanced bcrypt settings, rate limiting, CSRF protection
- Frontend: 2FA setup forms, OAuth buttons, profile management
- Backend: OAuth providers integration, enhanced middleware

## Testing Results
- Unit tests: 67 tests passing (22 new tests added)
- Integration tests: 18 tests passing (6 new tests)
- Security audit: Zero critical issues, 2 minor improvements made
- Penetration testing: Passed all security tests

## Performance Metrics
- Login response time: 120ms average (improved)
- Registration process: 280ms average (improved)
- 2FA verification: 50ms average
- Concurrent users tested: 500 (5x improvement)

## Date Completed
February 1, 2024

## Integration Points
- Payment system requires authenticated users
- Tournament registration needs user profiles
- Dashboard displays user-specific data
        """,
        
        'TASK_3_PAYMENT_INTEGRATION_COMPLETE.md': """# Task 3: Payment System Integration Complete

## Implementation Summary
Integrated comprehensive payment processing system with Stripe.

## Features Completed
- Credit card payment processing
- Subscription management (monthly/yearly)
- Refund and chargeback handling
- Invoice generation and email delivery
- Payment method storage for users
- Multi-currency support (USD, EUR, GBP)

## Technical Implementation
- Database: Payments, subscriptions, invoices tables
- Security: PCI compliance, secure token handling
- Frontend: Payment forms with Stripe Elements
- Backend: Stripe API integration, webhook handling

## Testing Results
- Unit tests: 38 tests passing
- Integration tests: 15 tests passing
- Payment flow tests: All scenarios tested
- Webhook tests: All events handled correctly

## Performance Metrics
- Payment processing: 2.5s average
- Subscription creation: 1.8s average
- Refund processing: 3.2s average

## Date Completed
February 10, 2024

## Dependencies
- Requires user authentication for payment processing
- Integrates with tournament registration system
- Connects to notification system for payment updates
        """,
        
        'PAYMENT_STRIPE_SETUP_GUIDE.md': """# Stripe Payment Integration Setup Guide

## Overview
Complete setup guide for integrating Stripe payment processing.

## Prerequisites
- Active Stripe account
- SSL certificate for production
- User authentication system in place

## Setup Steps

### 1. Account Configuration
- Create Stripe account
- Obtain API keys (test and live)
- Configure webhook endpoints
- Set up tax settings

### 2. Database Setup
```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    stripe_payment_id VARCHAR(255),
    amount DECIMAL(10,2),
    currency VARCHAR(3),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. Backend Integration
- Install Stripe SDK
- Configure API keys
- Implement payment endpoints
- Set up webhook handlers

### 4. Frontend Integration
- Include Stripe.js
- Create payment forms
- Handle payment responses
- Implement error handling

## Security Considerations
- Never store card details
- Use HTTPS for all transactions
- Validate webhook signatures
- Implement rate limiting

## Testing
- Use Stripe test cards
- Test all payment scenarios
- Verify webhook handling
- Test error conditions
        """,
        
        'PAYMENT_PROCESSING_GUIDE.md': """# Payment Processing Implementation Guide

## Overview
Comprehensive guide for implementing secure payment processing.

## Architecture Overview
The payment system consists of:
- Frontend payment forms
- Backend API endpoints
- Database for transaction records
- Webhook handlers for real-time updates

## Implementation Steps

### 1. Database Design
```sql
-- Enhanced payment tables
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    stripe_payment_id VARCHAR(255) UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50),
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    plan_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. API Endpoints
- POST /api/payments/create - Create payment intent
- POST /api/payments/confirm - Confirm payment
- GET /api/payments/history - Get payment history
- POST /api/subscriptions/create - Create subscription
- POST /api/webhooks/stripe - Handle Stripe webhooks

### 3. Security Implementation
- PCI DSS compliance
- Secure API key management
- Webhook signature verification
- Input validation and sanitization
- Rate limiting and fraud detection

### 4. Error Handling
- Payment declined scenarios
- Network timeout handling
- Webhook retry logic
- User-friendly error messages

## Integration Points
- User authentication required for all payments
- Tournament registration triggers payment flow
- Subscription management in user dashboard
- Email notifications for payment events

## Testing Strategy
- Unit tests for all payment functions
- Integration tests with Stripe test mode
- End-to-end payment flow testing
- Webhook event simulation
- Load testing for high-volume scenarios
        """,
        
        'TOURNAMENT_REGISTRATION_COMPLETE.md': """# Tournament Registration System Complete

## Implementation Summary
Completed comprehensive tournament registration system with payment integration.

## Features Completed
- Tournament creation and management
- Player registration with payment processing
- Team formation and management
- Bracket generation (single/double elimination)
- Match scheduling and results tracking
- Prize distribution system

## Technical Implementation
- Database: Tournaments, participants, matches, brackets tables
- Integration: Payment system for entry fees
- Frontend: Registration forms, tournament browser
- Backend: Tournament logic, bracket algorithms

## Testing Results
- Unit tests: 52 tests passing
- Integration tests: 20 tests passing
- Tournament flow tests: All scenarios covered
- Load tests: 1000 concurrent registrations

## Performance Metrics
- Registration process: 1.2s average
- Bracket generation: 500ms for 64 players
- Match result updates: 100ms average

## Date Completed
February 20, 2024

## Dependencies
- Requires user authentication for registration
- Integrates with payment system for entry fees
- Uses notification system for match updates
        """
    }
    
    # Write all test files
    for filename, content in scenario_files.items():
        file_path = temp_path / filename
        file_path.write_text(content, encoding='utf-8')
        test_files[filename] = str(file_path)
    
    print(f"✓ Created realistic test scenario with {len(scenario_files)} files")
    
    return test_files


def test_chronological_preservation(engine, analyses, temp_path):
    """Test Requirement 3.3: Preserve chronological order."""
    print(f"\n=== Testing Chronological Order Preservation ===")
    
    # Test with completion files that have clear chronological order
    completion_files = [
        'TASK_1_USER_AUTH_COMPLETE.md',
        'TASK_2_ENHANCED_AUTH_COMPLETE.md', 
        'TASK_3_PAYMENT_INTEGRATION_COMPLETE.md',
        'TOURNAMENT_REGISTRATION_COMPLETE.md'
    ]
    
    # Test chronological ordering
    ordered_files = engine.preserve_chronology(completion_files, analyses)
    
    print(f"✓ Chronological ordering completed for {len(completion_files)} files")
    
    # Verify task sequence is preserved
    task1_pos = ordered_files.index('TASK_1_USER_AUTH_COMPLETE.md')
    task2_pos = ordered_files.index('TASK_2_ENHANCED_AUTH_COMPLETE.md')
    task3_pos = ordered_files.index('TASK_3_PAYMENT_INTEGRATION_COMPLETE.md')
    
    chronological_correct = task1_pos < task2_pos < task3_pos
    
    if chronological_correct:
        print("✅ Task sequence preserved correctly")
    else:
        print("❌ Task sequence not preserved correctly")
    
    # Test with consolidation group
    group = ConsolidationGroup(
        group_id="test_chronological",
        category=Category.IMPLEMENTATION_COMPLETION,
        primary_file="TASK_1_USER_AUTH_COMPLETE.md",
        related_files=["TASK_2_ENHANCED_AUTH_COMPLETE.md", "TASK_3_PAYMENT_INTEGRATION_COMPLETE.md"],
        consolidation_strategy=ConsolidationStrategy.MERGE_CHRONOLOGICAL,
        output_filename="chronological_test.md"
    )
    
    consolidated = engine.consolidate_group(group, analyses)
    
    # Verify chronological content appears in order
    task1_content_pos = consolidated.find("TASK 1") if "TASK 1" in consolidated else consolidated.find("Task 1")
    task2_content_pos = consolidated.find("TASK 2") if "TASK 2" in consolidated else consolidated.find("Task 2")  
    task3_content_pos = consolidated.find("TASK 3") if "TASK 3" in consolidated else consolidated.find("Task 3")
    
    # If we can't find the exact task markers, look for the section headers
    if task1_content_pos == -1:
        task1_content_pos = consolidated.find("USER_AUTH_COMPLETE")
    if task2_content_pos == -1:
        task2_content_pos = consolidated.find("ENHANCED_AUTH_COMPLETE")
    if task3_content_pos == -1:
        task3_content_pos = consolidated.find("PAYMENT_INTEGRATION_COMPLETE")
    
    content_order_correct = (task1_content_pos != -1 and 
                           task2_content_pos != -1 and 
                           task3_content_pos != -1 and
                           task1_content_pos < task2_content_pos < task3_content_pos)
    
    if content_order_correct:
        print("✅ Consolidated content maintains chronological order")
    else:
        print("❌ Consolidated content chronological order incorrect")
    
    # Save result
    result_path = temp_path / "chronological_test_result.md"
    result_path.write_text(consolidated, encoding='utf-8')
    print(f"✓ Chronological test result saved to {result_path}")
    
    return chronological_correct and content_order_correct


def test_duplicate_elimination(engine, analyses, temp_path):
    """Test Requirement 3.4: Eliminate duplicate content while preserving unique insights."""
    print(f"\n=== Testing Duplicate Content Elimination ===")
    
    # Create test content with significant overlap for better testing
    overlapping_content1 = """# Payment Setup Guide

## Overview
Complete guide for setting up payment processing with Stripe.

## Features
- Credit card processing
- Subscription management  
- Refund handling
- Invoice generation

## Setup Steps
1. Create Stripe account
2. Obtain API keys
3. Configure webhooks
4. Set up payment forms

## Security
- PCI compliance
- Secure token handling
- Webhook verification

## Testing
- Test card numbers
- Webhook testing
- Error handling
"""

    overlapping_content2 = """# Payment Processing Guide

## Overview
Comprehensive guide for implementing payment processing.

## Features
- Credit card processing with 3D Secure
- Advanced subscription management
- Refund and chargeback handling
- Invoice generation and delivery
- Multi-currency support

## Setup Steps
1. Choose payment provider
2. Obtain API credentials
3. Configure webhooks and callbacks
4. Set up payment forms and UI
5. Implement security measures

## Security
- PCI DSS compliance
- Secure token handling
- Webhook signature verification
- Fraud detection

## Testing
- Test card numbers and scenarios
- Webhook testing procedures
- Error handling verification
- Load testing
"""
    
    original_length = len(overlapping_content1) + len(overlapping_content2)
    print(f"✓ Original combined length: {original_length} characters")
    
    # Test deduplication
    deduplicated = engine.eliminate_redundancy([overlapping_content1, overlapping_content2])
    deduplicated_length = len(deduplicated)
    
    print(f"✓ Deduplicated length: {deduplicated_length} characters")
    
    # Calculate reduction
    reduction_ratio = (original_length - deduplicated_length) / original_length
    print(f"✓ Content reduction: {reduction_ratio:.1%}")
    
    # Verify important unique content is preserved
    unique_terms = [
        'Stripe',  # From first guide
        '3D Secure',  # From second guide
        'PCI compliance',  # Common but important
        'fraud detection',  # From second guide
        'multi-currency'  # From second guide
    ]
    
    preserved_terms = sum(1 for term in unique_terms if term.lower() in deduplicated.lower())
    preservation_ratio = preserved_terms / len(unique_terms)
    
    print(f"✓ Important terms preserved: {preserved_terms}/{len(unique_terms)} ({preservation_ratio:.1%})")
    
    # Test with actual files from analyses (fallback test)
    if 'PAYMENT_STRIPE_SETUP_GUIDE.md' in analyses and 'PAYMENT_PROCESSING_GUIDE.md' in analyses:
        payment_content1 = analyses['PAYMENT_STRIPE_SETUP_GUIDE.md'].filepath.read_text()
        payment_content2 = analyses['PAYMENT_PROCESSING_GUIDE.md'].filepath.read_text()
        
        file_deduplicated = engine.eliminate_redundancy([payment_content1, payment_content2])
        file_original_length = len(payment_content1) + len(payment_content2)
        file_reduction = (file_original_length - len(file_deduplicated)) / file_original_length
        
        print(f"✓ File-based deduplication reduction: {file_reduction:.1%}")
        deduplication_effective = file_reduction > 0 or reduction_ratio > 0.1
    else:
        deduplication_effective = reduction_ratio > 0.1
    
    if deduplication_effective:
        print("✅ Deduplication effectively eliminates duplicates")
    else:
        print("❌ Deduplication does not eliminate duplicates effectively")
    
    # Save result
    result_path = temp_path / "deduplication_test_result.md"
    result_path.write_text(deduplicated, encoding='utf-8')
    print(f"✓ Deduplication test result saved to {result_path}")
    
    success = (reduction_ratio > 0.1 and  # At least 10% reduction from test content
               preservation_ratio > 0.6 and  # At least 60% term preservation  
               deduplication_effective)
    
    return success


def test_cross_reference_generation(engine, analyses, temp_path):
    """Test Requirement 3.5: Generate cross-references between consolidated documents."""
    print(f"\n=== Testing Cross-Reference Generation ===")
    
    # Create consolidated documents from our test files
    consolidated_docs = {
        "authentication_system_guide.md": (
            analyses['TASK_1_USER_AUTH_COMPLETE.md'].filepath.read_text() + 
            "\n\n" + 
            analyses['TASK_2_ENHANCED_AUTH_COMPLETE.md'].filepath.read_text()
        ),
        "payment_processing_guide.md": (
            analyses['PAYMENT_STRIPE_SETUP_GUIDE.md'].filepath.read_text() + 
            "\n\n" + 
            analyses['PAYMENT_PROCESSING_GUIDE.md'].filepath.read_text()
        ),
        "tournament_system_guide.md": analyses['TOURNAMENT_REGISTRATION_COMPLETE.md'].filepath.read_text()
    }
    
    print(f"✓ Created {len(consolidated_docs)} consolidated documents for cross-referencing")
    
    # Generate cross-references
    cross_refs = engine.create_cross_references(consolidated_docs, [])
    
    print(f"✓ Generated cross-references for {len(cross_refs)} documents")
    
    # Verify cross-references are generated
    total_refs = sum(len(refs) for refs in cross_refs.values())
    print(f"✓ Total cross-references generated: {total_refs}")
    
    # Verify expected relationships
    expected_relationships = {
        "authentication_system_guide.md": ["payment_processing_guide.md", "tournament_system_guide.md"],
        "payment_processing_guide.md": ["authentication_system_guide.md"],
        "tournament_system_guide.md": ["authentication_system_guide.md", "payment_processing_guide.md"]
    }
    
    relationships_correct = 0
    total_expected = 0
    
    for doc, expected_refs in expected_relationships.items():
        if doc in cross_refs:
            actual_refs = cross_refs[doc]
            for expected_ref in expected_refs:
                total_expected += 1
                if expected_ref in actual_refs:
                    relationships_correct += 1
                    print(f"  ✓ {doc} → {expected_ref}")
                else:
                    print(f"  ❌ Missing: {doc} → {expected_ref}")
    
    relationship_accuracy = relationships_correct / total_expected if total_expected > 0 else 0
    print(f"✓ Cross-reference accuracy: {relationships_correct}/{total_expected} ({relationship_accuracy:.1%})")
    
    # Test bidirectional references
    bidirectional_count = 0
    for doc1, refs1 in cross_refs.items():
        for ref_doc in refs1:
            if ref_doc in cross_refs and doc1 in cross_refs[ref_doc]:
                bidirectional_count += 1
    
    print(f"✓ Bidirectional references: {bidirectional_count}")
    
    # Save cross-reference analysis
    ref_analysis = ["Cross-Reference Analysis", "=" * 30]
    for doc_name, refs in cross_refs.items():
        ref_analysis.append(f"\n{doc_name}:")
        for ref in refs:
            ref_analysis.append(f"  → {ref}")
    
    result_path = temp_path / "cross_reference_analysis.txt"
    result_path.write_text('\n'.join(ref_analysis), encoding='utf-8')
    print(f"✓ Cross-reference analysis saved to {result_path}")
    
    success = (total_refs > 0 and 
               relationship_accuracy > 0.5 and  # At least 50% accuracy
               bidirectional_count > 0)
    
    return success


def test_full_consolidation_workflow(analyzer, engine, analyses, temp_path):
    """Test the complete consolidation workflow integration."""
    print(f"\n=== Testing Full Consolidation Workflow ===")
    
    # Identify consolidation groups
    consolidation_groups = analyzer.identify_consolidation_candidates(list(analyses.values()))
    print(f"✓ Identified {len(consolidation_groups)} consolidation groups")
    
    # Process each group
    consolidated_docs = {}
    
    for group in consolidation_groups:
        print(f"  Processing group: {group.group_id}")
        
        # Consolidate the group
        consolidated_content = engine.consolidate_group(group, analyses)
        
        if consolidated_content:
            consolidated_docs[group.output_filename] = consolidated_content
            print(f"    ✓ Generated {len(consolidated_content)} characters")
            
            # Save individual result
            result_path = temp_path / f"workflow_{group.output_filename}"
            result_path.write_text(consolidated_content, encoding='utf-8')
        else:
            print(f"    ❌ Failed to generate content")
    
    # Generate cross-references between all consolidated documents
    if consolidated_docs:
        cross_refs = engine.create_cross_references(consolidated_docs, consolidation_groups)
        print(f"✓ Generated cross-references between {len(consolidated_docs)} consolidated documents")
        
        # Save comprehensive workflow result
        workflow_summary = [
            "# Complete Consolidation Workflow Results",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"## Summary",
            f"- Original files processed: {len(analyses)}",
            f"- Consolidation groups created: {len(consolidation_groups)}",
            f"- Consolidated documents generated: {len(consolidated_docs)}",
            f"- Cross-references created: {sum(len(refs) for refs in cross_refs.values())}",
            "",
            "## Consolidation Groups",
        ]
        
        for group in consolidation_groups:
            workflow_summary.extend([
                f"### {group.group_id}",
                f"- Strategy: {group.consolidation_strategy.value}",
                f"- Files: {group.total_files}",
                f"- Output: {group.output_filename}",
                ""
            ])
        
        workflow_summary.extend([
            "## Cross-References",
            ""
        ])
        
        for doc, refs in cross_refs.items():
            workflow_summary.append(f"**{doc}**")
            for ref in refs:
                workflow_summary.append(f"  - {ref}")
            workflow_summary.append("")
        
        result_path = temp_path / "complete_workflow_summary.md"
        result_path.write_text('\n'.join(workflow_summary), encoding='utf-8')
        print(f"✓ Complete workflow summary saved to {result_path}")
        
        return len(consolidated_docs) > 0 and len(cross_refs) > 0
    
    return False


if __name__ == "__main__":
    test_task_4_2_complete()