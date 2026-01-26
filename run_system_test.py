#!/usr/bin/env python3
"""
System test runner for Documentation Consolidation System.
This script runs the complete system test with actual project documentation.
"""

import sys
import os
from pathlib import Path

# Add the doc_consolidation directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'doc_consolidation'))

def run_system_test():
    """Run the complete system test."""
    try:
        # Import the main components
        from main import DocumentationConsolidator
        from config import get_default_config
        
        print("🚀 Starting Documentation Consolidation System Test")
        print("=" * 60)
        
        # Create configuration
        config = get_default_config()
        config.dry_run = True  # Don't actually modify files
        config.validate_output = True
        config.create_backups = True
        
        print(f"📁 Root directory: {config.root_directory}")
        print(f"📄 Dry run mode: {config.dry_run}")
        print(f"✅ Validation enabled: {config.validate_output}")
        print("")
        
        # Initialize consolidator
        consolidator = DocumentationConsolidator(config)
        
        # Run the consolidation process
        print("🔍 Phase 1: Analyzing existing documentation...")
        result = consolidator.run()
        
        if result.success:
            print("✅ System test completed successfully!")
            print("")
            print("📊 Results Summary:")
            print(f"  - Files processed: {result.files_processed}")
            print(f"  - Files consolidated: {result.files_consolidated}")
            print(f"  - Errors: {len(result.errors)}")
            print(f"  - Warnings: {len(result.warnings)}")
            
            if result.errors:
                print("")
                print("❌ Errors encountered:")
                for error in result.errors[:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(result.errors) > 5:
                    print(f"  ... and {len(result.errors) - 5} more errors")
            
            if result.warnings:
                print("")
                print("⚠️ Warnings:")
                for warning in result.warnings[:3]:  # Show first 3 warnings
                    print(f"  - {warning}")
                if len(result.warnings) > 3:
                    print(f"  ... and {len(result.warnings) - 3} more warnings")
            
            return True
        else:
            print("❌ System test failed!")
            print("")
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("The system may have import issues that need to be resolved.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_system_test()
    sys.exit(0 if success else 1)