#!/usr/bin/env python3
"""
Test core functionality of the Documentation Consolidation System.
"""

import sys
import os
from pathlib import Path

# Add the doc_consolidation directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'doc_consolidation'))

def test_models():
    """Test the data models."""
    try:
        from models import FileAnalysis, Category, ContentType, Priority, ContentMetadata
        
        # Create a test file analysis
        metadata = ContentMetadata(
            word_count=500,
            key_topics=['payment', 'testing'],
            internal_links=['setup.md'],
            author='test',
            creation_date=None,
            last_modified=None
        )
        
        analysis = FileAnalysis(
            filepath=Path('test.md'),
            filename='test.md',
            category=Category.FEATURE_DOCS,
            content_type=ContentType.FEATURE_GUIDE,
            preservation_priority=Priority.HIGH,
            metadata=metadata,
            is_outdated=False
        )
        
        print("✅ Models test passed")
        return True
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False

def test_config():
    """Test the configuration system."""
    try:
        from config import ConsolidationConfig, get_default_config
        
        config = get_default_config()
        assert config.root_directory == Path('.')
        assert config.output_directory == Path('docs')
        
        print("✅ Config test passed")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_filesystem():
    """Test the filesystem utilities."""
    try:
        from filesystem import FileSystem
        
        fs = FileSystem()
        
        # Test file discovery
        md_files = fs.discover_markdown_files(Path('.'))
        assert len(md_files) > 0
        
        print(f"✅ Filesystem test passed - found {len(md_files)} markdown files")
        return True
    except Exception as e:
        print(f"❌ Filesystem test failed: {e}")
        return False

def test_analyzer():
    """Test the content analyzer."""
    try:
        from analyzer import ContentAnalyzer
        from config import get_default_config
        
        config = get_default_config()
        analyzer = ContentAnalyzer(config)
        
        # Test with a simple markdown file
        test_content = """# Test Document
        
This is a test payment system document.
It contains information about payment processing.

## Setup
Installation instructions here.
"""
        
        # Create a temporary file for testing
        test_file = Path('test_doc.md')
        test_file.write_text(test_content)
        
        try:
            analysis = analyzer.analyze_file(test_file)
            assert analysis is not None
            assert analysis.filename == 'test_doc.md'
            
            print("✅ Analyzer test passed")
            return True
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
                
    except Exception as e:
        print(f"❌ Analyzer test failed: {e}")
        return False

def main():
    """Run core functionality tests."""
    print("🧪 Testing Documentation Consolidation System Core Functionality")
    print("=" * 70)
    print("")
    
    tests = [
        ("Models", test_models),
        ("Configuration", test_config),
        ("Filesystem", test_filesystem),
        ("Content Analyzer", test_analyzer),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        if test_func():
            passed += 1
        print("")
    
    print("=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core functionality tests passed!")
        print("")
        print("✅ The system is ready for full integration testing")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        print("")
        print("🔧 Please resolve the failing tests before proceeding")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)