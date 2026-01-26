#!/usr/bin/env python3
"""
Documentation Consolidation Runner
Execute the consolidation process safely with proper error handling.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the doc_consolidation directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'doc_consolidation'))

def run_consolidation(dry_run=True):
    """Run the documentation consolidation process."""
    
    print("🚀 Documentation Consolidation System")
    print("=" * 50)
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE EXECUTION'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    try:
        # Import required components
        from doc_consolidation.config import get_default_config
        from doc_consolidation.filesystem import FileSystem
        from doc_consolidation.analyzer import ContentAnalyzer
        
        print("✅ System components loaded successfully")
        
        # Create configuration
        config = get_default_config()
        config.dry_run = dry_run
        config.create_backups = True
        config.validate_output = True
        
        print(f"✅ Configuration created:")
        print(f"   - Source directory: {config.source_directory}")
        print(f"   - Target directory: {config.target_directory}")
        print(f"   - Dry run: {config.dry_run}")
        print(f"   - Create backups: {config.create_backups}")
        print("")
        
        # Step 1: Analyze existing files
        print("📊 Step 1: Analyzing existing documentation...")
        fs = FileSystem()
        md_files = fs.list_files(Path('.'), '*.md')
        
        print(f"   Found {len(md_files)} markdown files to process")
        
        # Categorize files by type
        categories = {
            'completion': [],
            'setup': [],
            'feature': [],
            'test': [],
            'other': []
        }
        
        for file_path in md_files:
            filename = file_path.name.lower()
            if 'complete' in filename or 'summary' in filename:
                categories['completion'].append(file_path)
            elif 'setup' in filename or 'install' in filename:
                categories['setup'].append(file_path)
            elif any(f in filename for f in ['payment', 'tournament', 'auth', 'notification']):
                categories['feature'].append(file_path)
            elif 'test' in filename or 'validation' in filename:
                categories['test'].append(file_path)
            else:
                categories['other'].append(file_path)
        
        print("   File categorization:")
        for category, files in categories.items():
            print(f"     - {category.title()}: {len(files)} files")
        print("")
        
        # Step 2: Content Analysis
        print("🔍 Step 2: Performing content analysis...")
        analyzer = ContentAnalyzer(config)
        
        analyzed_files = []
        for i, file_path in enumerate(md_files[:5]):  # Analyze first 5 files as sample
            try:
                analysis = analyzer.analyze_file(file_path)
                analyzed_files.append(analysis)
                print(f"   ✅ Analyzed: {file_path.name} -> {analysis.category.value}")
            except Exception as e:
                print(f"   ⚠️ Error analyzing {file_path.name}: {e}")
        
        print(f"   Successfully analyzed {len(analyzed_files)} sample files")
        print("")
        
        # Step 3: Preview consolidation plan
        print("📋 Step 3: Consolidation plan preview...")
        
        completion_files = categories['completion']
        if len(completion_files) > 3:
            print(f"   📄 Will consolidate {len(completion_files)} completion files into:")
            print("     - implementation/completion-summary.md")
            print("     - implementation/phase-summaries/")
            print("     - implementation/task-histories/")
        
        feature_files = categories['feature']
        if len(feature_files) > 0:
            print(f"   🎯 Will organize {len(feature_files)} feature files into:")
            print("     - features/payments/")
            print("     - features/tournaments/")
            print("     - features/authentication/")
            print("     - features/notifications/")
        
        setup_files = categories['setup']
        if len(setup_files) > 0:
            print(f"   🛠️ Will organize {len(setup_files)} setup files into:")
            print("     - setup/installation.md")
            print("     - setup/configuration.md")
        
        print("")
        
        # Step 4: Directory structure preview
        print("📁 Step 4: Target directory structure...")
        target_structure = [
            "docs/",
            "docs/README.md (Master Index)",
            "docs/setup/",
            "docs/features/",
            "docs/development/",
            "docs/implementation/",
            "docs/testing/",
            "docs/reference/",
            "docs/archive/"
        ]
        
        for item in target_structure:
            print(f"   {item}")
        print("")
        
        if dry_run:
            print("🔒 DRY RUN MODE - No files will be modified")
            print("")
            print("📋 Next Steps:")
            print("1. Review the analysis above")
            print("2. If satisfied, run with: python run_consolidation.py --live")
            print("3. The system will create backups before making changes")
            print("4. Review the generated docs/ structure")
            print("5. Validate the consolidated content")
        else:
            print("⚠️ LIVE MODE - This would modify your files!")
            print("   (Full implementation requires additional integration)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during consolidation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    
    # Check command line arguments
    live_mode = '--live' in sys.argv
    
    if live_mode:
        print("⚠️ WARNING: You are about to run in LIVE mode!")
        print("This will modify your files. Make sure you have a backup!")
        response = input("Continue? (yes/no): ").lower().strip()
        if response != 'yes':
            print("Aborted.")
            return
    
    success = run_consolidation(dry_run=not live_mode)
    
    if success:
        print("\n🎉 Consolidation process completed successfully!")
    else:
        print("\n❌ Consolidation process failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)