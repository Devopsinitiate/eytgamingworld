"""
Integration test for Task 6.2: Archive section creation.

This test demonstrates the complete archive section creation functionality
including directory structure creation, file movement, and freshness indicators.
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from .archive_manager import ArchiveManager
from .models import (
    DocumentationStructure, ArchiveConfig, FileAnalysis, ContentMetadata,
    Category, ContentType, Priority, MigrationLog
)


class TestTask6_2Integration:
    """Integration test for Task 6.2 archive section creation."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_documentation_files(self, temp_workspace):
        """Create sample documentation files for testing."""
        files = []
        
        # Create various types of documentation files
        file_specs = [
            # (filename, content, category, content_type, priority, days_old)
            ("OLD_PAYMENT_GUIDE.md", "# Old Payment Guide\n\nThis is outdated payment documentation.", 
             Category.FEATURE_DOCS, ContentType.FEATURE_GUIDE, Priority.ARCHIVE, 500),
            
            ("DEPRECATED_SETUP.md", "# Deprecated Setup\n\nOld setup instructions.", 
             Category.SETUP_CONFIG, ContentType.SETUP_PROCEDURE, Priority.ARCHIVE, 300),
            
            ("LEGACY_TEST_REPORT.md", "# Legacy Test Report\n\nOld test results.", 
             Category.TESTING_VALIDATION, ContentType.TEST_REPORT, Priority.ARCHIVE, 200),
            
            ("CURRENT_FEATURE.md", "# Current Feature\n\nUp-to-date feature documentation.", 
             Category.FEATURE_DOCS, ContentType.FEATURE_GUIDE, Priority.HIGH, 10),
            
            ("AGING_INTEGRATION.md", "# Aging Integration Guide\n\nSomewhat old integration guide.", 
             Category.INTEGRATION_GUIDES, ContentType.INTEGRATION_GUIDE, Priority.MEDIUM, 120),
        ]
        
        for filename, content, category, content_type, priority, days_old in file_specs:
            file_path = temp_workspace / filename
            file_path.write_text(content, encoding='utf-8')
            
            metadata = ContentMetadata(
                last_modified=datetime.now() - timedelta(days=days_old),
                word_count=len(content.split()),
                key_topics=["test", "sample", filename.lower().split('_')[0]]
            )
            
            analysis = FileAnalysis(
                filepath=file_path,
                filename=filename,
                category=category,
                content_type=content_type,
                metadata=metadata,
                preservation_priority=priority
            )
            
            if priority == Priority.ARCHIVE:
                analysis.processing_notes.append(f"Archive candidate: Old content ({days_old} days)")
            
            files.append(analysis)
        
        return files
    
    def test_complete_archive_section_creation(self, temp_workspace, sample_documentation_files):
        """Test complete Task 6.2 archive section creation workflow."""
        
        # Step 1: Set up documentation structure
        docs_dir = temp_workspace / "docs"
        docs_dir.mkdir()
        
        archive_config = ArchiveConfig(
            path="archive",
            include_deprecated=True,
            include_migration_log=True,
            retention_policy="preserve_all"
        )
        
        structure = DocumentationStructure(
            root_path=str(docs_dir) + "/",
            archive_section=archive_config,
            migration_log=MigrationLog()
        )
        
        # Step 2: Initialize archive manager
        archive_manager = ArchiveManager(structure)
        
        # Step 3: Create archive directory structure (Requirement 7.3)
        print("Creating archive directory structure...")
        result = archive_manager.create_archive_directory_structure()
        assert result is True, "Archive directory structure creation should succeed"
        
        # Verify archive structure was created
        archive_path = docs_dir / "archive"
        assert archive_path.exists(), "Archive directory should exist"
        assert (archive_path / "deprecated").exists(), "Deprecated subdirectory should exist"
        assert (archive_path / "legacy-features").exists(), "Legacy features subdirectory should exist"
        assert (archive_path / "README.md").exists(), "Archive index should exist"
        
        print(f"✓ Archive directory structure created at {archive_path}")
        
        # Step 4: Move historical documentation to archive (Requirement 7.3)
        print("Moving historical documentation to archive...")
        moved_files = archive_manager.move_historical_documentation_to_archive(sample_documentation_files)
        
        # Verify files were moved
        archive_priority_files = [f for f in sample_documentation_files if f.preservation_priority == Priority.ARCHIVE]
        assert len(moved_files) >= len(archive_priority_files), "All archive priority files should be moved"
        
        print(f"✓ Moved {len(moved_files)} files to archive")
        
        # Verify archived files have proper headers
        for original_path, archived_path in moved_files.items():
            archived_file = Path(archived_path)
            assert archived_file.exists(), f"Archived file should exist: {archived_path}"
            
            content = archived_file.read_text(encoding='utf-8')
            assert "ARCHIVED CONTENT" in content, "Archived file should have archive header"
            assert "Archive Information" in content, "Archived file should have metadata"
            assert "Freshness Status" in content, "Archived file should have freshness indicator"
        
        # Step 5: Add freshness indicators to outdated content (Requirement 7.4)
        print("Adding freshness indicators to outdated content...")
        freshness_updates = archive_manager.add_freshness_indicators_to_outdated_content(sample_documentation_files)
        
        # Verify freshness report was created
        freshness_report = archive_path / "freshness-report.md"
        assert freshness_report.exists(), "Freshness report should be created"
        
        report_content = freshness_report.read_text(encoding='utf-8')
        assert "Content Freshness Report" in report_content, "Report should have proper title"
        assert "Freshness Summary" in report_content, "Report should have summary section"
        
        print(f"✓ Added freshness indicators, created report with {len(freshness_updates)} updates")
        
        # Step 6: Create archive migration log
        print("Creating archive migration log...")
        log_result = archive_manager.create_archive_migration_log(moved_files)
        assert log_result is True, "Migration log creation should succeed"
        
        migration_log = archive_path / "migration-log.md"
        assert migration_log.exists(), "Migration log should be created"
        
        log_content = migration_log.read_text(encoding='utf-8')
        assert "Archive Migration Log" in log_content, "Log should have proper title"
        assert "Archived Files" in log_content, "Log should list archived files"
        
        print(f"✓ Created migration log at {migration_log}")
        
        # Step 7: Validate archive structure
        print("Validating archive structure...")
        validation_errors = archive_manager.validate_archive_structure()
        assert len(validation_errors) == 0, f"Archive structure should be valid, but got errors: {validation_errors}"
        
        print("✓ Archive structure validation passed")
        
        # Step 8: Verify complete archive organization
        print("Verifying archive organization...")
        
        # Check that files are organized into appropriate subdirectories
        subdirs_with_files = []
        for subdir in ["deprecated", "legacy-features", "old-implementations", "historical-reports"]:
            subdir_path = archive_path / subdir
            if subdir_path.exists() and any(subdir_path.iterdir()):
                subdirs_with_files.append(subdir)
        
        assert len(subdirs_with_files) > 0, "At least one archive subdirectory should contain files"
        print(f"✓ Files organized into subdirectories: {subdirs_with_files}")
        
        # Step 9: Verify migration log tracking
        migration_operations = structure.migration_log.operations
        archive_operations = [op for op in migration_operations if op.get('type') == 'archive_file']
        assert len(archive_operations) >= len(moved_files), "All archive operations should be logged"
        
        print(f"✓ Migration log contains {len(archive_operations)} archive operations")
        
        # Final summary
        print("\n" + "="*60)
        print("TASK 6.2 ARCHIVE SECTION CREATION - COMPLETE")
        print("="*60)
        print(f"Archive directory: {archive_path}")
        print(f"Files archived: {len(moved_files)}")
        print(f"Freshness indicators: {len(freshness_updates)}")
        print(f"Subdirectories created: {len(subdirs_with_files)}")
        print(f"Migration operations logged: {len(archive_operations)}")
        print("="*60)
        
        # Verify all requirements are met
        assert archive_path.exists(), "Requirement 7.3: Archive directory structure created"
        assert len(moved_files) > 0, "Requirement 7.3: Historical documentation moved to archive"
        assert freshness_report.exists(), "Requirement 7.4: Freshness indicators added to outdated content"
        assert migration_log.exists(), "Archive migration log created"
        
        print("✅ All Task 6.2 requirements successfully implemented!")
    
    def test_archive_structure_components(self, temp_workspace):
        """Test individual components of archive structure."""
        docs_dir = temp_workspace / "docs"
        docs_dir.mkdir()
        
        structure = DocumentationStructure(
            root_path=str(docs_dir) + "/",
            archive_section=ArchiveConfig(),
            migration_log=MigrationLog()
        )
        
        archive_manager = ArchiveManager(structure)
        
        # Test archive directory creation
        result = archive_manager.create_archive_directory_structure()
        assert result is True
        
        archive_path = docs_dir / "archive"
        
        # Verify all expected subdirectories exist
        expected_subdirs = [
            "deprecated",
            "legacy-features", 
            "old-implementations",
            "historical-reports",
            "migration-records"
        ]
        
        for subdir in expected_subdirs:
            subdir_path = archive_path / subdir
            assert subdir_path.exists(), f"Subdirectory {subdir} should exist"
            assert subdir_path.is_dir(), f"Subdirectory {subdir} should be a directory"
        
        # Verify archive index exists and has proper content
        index_path = archive_path / "README.md"
        assert index_path.exists(), "Archive index should exist"
        
        index_content = index_path.read_text(encoding='utf-8')
        assert "Documentation Archive" in index_content
        assert "Archive Structure" in index_content
        assert "Usage Guidelines" in index_content
    
    def test_freshness_indicator_integration(self, temp_workspace):
        """Test freshness indicator functionality."""
        docs_dir = temp_workspace / "docs"
        docs_dir.mkdir()
        
        # Create a file with specific age
        old_file = temp_workspace / "old_document.md"
        old_file.write_text("# Old Document\n\nThis is old content.")
        
        metadata = ContentMetadata(
            last_modified=datetime.now() - timedelta(days=200),
            word_count=10,
            key_topics=["old", "document"]
        )
        
        analysis = FileAnalysis(
            filepath=old_file,
            filename="old_document.md",
            category=Category.FEATURE_DOCS,
            content_type=ContentType.FEATURE_GUIDE,
            metadata=metadata,
            preservation_priority=Priority.MEDIUM
        )
        
        structure = DocumentationStructure(
            root_path=str(docs_dir) + "/",
            archive_section=ArchiveConfig(),
            migration_log=MigrationLog()
        )
        
        archive_manager = ArchiveManager(structure)
        archive_manager.create_archive_directory_structure()
        
        # Test freshness indicator creation
        freshness_updates = archive_manager.add_freshness_indicators_to_outdated_content([analysis])
        
        # Verify freshness report
        freshness_report = docs_dir / "archive" / "freshness-report.md"
        assert freshness_report.exists()
        
        report_content = freshness_report.read_text(encoding='utf-8')
        assert "old_document.md" in report_content
        assert "Freshness Summary" in report_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])