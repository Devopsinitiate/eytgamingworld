"""
Comprehensive tests for directory structure generation functionality.

This module tests the enhanced directory structure creation capabilities
of the StructureGenerator class, validating Requirements 1.1 and 1.3.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from .config import ConsolidationConfig
from .generator import StructureGenerator
from .models import (
    DocumentationStructure, DirectoryConfig, ArchiveConfig, IndexConfig,
    Category
)


class TestDirectoryStructureGeneration(unittest.TestCase):
    """Test enhanced directory structure generation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = ConsolidationConfig(
            source_directory=self.temp_dir,
            target_directory=f"{self.temp_dir}/docs",
            create_backups=False
        )
        self.generator = StructureGenerator(self.config)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_basic_directory_structure_creation(self):
        """Test basic directory structure creation with default configuration."""
        # Create structure with default configuration
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        
        # Create directory structure
        success = self.generator.create_directory_structure(structure)
        self.assertTrue(success, "Directory structure creation should succeed")
        
        # Verify root directory exists
        root_path = Path(structure.root_path)
        self.assertTrue(root_path.exists(), "Root directory should exist")
        self.assertTrue(root_path.is_dir(), "Root path should be a directory")
        
        # Verify all category directories exist
        for category, config in structure.categories.items():
            category_path = root_path / config.path
            self.assertTrue(category_path.exists(), 
                          f"Category directory should exist: {category_path}")
            self.assertTrue(category_path.is_dir(), 
                          f"Category path should be a directory: {category_path}")
        
        # Verify archive directory exists
        archive_path = root_path / structure.archive_section.path
        self.assertTrue(archive_path.exists(), "Archive directory should exist")
        self.assertTrue(archive_path.is_dir(), "Archive path should be a directory")
    
    def test_subdirectory_creation(self):
        """Test creation of subdirectories within category directories."""
        # Create structure with subdirectories
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        
        # Ensure some categories have subdirectories
        structure.categories[Category.FEATURE_DOCS].subdirectories = [
            "authentication", "payments", "tournaments"
        ]
        structure.categories[Category.TESTING_VALIDATION].subdirectories = [
            "test-reports", "validation-results"
        ]
        
        # Create directory structure
        success = self.generator.create_directory_structure(structure)
        self.assertTrue(success, "Directory structure creation should succeed")
        
        # Verify subdirectories exist
        root_path = Path(structure.root_path)
        
        # Check feature subdirectories
        features_path = root_path / "features"
        for subdir in ["authentication", "payments", "tournaments"]:
            subdir_path = features_path / subdir
            self.assertTrue(subdir_path.exists(), 
                          f"Feature subdirectory should exist: {subdir_path}")
            self.assertTrue(subdir_path.is_dir(), 
                          f"Feature subdirectory should be a directory: {subdir_path}")
        
        # Check testing subdirectories
        testing_path = root_path / "testing"
        for subdir in ["test-reports", "validation-results"]:
            subdir_path = testing_path / subdir
            self.assertTrue(subdir_path.exists(), 
                          f"Testing subdirectory should exist: {subdir_path}")
            self.assertTrue(subdir_path.is_dir(), 
                          f"Testing subdirectory should be a directory: {subdir_path}")
    
    def test_archive_directory_with_deprecated(self):
        """Test archive directory creation with deprecated subdirectory."""
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        structure.archive_section.include_deprecated = True
        
        success = self.generator.create_directory_structure(structure)
        self.assertTrue(success, "Directory structure creation should succeed")
        
        # Verify archive and deprecated directories
        root_path = Path(structure.root_path)
        archive_path = root_path / "archive"
        deprecated_path = archive_path / "deprecated"
        
        self.assertTrue(archive_path.exists(), "Archive directory should exist")
        self.assertTrue(deprecated_path.exists(), "Deprecated directory should exist")
        self.assertTrue(deprecated_path.is_dir(), "Deprecated path should be a directory")
    
    def test_archive_directory_without_deprecated(self):
        """Test archive directory creation without deprecated subdirectory."""
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        structure.archive_section.include_deprecated = False
        
        success = self.generator.create_directory_structure(structure)
        self.assertTrue(success, "Directory structure creation should succeed")
        
        # Verify archive exists but deprecated does not
        root_path = Path(structure.root_path)
        archive_path = root_path / "archive"
        deprecated_path = archive_path / "deprecated"
        
        self.assertTrue(archive_path.exists(), "Archive directory should exist")
        self.assertFalse(deprecated_path.exists(), "Deprecated directory should not exist")
    
    def test_custom_directory_structure(self):
        """Test creation of custom directory structure."""
        # Create custom structure
        custom_categories = {
            Category.SETUP_CONFIG: DirectoryConfig(
                path="installation",
                description="Installation guides",
                subdirectories=["quick-start", "advanced"]
            ),
            Category.FEATURE_DOCS: DirectoryConfig(
                path="components",
                description="Component documentation",
                subdirectories=["core", "plugins", "extensions"]
            )
        }
        
        structure = DocumentationStructure(
            root_path=f"{self.temp_dir}/custom_docs/",
            categories=custom_categories
        )
        
        success = self.generator.create_directory_structure(structure)
        self.assertTrue(success, "Custom directory structure creation should succeed")
        
        # Verify custom directories
        root_path = Path(structure.root_path)
        
        # Check installation directory and subdirectories
        install_path = root_path / "installation"
        self.assertTrue(install_path.exists(), "Installation directory should exist")
        
        for subdir in ["quick-start", "advanced"]:
            subdir_path = install_path / subdir
            self.assertTrue(subdir_path.exists(), 
                          f"Installation subdirectory should exist: {subdir_path}")
        
        # Check components directory and subdirectories
        components_path = root_path / "components"
        self.assertTrue(components_path.exists(), "Components directory should exist")
        
        for subdir in ["core", "plugins", "extensions"]:
            subdir_path = components_path / subdir
            self.assertTrue(subdir_path.exists(), 
                          f"Components subdirectory should exist: {subdir_path}")
    
    def test_directory_structure_validation(self):
        """Test validation of directory structure configuration."""
        # Test with invalid configuration
        invalid_structure = DocumentationStructure(
            root_path="",  # Empty root path should fail validation
            categories={}  # Empty categories should fail validation
        )
        
        success = self.generator.create_directory_structure(invalid_structure)
        self.assertFalse(success, "Invalid structure should fail creation")
    
    def test_duplicate_path_validation(self):
        """Test validation catches duplicate directory paths."""
        # Create structure with duplicate paths
        duplicate_categories = {
            Category.SETUP_CONFIG: DirectoryConfig(
                path="docs",
                description="Setup docs"
            ),
            Category.FEATURE_DOCS: DirectoryConfig(
                path="docs",  # Duplicate path
                description="Feature docs"
            )
        }
        
        structure = DocumentationStructure(
            root_path=f"{self.temp_dir}/test_docs/",
            categories=duplicate_categories
        )
        
        success = self.generator.create_directory_structure(structure)
        self.assertFalse(success, "Duplicate paths should fail validation")
    
    def test_permission_error_handling(self):
        """Test handling of permission errors during directory creation."""
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        
        # Mock mkdir to raise PermissionError
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
            success = self.generator.create_directory_structure(structure)
            self.assertFalse(success, "Permission error should cause failure")
    
    def test_os_error_handling(self):
        """Test handling of OS errors during directory creation."""
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        
        # Mock mkdir to raise OSError
        with patch('pathlib.Path.mkdir', side_effect=OSError("Disk full")):
            success = self.generator.create_directory_structure(structure)
            self.assertFalse(success, "OS error should cause failure")
    
    def test_directory_verification(self):
        """Test directory structure verification after creation."""
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        
        # Create structure successfully
        success = self.generator.create_directory_structure(structure)
        self.assertTrue(success, "Directory structure creation should succeed")
        
        # Test verification method directly
        verification_result = self.generator._verify_directory_structure(structure)
        self.assertTrue(verification_result, "Directory structure verification should pass")
        
        # Remove a directory and test verification failure
        root_path = Path(structure.root_path)
        setup_path = root_path / "setup"
        if setup_path.exists():
            setup_path.rmdir()
        
        verification_result = self.generator._verify_directory_structure(structure)
        self.assertFalse(verification_result, "Directory structure verification should fail")
    
    def test_requirements_compliance(self):
        """Test that directory structure meets Requirements 1.1 and 1.3."""
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        
        success = self.generator.create_directory_structure(structure)
        self.assertTrue(success, "Directory structure creation should succeed")
        
        root_path = Path(structure.root_path)
        
        # Requirement 1.1: Hierarchical folder structure under docs/ with logical categories
        self.assertTrue(root_path.exists(), "Root docs/ directory should exist")
        
        # Check that logical categories exist
        expected_categories = ["setup", "features", "development", "testing", 
                             "reference", "implementation", "archive"]
        
        for category_name in expected_categories:
            category_path = root_path / category_name
            self.assertTrue(category_path.exists(), 
                          f"Logical category directory should exist: {category_name}")
        
        # Requirement 1.3: Separate directories for setup, features, testing, 
        # implementation, and reference materials
        required_dirs = ["setup", "features", "testing", "implementation", "reference"]
        
        for required_dir in required_dirs:
            dir_path = root_path / required_dir
            self.assertTrue(dir_path.exists(), 
                          f"Required directory should exist: {required_dir}")
            self.assertTrue(dir_path.is_dir(), 
                          f"Required path should be a directory: {required_dir}")
    
    def test_django_conventions_compliance(self):
        """Test that directory structure follows Django documentation conventions."""
        # Set Django conventions flag
        self.config.follow_django_conventions = True
        generator = StructureGenerator(self.config)
        
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        
        success = generator.create_directory_structure(structure)
        self.assertTrue(success, "Directory structure creation should succeed")
        
        # Verify Django-style directory names and structure
        root_path = Path(structure.root_path)
        
        # Django projects typically have these documentation sections
        django_style_dirs = ["setup", "features", "development", "reference"]
        
        for django_dir in django_style_dirs:
            dir_path = root_path / django_dir
            self.assertTrue(dir_path.exists(), 
                          f"Django-style directory should exist: {django_dir}")
    
    def test_logging_during_creation(self):
        """Test that appropriate logging occurs during directory creation."""
        structure = DocumentationStructure(root_path=f"{self.temp_dir}/test_docs/")
        
        # Capture log messages
        with patch.object(self.generator.logger, 'info') as mock_info, \
             patch.object(self.generator.logger, 'debug') as mock_debug:
            
            success = self.generator.create_directory_structure(structure)
            self.assertTrue(success, "Directory structure creation should succeed")
            
            # Verify logging calls were made
            mock_info.assert_called()
            mock_debug.assert_called()
            
            # Check for specific log messages
            info_calls = [call[0][0] for call in mock_info.call_args_list]
            self.assertTrue(any("Creating directory structure" in msg for msg in info_calls),
                          "Should log directory structure creation start")
            self.assertTrue(any("created successfully" in msg for msg in info_calls),
                          "Should log successful completion")


if __name__ == '__main__':
    unittest.main()