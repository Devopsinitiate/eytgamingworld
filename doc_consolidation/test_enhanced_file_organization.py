"""
Test suite for enhanced file organization and placement functionality.

This module tests the enhanced organize_files method and supporting functions
that handle file naming conflicts, duplicates, and maintain file integrity during moves.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

# Add the parent directory to the path to enable imports
sys.path.insert(0, str(Path(__file__).parent))

from generator import StructureGenerator
from models import (
    FileAnalysis, DocumentationStructure, Category, ContentType, 
    ContentMetadata, Priority, DirectoryConfig
)
from config import ConsolidationConfig


def test_organize_files_with_conflicts():
    """Test file organization with naming conflicts."""
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        docs_dir = temp_path / "docs"
        
        source_dir.mkdir()
        
        # Create test files with potential conflicts
        test_files = [
            "PAYMENT_SETUP.md",
            "payment_setup.md",  # Potential conflict (case difference)
            "TOURNAMENT_GUIDE.md",
            "tournament_guide.md",  # Another potential conflict
            "TEST_REPORT.md"
        ]
        
        file_analyses = []
        for filename in test_files:
            file_path = source_dir / filename
            file_path.write_text(f"# {filename}\n\nContent for {filename}")
            
            # Create FileAnalysis
            metadata = ContentMetadata(
                word_count=10,
                key_topics=[filename.split('_')[0].lower()]
            )
            
            if 'payment' in filename.lower():
                category = Category.FEATURE_DOCS
                content_type = ContentType.FEATURE_GUIDE
            elif 'tournament' in filename.lower():
                category = Category.FEATURE_DOCS
                content_type = ContentType.FEATURE_GUIDE
            elif 'test' in filename.lower():
                category = Category.TESTING_VALIDATION
                content_type = ContentType.TEST_REPORT
            else:
                category = Category.UNCATEGORIZED
                content_type = ContentType.GENERAL_DOC
            
            analysis = FileAnalysis(
                filepath=file_path,
                filename=filename,
                category=category,
                content_type=content_type,
                metadata=metadata
            )
            file_analyses.append(analysis)
        
        # Create configuration and generator
        config = ConsolidationConfig()
        generator = StructureGenerator(config)
        
        # Create documentation structure
        structure = DocumentationStructure(root_path=str(docs_dir))
        
        # Create directory structure first
        assert generator.create_directory_structure(structure)
        
        # Test file organization
        consolidated_docs = {}  # No consolidated docs for this test
        file_moves = generator.organize_files(file_analyses, consolidated_docs, structure)
        
        # Verify results
        assert len(file_moves) == len(test_files)
        
        # Check that conflicts were resolved
        moved_files = list(file_moves.values())
        unique_filenames = set(Path(f).name for f in moved_files)
        
        # Should have unique filenames after conflict resolution
        assert len(unique_filenames) == len(moved_files)
        
        # Verify files exist at target locations
        for target_path in file_moves.values():
            assert Path(target_path).exists()
            
        print("✓ File organization with conflicts test passed")


def test_file_integrity_during_moves():
    """Test that file integrity is maintained during moves."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        docs_dir = temp_path / "docs"
        
        source_dir.mkdir()
        
        # Create test file with specific content
        test_content = """# Test Document

This is a test document with specific content that should be preserved.

## Section 1
Content in section 1.

## Section 2
Content in section 2 with special characters: àáâãäå

```python
def test_function():
    return "test"
```

- List item 1
- List item 2
- List item 3
"""
        
        test_file = source_dir / "TEST_INTEGRITY.md"
        test_file.write_text(test_content, encoding='utf-8')
        
        # Create FileAnalysis
        metadata = ContentMetadata(
            word_count=50,
            key_topics=['test', 'integrity'],
            code_blocks=1,
            headings=['Test Document', 'Section 1', 'Section 2']
        )
        
        analysis = FileAnalysis(
            filepath=test_file,
            filename="TEST_INTEGRITY.md",
            category=Category.TESTING_VALIDATION,
            content_type=ContentType.TEST_REPORT,
            metadata=metadata
        )
        
        # Create configuration and generator
        config = ConsolidationConfig()
        generator = StructureGenerator(config)
        
        # Create documentation structure
        structure = DocumentationStructure(root_path=str(docs_dir))
        
        # Create directory structure first
        assert generator.create_directory_structure(structure)
        
        # Test file organization
        file_moves = generator.organize_files([analysis], {}, structure)
        
        # Verify file was moved
        assert len(file_moves) == 1
        target_path = Path(list(file_moves.values())[0])
        assert target_path.exists()
        
        # Verify content integrity
        moved_content = target_path.read_text(encoding='utf-8')
        assert moved_content == test_content
        
        print("✓ File integrity during moves test passed")


def test_subdirectory_placement_logic():
    """Test enhanced subdirectory placement logic."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        docs_dir = temp_path / "docs"
        
        source_dir.mkdir()
        
        # Create test files for different subdirectory scenarios
        test_cases = [
            ("PAYMENT_API_GUIDE.md", Category.FEATURE_DOCS, "features/payments"),
            ("TOURNAMENT_SETUP.md", Category.FEATURE_DOCS, "features/tournaments"),
            ("AUTH_INTEGRATION.md", Category.FEATURE_DOCS, "features/authentication"),
            ("TEST_REPORT_VALIDATION.md", Category.TESTING_VALIDATION, "testing/test-reports"),
            ("VALIDATION_RESULTS.md", Category.TESTING_VALIDATION, "testing/validation-results"),
            ("TASK_COMPLETE_SUMMARY.md", Category.IMPLEMENTATION_COMPLETION, "implementation/completion-summaries"),
            ("PHASE_1_SUMMARY.md", Category.IMPLEMENTATION_COMPLETION, "implementation/phase-summaries"),
            ("QUICK_REFERENCE.md", Category.QUICK_REFERENCES, "reference"),
        ]
        
        file_analyses = []
        for filename, category, expected_path in test_cases:
            file_path = source_dir / filename
            file_path.write_text(f"# {filename}\n\nContent for {filename}")
            
            # Determine content type based on filename
            if 'test' in filename.lower() or 'report' in filename.lower():
                content_type = ContentType.TEST_REPORT
            elif 'complete' in filename.lower() or 'summary' in filename.lower():
                content_type = ContentType.COMPLETION_SUMMARY
            elif 'quick' in filename.lower() or 'reference' in filename.lower():
                content_type = ContentType.QUICK_REFERENCE
            else:
                content_type = ContentType.FEATURE_GUIDE
            
            metadata = ContentMetadata(word_count=10)
            
            analysis = FileAnalysis(
                filepath=file_path,
                filename=filename,
                category=category,
                content_type=content_type,
                metadata=metadata
            )
            file_analyses.append(analysis)
        
        # Create configuration and generator
        config = ConsolidationConfig()
        generator = StructureGenerator(config)
        
        # Create documentation structure
        structure = DocumentationStructure(root_path=str(docs_dir))
        
        # Create directory structure first
        assert generator.create_directory_structure(structure)
        
        # Test file organization
        file_moves = generator.organize_files(file_analyses, {}, structure)
        
        # Verify subdirectory placement
        for i, (filename, category, expected_path) in enumerate(test_cases):
            source_path = str(source_dir / filename)
            target_path = file_moves.get(source_path)
            
            assert target_path is not None, f"File {filename} was not moved"
            
            # Check that file is in expected directory
            relative_path = Path(target_path).relative_to(docs_dir)
            expected_relative = Path(expected_path) / filename
            
            assert str(relative_path) == str(expected_relative), \
                f"File {filename} placed in {relative_path}, expected {expected_relative}"
        
        print("✓ Subdirectory placement logic test passed")


def test_consolidated_file_organization():
    """Test organization of consolidated documents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        docs_dir = temp_path / "docs"
        
        # Create consolidated documents
        consolidated_docs = {
            "payment_system_guide.md": "# Payment System Guide\n\nConsolidated payment documentation.",
            "tournament_management.md": "# Tournament Management\n\nConsolidated tournament documentation.",
            "testing_procedures.md": "# Testing Procedures\n\nConsolidated testing documentation.",
            "implementation_summary.md": "# Implementation Summary\n\nConsolidated implementation documentation."
        }
        
        # Create configuration and generator
        config = ConsolidationConfig()
        generator = StructureGenerator(config)
        
        # Create documentation structure
        structure = DocumentationStructure(root_path=str(docs_dir))
        
        # Create directory structure first
        assert generator.create_directory_structure(structure)
        
        # Test file organization with consolidated docs
        file_moves = generator.organize_files([], consolidated_docs, structure)
        
        # Verify consolidated files were placed correctly
        expected_placements = {
            "payment_system_guide.md": "features/payments",
            "tournament_management.md": "features/tournaments", 
            "testing_procedures.md": "testing",
            "implementation_summary.md": "implementation"
        }
        
        for filename, expected_dir in expected_placements.items():
            consolidated_key = f"consolidated_{filename}"
            target_path = file_moves.get(consolidated_key)
            
            assert target_path is not None, f"Consolidated file {filename} was not placed"
            
            # Verify file exists and is in correct directory
            target_file = Path(target_path)
            assert target_file.exists()
            
            relative_path = target_file.relative_to(docs_dir)
            assert str(relative_path).startswith(expected_dir), \
                f"Consolidated file {filename} placed in wrong directory: {relative_path}"
            
            # Verify content integrity
            content = target_file.read_text()
            assert content == consolidated_docs[filename]
        
        print("✓ Consolidated file organization test passed")


def test_filename_conflict_resolution():
    """Test filename conflict resolution with various scenarios."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        target_dir = temp_path / "target"
        target_dir.mkdir()
        
        # Create configuration and generator
        config = ConsolidationConfig()
        generator = StructureGenerator(config)
        
        # Test basic conflict resolution
        used_filenames = {"test.md"}
        resolved = generator._resolve_filename_conflict("test.md", target_dir, used_filenames)
        assert resolved == "test_001.md"
        
        # Test with existing file in directory
        existing_file = target_dir / "existing.md"
        existing_file.write_text("existing content")
        
        resolved = generator._resolve_filename_conflict("existing.md", target_dir, set())
        assert resolved == "existing_001.md"
        
        # Test with multiple conflicts
        used_filenames = {"conflict.md", "conflict_001.md", "conflict_002.md"}
        resolved = generator._resolve_filename_conflict("conflict.md", target_dir, used_filenames)
        assert resolved == "conflict_003.md"
        
        # Test with file without extension
        resolved = generator._resolve_filename_conflict("README", target_dir, {"README"})
        assert resolved == "README_001"
        
        print("✓ Filename conflict resolution test passed")


def run_all_tests():
    """Run all enhanced file organization tests."""
    print("Running enhanced file organization tests...")
    
    test_organize_files_with_conflicts()
    test_file_integrity_during_moves()
    test_subdirectory_placement_logic()
    test_consolidated_file_organization()
    test_filename_conflict_resolution()
    
    print("✅ All enhanced file organization tests passed!")


if __name__ == "__main__":
    run_all_tests()