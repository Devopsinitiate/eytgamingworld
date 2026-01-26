"""
Basic tests for the Documentation Consolidation System.

This module contains simple tests to verify that the core components
are working correctly and can be imported and instantiated.
"""

import tempfile
import unittest
from pathlib import Path

from .analyzer import ContentAnalyzer
from .engine import ConsolidationEngine
from .generator import StructureGenerator
from .models import (
    FileAnalysis, ConsolidationGroup, DocumentationStructure,
    Category, ContentType, Priority, ContentMetadata
)
from .config import ConsolidationConfig, get_default_config
from .filesystem import FileSystem


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality of the documentation consolidation system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = get_default_config()
        self.temp_dir = tempfile.mkdtemp()
        self.config.source_directory = self.temp_dir
        self.config.target_directory = f"{self.temp_dir}/docs"
        self.config.backup_directory = f"{self.temp_dir}/backup"
    
    def test_config_creation(self):
        """Test that configuration can be created and validated."""
        config = get_default_config()
        self.assertIsInstance(config, ConsolidationConfig)
        
        # Test validation with non-existent directory
        config.source_directory = "/non/existent/directory"
        errors = config.validate()
        # Should have at least one error since source directory doesn't exist
        self.assertGreater(len(errors), 0)
    
    def test_component_initialization(self):
        """Test that all components can be initialized."""
        analyzer = ContentAnalyzer(self.config)
        self.assertIsInstance(analyzer, ContentAnalyzer)
        
        engine = ConsolidationEngine(self.config)
        self.assertIsInstance(engine, ConsolidationEngine)
        
        generator = StructureGenerator(self.config)
        self.assertIsInstance(generator, StructureGenerator)
        
        filesystem = FileSystem()
        self.assertIsInstance(filesystem, FileSystem)
    
    def test_data_models(self):
        """Test that data models can be created and used."""
        # Test ContentMetadata
        metadata = ContentMetadata()
        self.assertEqual(metadata.word_count, 0)
        self.assertEqual(len(metadata.key_topics), 0)
        
        # Test FileAnalysis
        test_path = Path(self.temp_dir) / "test.md"
        analysis = FileAnalysis(
            filepath=test_path,
            filename="test.md",
            category=Category.FEATURE_DOCS,
            content_type=ContentType.FEATURE_GUIDE,
            metadata=metadata,
            preservation_priority=Priority.HIGH
        )
        
        self.assertEqual(analysis.filename, "test.md")
        self.assertEqual(analysis.category, Category.FEATURE_DOCS)
        self.assertEqual(analysis.preservation_priority, Priority.HIGH)
        
        # Test ConsolidationGroup
        group = ConsolidationGroup(
            group_id="test_group",
            category=Category.FEATURE_DOCS,
            primary_file="primary.md",
            related_files=["related1.md", "related2.md"],
            output_filename="consolidated.md"
        )
        
        self.assertEqual(group.total_files, 3)  # 1 primary + 2 related
        
        # Test DocumentationStructure
        structure = DocumentationStructure()
        self.assertEqual(structure.root_path, "docs/")
        self.assertIn(Category.SETUP_CONFIG, structure.categories)
        
        # Test getting category path
        setup_path = structure.get_category_path(Category.SETUP_CONFIG)
        self.assertEqual(setup_path, "docs/setup")
    
    def test_file_discovery(self):
        """Test file discovery functionality."""
        # Create test files
        test_files = [
            "README.md",
            "SETUP_GUIDE.md",
            "PAYMENT_COMPLETE.md",
            "test_file.txt"  # Should be ignored
        ]
        
        temp_path = Path(self.temp_dir)
        for filename in test_files:
            test_file = temp_path / filename
            test_file.write_text(f"# {filename}\n\nTest content for {filename}")
        
        # Test discovery
        analyzer = ContentAnalyzer(self.config)
        discovered = analyzer.discover_files(self.temp_dir)
        
        # Should find only .md files
        discovered_names = [f.name for f in discovered]
        self.assertIn("README.md", discovered_names)
        self.assertIn("SETUP_GUIDE.md", discovered_names)
        self.assertIn("PAYMENT_COMPLETE.md", discovered_names)
        self.assertNotIn("test_file.txt", discovered_names)
    
    def test_file_classification(self):
        """Test file classification by pattern."""
        analyzer = ContentAnalyzer(self.config)
        
        # Test setup file classification
        category, confidence = analyzer.classify_by_pattern("INSTALLATION_SETUP.md")
        self.assertEqual(category, Category.SETUP_CONFIG)
        self.assertGreater(confidence, 0.5)
        
        # Test completion file classification
        category, confidence = analyzer.classify_by_pattern("TASK_1_COMPLETE.md")
        self.assertEqual(category, Category.IMPLEMENTATION_COMPLETION)
        self.assertGreater(confidence, 0.5)
        
        # Test payment file classification
        category, confidence = analyzer.classify_by_pattern("PAYMENT_SYSTEM_GUIDE.md")
        self.assertEqual(category, Category.FEATURE_DOCS)
        self.assertGreater(confidence, 0.5)
        
        # Test unknown file
        category, confidence = analyzer.classify_by_pattern("unknown_file.md")
        self.assertEqual(category, Category.UNCATEGORIZED)
    
    def test_content_metadata_extraction(self):
        """Test content metadata extraction."""
        analyzer = ContentAnalyzer(self.config)
        
        test_content = """# Test Document

This is a test document with various elements.

## Section 1

Some content here with a [link](other.md).

- Bullet point 1
- Bullet point 2

## Section 2

More content with an external [link](https://example.com).

```python
def test_function():
    return "test"
```

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

![Image](image.png)
"""
        
        metadata = analyzer.extract_content_metadata(test_content)
        
        self.assertGreater(metadata.word_count, 0)
        self.assertEqual(len(metadata.headings), 3)  # Main title + 2 sections
        self.assertEqual(metadata.code_blocks, 1)
        self.assertTrue(metadata.has_tables)
        self.assertTrue(metadata.has_images)
        self.assertGreaterEqual(len(metadata.internal_links), 1)  # At least 1 internal link
        self.assertEqual(len(metadata.external_links), 1)
    
    def test_directory_structure_creation(self):
        """Test directory structure creation."""
        generator = StructureGenerator(self.config)
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        
        success = generator.create_directory_structure(structure)
        self.assertTrue(success)
        
        # Check that directories were created
        root_path = Path(structure.root_path)
        self.assertTrue(root_path.exists())
        
        # Check category directories
        for category, config in structure.categories.items():
            category_path = root_path / config.path
            self.assertTrue(category_path.exists(), f"Category directory missing: {category_path}")
    
    def test_filesystem_operations(self):
        """Test basic filesystem operations."""
        filesystem = FileSystem()
        
        # Test file writing and reading
        test_file = Path(self.temp_dir) / "test_write.md"
        test_content = "# Test Content\n\nThis is a test file."
        
        success = filesystem.write_file(test_file, test_content)
        self.assertTrue(success)
        self.assertTrue(filesystem.file_exists(test_file))
        
        read_content = filesystem.read_file(test_file)
        self.assertEqual(read_content, test_content)
        
        # Test file stats
        stats = filesystem.get_file_stats(test_file)
        self.assertIn('size', stats)
        self.assertIn('modified', stats)
        self.assertGreater(stats['size'], 0)
        
        # Test directory creation
        test_dir = Path(self.temp_dir) / "test_subdir"
        success = filesystem.create_directory(test_dir)
        self.assertTrue(success)
        self.assertTrue(test_dir.exists())
        
        # Test file listing
        files = filesystem.list_files(Path(self.temp_dir), "*.md")
        self.assertGreater(len(files), 0)


if __name__ == '__main__':
    unittest.main()