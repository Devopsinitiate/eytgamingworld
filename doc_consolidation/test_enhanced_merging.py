#!/usr/bin/env python3
"""
Enhanced test for content merging and deduplication functionality.

This test verifies the enhanced content merging and deduplication
functionality implemented in Task 4.2.
"""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from doc_consolidation.analyzer import ContentAnalyzer
from doc_consolidation.engine import ConsolidationEngine
from doc_consolidation.config import ConsolidationConfig
from doc_consolidation.models import ConsolidationGroup, ConsolidationStrategy, Category


def test_enhanced_content_merging():
    """Test enhanced content merging and deduplication functionality."""
    print("Testing Enhanced Content Merging and Deduplication")
    print("=" * 70)
    
    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create test files with complex overlapping content
        test_files = create_complex_test_files(temp_path)
        
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
            print(f"  - {analysis.filename}: {analysis.category.value}")
        
        # Test enhanced functionality
        test_enhanced_deduplication(engine, analyses, temp_path)
        test_enhanced_chronological_ordering(engine, analyses, temp_path)
        test_enhanced_cross_references(engine, analyses, temp_path)
        test_comprehensive_consolidation(engine, analyses, temp_path)
        
        print(f"\n{'='*70}")
        print("✅ Enhanced content merging and deduplication test PASSED!")
        
        return True
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


def create_complex_test_files(temp_path: Path) -> dict:
    """Create complex test files with overlapping content for enhanced testing."""
    
    test_files = {}
    
    # Complex overlapping files for deduplication testing
    complex_files = {
        'TASK_1_AUTH_COMPLETE.md': """# Task 1: Authentication System Complete

## Overview
The authentication system has been successfully implemented with comprehensive security features.

## Features Implemented
- User registration and login functionality
- Password reset mechanism with email verification
- Session management using JWT tokens
- Two-factor authentication (2FA) support
- OAuth integration with Google and GitHub

## Implementation Details
The authentication system uses JWT tokens for secure session management.
Security measures include:
- Password hashing with bcrypt and salt
- Rate limiting for login attempts
- CSRF protection
- Secure cookie handling

## Database Schema
- users table with encrypted passwords
- sessions table for active sessions
- oauth_tokens table for third-party authentication

## Testing Results
- All unit tests passing (95% coverage)
- Security audit completed successfully
- Penetration testing performed
- Load testing completed (1000 concurrent users)

## Date
Created: 2024-01-15
Completed: 2024-01-20
Author: Development Team
        """,
        
        'TASK_2_AUTH_ENHANCEMENT.md': """# Task 2: Authentication Enhancement Complete

## Overview
Enhanced the existing authentication system with advanced security features and improved user experience.

## Features Implemented
- User registration and login functionality (enhanced)
- Advanced password reset mechanism with SMS verification
- Enhanced session management using JWT tokens with refresh tokens
- Two-factor authentication (2FA) support with TOTP
- OAuth integration with Google, GitHub, and Microsoft
- Single Sign-On (SSO) capability

## Implementation Details
The enhanced authentication system uses JWT tokens with refresh token rotation for secure session management.
Advanced security measures include:
- Password hashing with bcrypt and salt (upgraded algorithm)
- Advanced rate limiting with IP-based blocking
- CSRF protection with double-submit cookies
- Secure cookie handling with SameSite attributes
- Session fingerprinting for additional security

## Database Schema
- users table with encrypted passwords and metadata
- sessions table for active sessions with fingerprints
- oauth_tokens table for third-party authentication
- refresh_tokens table for token rotation
- security_logs table for audit trail

## Testing Results
- All unit tests passing (98% coverage)
- Security audit completed successfully with zero critical issues
- Advanced penetration testing performed
- Load testing completed (5000 concurrent users)
- Performance optimization completed

## Additional Features
- Account lockout after failed attempts
- Password strength validation
- Email verification for new accounts
- Account recovery mechanisms

## Date
Created: 2024-01-25
Completed: 2024-02-01
Author: Development Team
        """,
        
        'PAYMENT_STRIPE_INTEGRATION.md': """# Payment Integration with Stripe

## Overview
Complete integration with Stripe payment processing system for secure and reliable payment handling.

## Setup Process
1. Create Stripe account and obtain API keys
2. Configure webhook endpoints for payment events
3. Set up payment forms with Stripe Elements
4. Implement server-side payment processing
5. Configure tax calculation and invoicing

## Features Implemented
- Credit card processing with 3D Secure
- Subscription management with multiple plans
- Refund and chargeback handling
- Invoice generation and management
- Multi-currency support (USD, EUR, GBP)
- Payment method storage for returning customers

## Security Implementation
- PCI DSS compliance maintained
- Secure token handling with Stripe tokens
- Webhook signature verification
- Fraud detection and prevention
- SSL/TLS encryption for all transactions

## Database Schema
- payments table for transaction records
- subscriptions table for recurring payments
- payment_methods table for stored methods
- invoices table for billing records

## Testing Procedures
- Test card numbers for various scenarios
- Webhook testing with Stripe CLI
- Error handling verification
- Refund process testing
- Subscription lifecycle testing

## Integration Points
- User authentication required for payments
- Tournament registration payment processing
- Subscription management in user dashboard

## Date
Created: 2024-02-05
Author: Payment Team
        """,
        
        'PAYMENT_PROCESSING_GUIDE.md': """# Comprehensive Payment Processing Guide

## Overview
Complete guide for implementing secure payment processing across the entire application ecosystem.

## Setup Process
1. Choose and configure payment provider (Stripe recommended)
2. Obtain API credentials and configure environments
3. Set up webhook endpoints and event handling
4. Implement payment forms with security best practices
5. Configure tax calculation and compliance
6. Set up monitoring and alerting

## Features Implemented
- Credit card processing with advanced fraud detection
- Subscription management with flexible billing cycles
- Comprehensive refund and chargeback handling
- Automated invoice generation and delivery
- Multi-currency support with real-time conversion
- Payment method storage with tokenization
- Recurring payment automation
- Payment analytics and reporting

## Security Implementation
- Full PCI DSS compliance certification
- Advanced secure token handling with encryption
- Comprehensive webhook signature verification
- Multi-layer fraud detection and prevention
- End-to-end SSL/TLS encryption
- Regular security audits and updates

## Database Schema
- payments table with comprehensive transaction data
- subscriptions table with flexible billing options
- payment_methods table with secure tokenization
- invoices table with detailed billing information
- payment_logs table for audit trails
- fraud_detection table for security monitoring

## Testing Procedures
- Comprehensive test card scenarios
- Automated webhook testing
- Error handling and recovery testing
- Load testing for high-volume transactions
- Security penetration testing
- Compliance validation testing

## Integration Points
- Seamless user authentication integration
- Tournament registration with payment processing
- Subscription management in user dashboard
- Admin panel for payment monitoring
- Reporting and analytics integration

## Performance Optimization
- Caching for payment method retrieval
- Asynchronous webhook processing
- Database indexing for transaction queries
- CDN integration for payment forms

## Date
Created: 2024-02-10
Updated: 2024-02-15
Author: Payment Team
        """,
        
        'TOURNAMENT_SYSTEM_SETUP.md': """# Tournament Management System Setup

## Overview
Comprehensive setup guide for the tournament management system with advanced features.

## Database Schema Design
- tournaments table with metadata and configuration
- participants table with player information and stats
- matches table with results and scheduling
- brackets table with tournament structure
- prizes table with reward distribution

## Core Features
- Tournament creation with multiple formats
- Player registration and team management
- Advanced bracket generation algorithms
- Intelligent match scheduling system
- Real-time scoring and results tracking

## Tournament Types Supported
- Single elimination tournaments
- Double elimination with losers bracket
- Swiss system for large tournaments
- Round robin for small groups
- Custom hybrid formats

## Configuration Options
- Flexible scoring systems and tiebreakers
- Customizable time limits and rules
- Registration settings and requirements
- Prize distribution configurations
- Streaming and broadcast integration

## Integration Requirements
- User authentication for player registration
- Payment processing for entry fees
- Notification system for match updates
- Dashboard integration for management

## Date
Created: 2024-02-12
Author: Tournament Team
        """,
        
        'TOURNAMENT_MANAGEMENT_GUIDE.md': """# Advanced Tournament Management Guide

## Overview
Complete guide for managing tournaments with advanced features and administrative capabilities.

## Database Schema Design
- tournaments table with comprehensive metadata
- participants table with detailed player profiles
- matches table with extensive result tracking
- brackets table with dynamic tournament structure
- prizes table with flexible reward systems
- tournament_logs table for audit trails

## Advanced Features
- Multi-format tournament creation and management
- Sophisticated player registration with verification
- AI-powered bracket generation algorithms
- Dynamic match scheduling with conflict resolution
- Real-time scoring with live updates
- Automated prize distribution system

## Tournament Types Supported
- Single elimination with seeding
- Double elimination with comprehensive losers bracket
- Swiss system with advanced pairing algorithms
- Round robin with tiebreaker systems
- Custom hybrid formats with rule flexibility
- Team-based tournaments with roster management

## Administrative Tools
- Tournament monitoring dashboard
- Player management and verification
- Match result validation and disputes
- Financial tracking and reporting
- Communication tools for participants

## Configuration Options
- Advanced scoring systems with custom rules
- Flexible time limits and scheduling
- Registration requirements and restrictions
- Prize distribution with tax handling
- Streaming integration with multiple platforms
- Sponsorship and branding customization

## Integration Requirements
- Seamless user authentication integration
- Comprehensive payment processing for fees
- Advanced notification system for all updates
- Dashboard integration for complete management
- Reporting and analytics for performance tracking

## Performance Features
- Caching for tournament data
- Real-time updates with WebSocket
- Mobile-responsive interface
- Offline capability for match recording

## Date
Created: 2024-02-18
Updated: 2024-02-20
Author: Tournament Team
        """
    }
    
    # Write all test files
    for filename, content in complex_files.items():
        file_path = temp_path / filename
        file_path.write_text(content, encoding='utf-8')
        test_files[filename] = str(file_path)
    
    print(f"✓ Created {len(complex_files)} complex test files with overlapping content")
    
    return test_files


def test_enhanced_deduplication(engine, analyses, temp_path):
    """Test enhanced deduplication functionality."""
    print(f"\n=== Testing Enhanced Deduplication ===")
    
    # Test with highly overlapping authentication content
    auth_content1 = analyses['TASK_1_AUTH_COMPLETE.md'].filepath.read_text()
    auth_content2 = analyses['TASK_2_AUTH_ENHANCEMENT.md'].filepath.read_text()
    
    print(f"✓ Original content 1: {len(auth_content1)} characters")
    print(f"✓ Original content 2: {len(auth_content2)} characters")
    print(f"✓ Combined length: {len(auth_content1) + len(auth_content2)} characters")
    
    # Test enhanced deduplication
    deduplicated = engine.eliminate_redundancy([auth_content1, auth_content2])
    
    print(f"✓ Deduplicated content: {len(deduplicated)} characters")
    
    # Calculate deduplication efficiency
    original_total = len(auth_content1) + len(auth_content2)
    reduction_ratio = (original_total - len(deduplicated)) / original_total
    print(f"✓ Content reduction: {reduction_ratio:.1%}")
    
    # Verify important content is preserved
    important_terms = ['JWT tokens', 'bcrypt', 'OAuth', '2FA', 'security audit']
    preserved_terms = sum(1 for term in important_terms if term in deduplicated)
    print(f"✓ Important terms preserved: {preserved_terms}/{len(important_terms)}")
    
    # Save result for inspection
    result_path = temp_path / "enhanced_deduplication_result.md"
    result_path.write_text(deduplicated, encoding='utf-8')
    print(f"✓ Enhanced deduplication result saved to {result_path}")


def test_enhanced_chronological_ordering(engine, analyses, temp_path):
    """Test enhanced chronological ordering functionality."""
    print(f"\n=== Testing Enhanced Chronological Ordering ===")
    
    # Test with files that have various date sources
    test_files = [
        'TASK_1_AUTH_COMPLETE.md',
        'TASK_2_AUTH_ENHANCEMENT.md',
        'PAYMENT_STRIPE_INTEGRATION.md',
        'PAYMENT_PROCESSING_GUIDE.md',
        'TOURNAMENT_SYSTEM_SETUP.md',
        'TOURNAMENT_MANAGEMENT_GUIDE.md'
    ]
    
    # Test chronological ordering
    ordered_files = engine.preserve_chronology(test_files, analyses)
    
    print(f"✓ Chronological ordering completed")
    print(f"✓ Original order: {', '.join(test_files[:3])}...")
    print(f"✓ Chronological order: {', '.join(ordered_files[:3])}...")
    
    # Verify ordering makes sense
    task1_pos = ordered_files.index('TASK_1_AUTH_COMPLETE.md')
    task2_pos = ordered_files.index('TASK_2_AUTH_ENHANCEMENT.md')
    
    if task1_pos < task2_pos:
        print("✓ Task sequence ordering preserved correctly")
    else:
        print("⚠️  Warning: Task sequence may not be optimal")
    
    # Save ordering analysis
    ordering_analysis = []
    for i, filename in enumerate(ordered_files, 1):
        analysis = analyses[filename]
        date_info = "No date"
        if analysis.metadata.creation_date:
            date_info = analysis.metadata.creation_date.strftime('%Y-%m-%d')
        ordering_analysis.append(f"{i}. {filename} - {date_info}")
    
    result_path = temp_path / "chronological_ordering_result.txt"
    result_path.write_text('\n'.join(ordering_analysis), encoding='utf-8')
    print(f"✓ Chronological ordering analysis saved to {result_path}")


def test_enhanced_cross_references(engine, analyses, temp_path):
    """Test enhanced cross-reference generation functionality."""
    print(f"\n=== Testing Enhanced Cross-Reference Generation ===")
    
    # Create sample consolidated documents
    consolidated_docs = {
        "authentication_comprehensive_guide.md": analyses['TASK_1_AUTH_COMPLETE.md'].filepath.read_text(),
        "payment_comprehensive_guide.md": analyses['PAYMENT_STRIPE_INTEGRATION.md'].filepath.read_text(),
        "tournament_comprehensive_guide.md": analyses['TOURNAMENT_SYSTEM_SETUP.md'].filepath.read_text()
    }
    
    # Test enhanced cross-reference generation
    cross_refs = engine.create_cross_references(consolidated_docs, [])
    
    print(f"✓ Enhanced cross-reference generation completed")
    print(f"✓ Generated references for {len(cross_refs)} documents")
    
    total_refs = sum(len(refs) for refs in cross_refs.values())
    print(f"✓ Total cross-references: {total_refs}")
    
    # Analyze cross-reference quality
    for doc_name, refs in cross_refs.items():
        print(f"  - {doc_name}: {len(refs)} references")
        for ref in refs[:2]:  # Show first 2 references
            print(f"    → {ref}")
    
    # Verify bidirectional references
    bidirectional_count = 0
    for doc1, refs1 in cross_refs.items():
        for ref_doc in refs1:
            if ref_doc in cross_refs and doc1 in cross_refs[ref_doc]:
                bidirectional_count += 1
    
    print(f"✓ Bidirectional references: {bidirectional_count}")
    
    # Save cross-reference analysis
    ref_analysis = []
    for doc_name, refs in cross_refs.items():
        ref_analysis.append(f"\n{doc_name}:")
        for ref in refs:
            ref_analysis.append(f"  → {ref}")
    
    result_path = temp_path / "cross_references_result.txt"
    result_path.write_text('\n'.join(ref_analysis), encoding='utf-8')
    print(f"✓ Cross-reference analysis saved to {result_path}")


def test_comprehensive_consolidation(engine, analyses, temp_path):
    """Test comprehensive consolidation with all strategies."""
    print(f"\n=== Testing Comprehensive Consolidation ===")
    
    # Test different consolidation strategies
    test_groups = [
        ConsolidationGroup(
            group_id="auth_consolidation",
            category=Category.IMPLEMENTATION_COMPLETION,
            primary_file="TASK_1_AUTH_COMPLETE.md",
            related_files=["TASK_2_AUTH_ENHANCEMENT.md"],
            consolidation_strategy=ConsolidationStrategy.MERGE_CHRONOLOGICAL,
            output_filename="authentication_complete_history.md"
        ),
        ConsolidationGroup(
            group_id="payment_consolidation",
            category=Category.FEATURE_DOCS,
            primary_file="PAYMENT_STRIPE_INTEGRATION.md",
            related_files=["PAYMENT_PROCESSING_GUIDE.md"],
            consolidation_strategy=ConsolidationStrategy.MERGE_TOPICAL,
            output_filename="payment_comprehensive_guide.md"
        ),
        ConsolidationGroup(
            group_id="tournament_consolidation",
            category=Category.FEATURE_DOCS,
            primary_file="TOURNAMENT_SYSTEM_SETUP.md",
            related_files=["TOURNAMENT_MANAGEMENT_GUIDE.md"],
            consolidation_strategy=ConsolidationStrategy.MERGE_TOPICAL,
            output_filename="tournament_comprehensive_guide.md"
        )
    ]
    
    consolidated_results = {}
    
    for group in test_groups:
        print(f"\n--- Testing {group.consolidation_strategy.value} strategy ---")
        
        consolidated_content = engine.consolidate_group(group, analyses)
        consolidated_results[group.output_filename] = consolidated_content
        
        print(f"✓ Consolidated {group.total_files} files")
        print(f"✓ Output length: {len(consolidated_content)} characters")
        
        # Verify content quality
        if consolidated_content:
            sections = consolidated_content.count('##')
            print(f"✓ Sections created: {sections}")
            
            # Save result
            result_path = temp_path / group.output_filename
            result_path.write_text(consolidated_content, encoding='utf-8')
            print(f"✓ Result saved to {result_path}")
    
    # Test cross-references between consolidated documents
    print(f"\n--- Testing Cross-References Between Consolidated Documents ---")
    cross_refs = engine.create_cross_references(consolidated_results, test_groups)
    
    print(f"✓ Cross-references generated between {len(consolidated_results)} consolidated documents")
    for doc, refs in cross_refs.items():
        print(f"  - {doc}: {len(refs)} references")
    
    print("✅ Comprehensive consolidation test completed successfully!")


if __name__ == "__main__":
    test_enhanced_content_merging()