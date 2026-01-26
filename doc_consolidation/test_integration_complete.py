"""
Integration tests for the complete Documentation Consolidation System.

This module tests the full integration of all components working together
through the main application interface.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from .main import DocumentationConsolidator
from .config import ConsolidationConfig
from .pipeline import DocumentationPipeline
from .config_manager import config_manager


class TestCompleteIntegration:
    """Test complete system integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.temp_dir) / "source"
        self.target_dir = Path(self.temp_dir) / "docs"
        self.backup_dir = Path(self.temp_dir) / "backup"
        
        # Create source directory with test files
        self.source_dir.mkdir(parents=True)
        self._create_test_files()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_files(self):
        """Create test markdown files."""
        test_files = {
            "README.md": "# Main README\nProject overview",
            "SETUP_GUIDE.md": "# Setup Guide\nInstallation instructions",
            "PAYMENT_COMPLETE.md": "# Payment Implementation Complete\nPayment system done",
            "TOURNAMENT_COMPLETE.md": "# Tournament Implementation Complete\nTournament system done",
            "TASK_1_COMPLETE.md": "# Task 1 Complete\nFirst task finished",
            "TASK_2_COMPLETE.md": "# Task 2 Complete\nSecond task finished",
            "QUICK_START.md": "# Quick Start\nGetting started guide",
            "API_INTEGRATION.md": "# API Integration\nAPI documentation",
            "test_results.md": "# Test Results\nTesting outcomes"
        }
        
        for filename, content in test_files.items():
            file_path = self.source_dir / filename
            file_path.write_text(content, encoding='utf-8')
    
    def test_configuration_manager_integration(self):
        """Test configuration manager integration."""
        # Test loading configuration with multiple sources
        config = config_manager.load_configuration(
            config_file=None,
            env_prefix="TEST_DOC_",
            cli_overrides={
                'source_directory': str(self.source_dir),
                'target_directory': str(self.target_dir),
                'backup_directory': str(self.backup_dir)
            }
        )
        
        assert config.source_directory == str(self.source_dir)
        assert config.target_directory == str(self.target_dir)
        assert config.backup_directory == str(self.backup_dir)
    
    def test_pipeline_integration(self):
        """Test pipeline integration with all components."""
        config = ConsolidationConfig(
            source_directory=str(self.source_dir),
            target_directory=str(self.target_dir),
            backup_directory=str(self.backup_dir),
            create_backups=False,  # Skip backup for test
            enable_consolidation=True
        )
        
        pipeline = DocumentationPipeline(config)
        
        # Mock progress callback
        progress_calls = []
        def progress_callback(step, total, message):
            progress_calls.append((step, total, message))
        
        # Run pipeline
        result = pipeline.run(progress_callback)
        
        # Verify result
        assert result.success
        assert result.files_processed > 0
        assert len(progress_calls) > 0
        
        # Verify target directory was created
        assert self.target_dir.exists()
        
        # Verify master index was created
        master_index = self.target_dir / "README.md"
        assert master_index.exists()
        
        # Verify some files were organized
        assert result.files_moved > 0
    
    def test_consolidator_integration(self):
        """Test main consolidator integration."""
        config = ConsolidationConfig(
            source_directory=str(self.source_dir),
            target_directory=str(self.target_dir),
            backup_directory=str(self.backup_dir),
            create_backups=False,  # Skip backup for test
            enable_consolidation=True
        )
        
        consolidator = DocumentationConsolidator(config, show_progress=False)
        
        # Run consolidation
        success = consolidator.run_consolidation()
        
        # Verify success
        assert success
        
        # Verify target directory structure
        assert self.target_dir.exists()
        assert (self.target_dir / "README.md").exists()
        
        # Verify some category directories were created
        expected_dirs = ["setup", "features", "implementation", "reference", "development"]
        created_dirs = [d.name for d in self.target_dir.iterdir() if d.is_dir()]
        
        # At least some directories should be created
        assert len(created_dirs) > 0
        
        # Get statistics
        stats = consolidator.get_statistics()
        assert stats['files_discovered'] > 0
        assert stats['files_analyzed'] > 0
    
    def test_error_handling_integration(self):
        """Test error handling across components."""
        # Test with non-existent source directory
        config = ConsolidationConfig(
            source_directory="/non/existent/path",
            target_directory=str(self.target_dir),
            backup_directory=str(self.backup_dir)
        )
        
        consolidator = DocumentationConsolidator(config, show_progress=False)
        
        # Should handle error gracefully
        success = consolidator.run_consolidation()
        assert not success
    
    def test_dry_run_integration(self):
        """Test dry run functionality integration."""
        # This would be tested through the CLI interface
        # For now, just verify the pipeline can be created
        config = ConsolidationConfig(
            source_directory=str(self.source_dir),
            target_directory=str(self.target_dir),
            backup_directory=str(self.backup_dir),
            create_backups=False
        )
        
        pipeline = DocumentationPipeline(config)
        
        # Verify pipeline components are initialized
        assert pipeline.analyzer is not None
        assert pipeline.engine is not None
        assert pipeline.generator is not None
        assert pipeline.filesystem is not None
    
    def test_configuration_validation_integration(self):
        """Test configuration validation integration."""
        # Test invalid configuration
        with pytest.raises(ValueError):
            config_manager.load_configuration(
                cli_overrides={
                    'source_directory': '/non/existent/path',
                    'max_file_size_mb': -1,  # Invalid value
                    'min_confidence_score': 2.0  # Invalid value
                }
            )
    
    def test_component_wiring(self):
        """Test that all components are properly wired together."""
        config = ConsolidationConfig(
            source_directory=str(self.source_dir),
            target_directory=str(self.target_dir),
            backup_directory=str(self.backup_dir)
        )
        
        # Test DocumentationConsolidator wiring
        consolidator = DocumentationConsolidator(config)
        assert consolidator.pipeline is not None
        assert consolidator.config is not None
        
        # Test DocumentationPipeline wiring
        pipeline = consolidator.pipeline
        assert pipeline.analyzer is not None
        assert pipeline.engine is not None
        assert pipeline.generator is not None
        assert pipeline.filesystem is not None
        assert pipeline.error_handler is not None
        assert pipeline.report_generator is not None
        
        # Verify all components have the same config
        assert pipeline.analyzer.config == config
        assert pipeline.engine.config == config
        assert pipeline.generator.config == config


if __name__ == '__main__':
    pytest.main([__file__])