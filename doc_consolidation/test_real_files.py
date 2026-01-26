#!/usr/bin/env python3
"""
Test the file analysis system with real project files.

This test validates that the file analysis system works correctly with
actual files from the project root directory.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from doc_consolidation.analyzer import ContentAnalyzer
from doc_consolidation.config import ConsolidationConfig
from doc_consolidation.models import Category


def test_real_files():
    """Test file analysis with real project files."""
    print("Testing File Analysis with Real Project Files")
    print("=" * 55)
    
    # Set up analyzer
    config = ConsolidationConfig()
    config.source_directory = "."
    analyzer = ContentAnalyzer(config)
    
    # Select a representative sample of real files to test
    test_files = [
        "TASK_1_COMPLETE_SUMMARY.md",
        "PAYMENT_SYSTEM_COMPLETE.md", 
        "AUTHENTICATION_SYSTEM_READY.md",
        "INSTALLATION_GUIDE.md",
        "REDIS_SETUP.md",
        "QUICK_START_INTEGRATION.md",
        "DEVELOPER_QUICK_START.md",
        "INTEGRATION_TESTS_IMPLEMENTATION_COMPLETE.md",
        "Complete_Summary.md",
        "PHASE_2_COMPLETE.md",
        "README.md"
    ]
    
    print(f"\nTesting {len(test_files)} real files:")
    print("-" * 40)
    
    successful_analyses = 0
    total_files = 0
    
    for filename in test_files:
        file_path = Path(".") / filename
        
        if not file_path.exists():
            print(f"⚠️  {filename}: File not found (skipping)")
            continue
        
        total_files += 1
        
        try:
            # Analyze the file
            analysis = analyzer.analyze_file(file_path)
            
            # Validate the analysis
            if (analysis.category != Category.UNCATEGORIZED or 
                analysis.confidence_score > 0.0):
                successful_analyses += 1
                status = "✅"
            else:
                status = "⚠️ "
            
            print(f"{status} {filename}:")
            print(f"    Category: {analysis.category.value}")
            print(f"    Content Type: {analysis.content_type.value}")
            print(f"    Confidence: {analysis.confidence_score:.2f}")
            print(f"    Priority: {analysis.preservation_priority.value}")
            print(f"    Word Count: {analysis.metadata.word_count}")
            print(f"    Headings: {len(analysis.metadata.headings)}")
            
            if analysis.processing_notes:
                print(f"    Notes: {'; '.join(analysis.processing_notes[:2])}")
            
            print()
            
        except Exception as e:
            print(f"❌ {filename}: Error during analysis - {e}")
            print()
    
    print("=" * 55)
    print(f"Results: {successful_analyses}/{total_files} files analyzed successfully")
    
    if successful_analyses == total_files:
        print("✅ ALL REAL FILES ANALYZED SUCCESSFULLY!")
        print("✅ The file analysis system is working correctly with real project data.")
    else:
        print(f"⚠️  {total_files - successful_analyses} files had issues")
    
    # Test consolidation group identification with real files
    print("\nTesting Consolidation Group Identification:")
    print("-" * 45)
    
    try:
        # Discover and analyze a larger set of files
        discovered_files = analyzer.discover_files(".")
        
        # Limit to first 20 files for performance
        sample_files = discovered_files[:20]
        analyses = []
        
        for file_path in sample_files:
            try:
                analysis = analyzer.analyze_file(file_path)
                analyses.append(analysis)
            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")
        
        # Identify consolidation groups
        groups = analyzer.identify_consolidation_candidates(analyses)
        
        print(f"✅ Analyzed {len(analyses)} files from project")
        print(f"✅ Identified {len(groups)} consolidation groups:")
        
        for group in groups:
            print(f"   - {group.group_id}: {group.primary_file} + {len(group.related_files)} related")
            print(f"     Strategy: {group.consolidation_strategy.value}")
            print(f"     Output: {group.output_filename}")
        
        if len(groups) == 0:
            print("   (No consolidation groups found - files are sufficiently distinct)")
        
    except Exception as e:
        print(f"❌ Error during consolidation group identification: {e}")
    
    print("\n" + "=" * 55)
    return successful_analyses == total_files


if __name__ == "__main__":
    success = test_real_files()
    sys.exit(0 if success else 1)