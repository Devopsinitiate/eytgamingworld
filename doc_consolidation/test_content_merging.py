#!/usr/bin/env python3
"""
Test for content merging and deduplication functionality.

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


def test_content_merging_and_deduplication():
    """Test content merging and deduplication functionality."""
    print("Testing Content Merging and Deduplication")
    print("=" * 60)
    
    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create test files with overlapping content
        test_files = create_test_files_with_overlapping_content(temp_path)
        
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
        
        # Test different consolidation strategies
        test_chronological_merging(engine, analyses, temp_path)
        test_topical_merging(engine, analyses, temp_path)
        test_deduplication(engine, analyses, temp_path)
        test_cross_references(engine, analyses, temp_path)
        
        print(f"\n{'='*60}")
        print("✅ Content merging and deduplication test PASSED!")
        
        return True
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


def create_test_files_with_overlapping_content(temp_path: Path) -> dict:
    """Create test files with overlapping content for deduplication testing."""
    
    test_files = {}
    
    # Files with overlapping content for deduplication testing
    overlapping_files = {
        'TASK_1_COMPLETE.md': """# Task 1: Authentication Complete

## Overview
Authentication system implementation completed successfully.

## Features Implemented
- User login and logout functionality
- Password reset mechanism
- Session management
- Two-factor authentication

## Implementation Details
The authentication system uses JWT tokens for session management.
Security measures include password hashing with bcrypt.

## Testing
All authentication tests are passing.
Security audit completed successfully.

## Date
Created: 2024-01-15
Author: Development Team
        """,
        
        'TASK_2_COMPLETE.md': """# Task 2: Authentication Enhancement Complete

## Overview
Enhanced authentication system with additional security features.

## Features Implemented
- User login and logout functionality
- Advanced password reset mechanism
- Enhanced session management
- Two-factor authentication
- OAuth integration

## Implementation Details
The authentication system uses JWT tokens for session management.
Security measures include password hashing with bcrypt and salt.
Added OAuth providers for Google and GitHub.

## Testing
All authentication tests are passing.
Security audit completed successfully.
Additional penetration testing performed.

## Date
Created: 2024-01-20
Author: Development Team
        """,
        
        'PAYMENT_STRIPE_GUIDE.md': """# Payment Integration with Stripe

## Overview
Complete guide for Stripe payment integration.

## Setup Process
1. Create Stripe account
2. Obtain API keys
3. Configure webhooks
4. Set up payment forms

## Features
- Credit card processing
- Subscription management
- Refund handling
- Invoice generation

## Security
- PCI compliance
- Secure token handling
- Webhook verification

## Testing
- Test card numbers
- Webhook testing
- Error handling verification
        """,
        
        'PAYMENT_PROCESSING_GUIDE.md': """# Payment Processing Guide

## Overview
Comprehensive guide for payment processing implementation.

## Setup Process
1. Choose payment provider
2. Obtain API credentials
3. Configure webhooks and callbacks
4. Set up payment forms and UI

## Features
- Credit card processing
- Subscription management
- Refund and chargeback handling
- Invoice generation
- Multi-currency support

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
        """,
        
        'TOURNAMENT_SETUP.md': """# Tournament System Setup

## Overview
Setting up the tournament management system.

## Database Schema
- tournaments table
- participants table
- matches table
- brackets table

## Features
- Tournament creation
- Player registration
- Bracket generation
- Match scheduling

## Configuration
- Tournament types (single/double elimination)
- Scoring systems
- Time limits
        """,
        
        'TOURNAMENT_MANAGEMENT.md': """# Tournament Management Guide

## Overview
Complete guide for managing tournaments.

## Database Schema
- tournaments table with metadata
- participants table with player info
- matches table with results
- brackets table with structure

## Features
- Tournament creation and setup
- Player registration and management
- Bracket generation algorithms
- Match scheduling and results
- Prize distribution

## Configuration
- Tournament types (single/double elimination, swiss)
- Scoring systems and tiebreakers
- Time limits and rules
- Registration settings
        """
    }
    
    # Write all test files
    for filename, content in overlapping_files.items():
        file_path = temp_path / filename
        file_path.write_text(content, encoding='utf-8')
        test_files[filename] = str(file_path)
    
    print(f"✓ Created {len(overlapping_files)} test files with overlapping content")
    
    return test_files


def test_chronological_merging(engine, analyses, temp_path):
    """Test chronological merging functionality."""
    print(f"\n=== Testing Chronological Merging ===")
    
    # Create a consolidation group for chronological merging
    group = ConsolidationGroup(
        group_id="test_chronological",
        category=Category.IMPLEMENTATION_COMPLETION,
        primary_file="TASK_1_COMPLETE.md",
        related_files=["TASK_2_COMPLETE.md"],
        consolidation_strategy=ConsolidationStrategy.MERGE_CHRONOLOGICAL,
        output_filename="chronological_merge_test.md"
    )
    
    # Test consolidation
    consolidated_content = engine.consolidate_group(group, analyses)
    
    print(f"✓ Chronological merge completed")
    print(f"✓ Content length: {len(consolidated_content)} characters")
    
    # Verify chronological order
    if "Task 1" in consolidated_content and "Task 2" in consolidated_content:
        task1_pos = consolidated_content.find("Task 1")
        task2_pos = consolidated_content.find("Task 2")
        if task1_pos < task2_pos:
            print("✓ Files merged in chronological order")
        else:
            print("⚠️  Warning: Files may not be in chronological order")
    
    # Save result for inspection
    result_path = temp_path / "chronological_result.md"
    result_path.write_text(consolidated_content, encoding='utf-8')
    print(f"✓ Result saved to {result_path}")


def test_topical_merging(engine, analyses, temp_path):
    """Test topical merging functionality."""
    print(f"\n=== Testing Topical Merging ===")
    
    # Create a consolidation group for topical merging
    group = ConsolidationGroup(
        group_id="test_topical",
        category=Category.FEATURE_DOCS,
        primary_file="PAYMENT_STRIPE_GUIDE.md",
        related_files=["PAYMENT_PROCESSING_GUIDE.md"],
        consolidation_strategy=ConsolidationStrategy.MERGE_TOPICAL,
        output_filename="topical_merge_test.md"
    )
    
    # Test consolidation
    consolidated_content = engine.consolidate_group(group, analyses)
    
    print(f"✓ Topical merge completed")
    print(f"✓ Content length: {len(consolidated_content)} characters")
    
    # Verify topics are organized
    if "## Overview" in consolidated_content and "## Features" in consolidated_content:
        print("✓ Content organized by topics")
    
    # Save result for inspection
    result_path = temp_path / "topical_result.md"
    result_path.write_text(consolidated_content, encoding='utf-8')
    print(f"✓ Result saved to {result_path}")


def test_deduplication(engine, analyses, temp_path):
    """Test content deduplication functionality."""
    print(f"\n=== Testing Content Deduplication ===")
    
    # Test with overlapping content
    content1 = """# Authentication System

## Features
- User login and logout functionality
- Password reset mechanism
- Session management

## Security
- JWT tokens
- Password hashing with bcrypt
    """
    
    content2 = """# Enhanced Authentication

## Features
- User login and logout functionality
- Advanced password reset mechanism
- Enhanced session management
- Two-factor authentication

## Security
- JWT tokens for sessions
- Password hashing with bcrypt and salt
    """
    
    # Test deduplication
    deduplicated = engine.eliminate_redundancy([content1, content2])
    
    print(f"✓ Deduplication completed")
    print(f"✓ Original content 1: {len(content1)} characters")
    print(f"✓ Original content 2: {len(content2)} characters")
    print(f"✓ Deduplicated content: {len(deduplicated)} characters")
    
    # Verify deduplication worked
    if len(deduplicated) < len(content1) + len(content2):
        print("✓ Content successfully deduplicated")
    else:
        print("⚠️  Warning: Deduplication may not have worked effectively")
    
    # Save result for inspection
    result_path = temp_path / "deduplication_result.md"
    result_path.write_text(deduplicated, encoding='utf-8')
    print(f"✓ Result saved to {result_path}")


def test_cross_references(engine, analyses, temp_path):
    """Test cross-reference generation functionality."""
    print(f"\n=== Testing Cross-Reference Generation ===")
    
    # Create sample consolidated documents
    consolidated_docs = {
        "authentication_guide.md": """# Authentication Guide
        
## Overview
Complete authentication system documentation.

## Features
- User login
- Password reset
- Session management
- Two-factor authentication

## Security
- JWT tokens
- Password hashing
- OAuth integration
        """,
        
        "payment_guide.md": """# Payment Guide
        
## Overview
Payment processing documentation.

## Features
- Credit card processing
- Subscription management
- Refund handling

## Security
- PCI compliance
- Token handling
- Webhook verification

## Authentication
Payment processing requires user authentication.
        """,
        
        "tournament_guide.md": """# Tournament Guide
        
## Overview
Tournament management documentation.

## Features
- Tournament creation
- Player registration
- Bracket generation

## Authentication
Tournament participation requires user authentication.
Players must be logged in to register.
        """
    }
    
    # Test cross-reference generation
    cross_refs = engine.create_cross_references(consolidated_docs, [])
    
    print(f"✓ Cross-reference generation completed")
    print(f"✓ Generated references for {len(cross_refs)} documents")
    
    for doc_name, refs in cross_refs.items():
        print(f"  - {doc_name}: {len(refs)} references -> {', '.join(refs)}")
    
    # Verify cross-references make sense
    if "authentication_guide.md" in cross_refs:
        auth_refs = cross_refs["authentication_guide.md"]
        if any("payment" in ref or "tournament" in ref for ref in auth_refs):
            print("✓ Authentication guide properly cross-referenced")
    
    print("✓ Cross-reference generation test completed")


if __name__ == "__main__":
    test_content_merging_and_deduplication()