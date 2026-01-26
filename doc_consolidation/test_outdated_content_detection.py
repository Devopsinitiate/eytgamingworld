"""
Unit tests for outdated content detection functionality (Task 6.1).

Tests the ContentAnalyzer's outdated content detection methods that implement
Requirements 7.1, 7.2, and 7.5.
"""

import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from doc_consolidation.outdated_content_detector import OutdatedContentDetector
from doc_consolidation.models import (
    FileAnalysis, ContentMetadata, Category, ContentType, Priority
)
from doc_consolidation.config import ConsolidationConfig


class TestOutdatedContentDetection(unittest.TestCase):
    """Test outdated content detection functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = OutdatedContentDetector()
        
        # Create test file analyses with different ages
        self.current_time = datetime.now()
        
        # Fresh file (1 week old)
        self.fresh_analysis = self._create_test_analysis(
            "fresh_guide.md",
            ContentType.FEATURE_GUIDE,
            age_days=7
        )
        
        # Recent file (1 month old)
        self.recent_analysis = self._create_test_analysis(
            "recent_setup.md",
            ContentType.SETUP_PROCEDURE,
            age_days=30
        )
        
        # Aging file (3 months old)
        self.aging_analysis = self._create_test_analysis(
            "aging_test_report.md",
            ContentType.TEST_REPORT,
            age_days=90
        )
        
        # Stale file (6 months old)
        self.stale_analysis = self._create_test_analysis(
            "stale_completion.md",
            ContentType.COMPLETION_SUMMARY,
            age_days=180
        )
        
        # Old file (1 year old)
        self.old_analysis = self._create_test_analysis(
            "old_feature.md",
            ContentType.FEATURE_GUIDE,
            age_days=365
        )
        
        # Very old file (2 years old)
        self.very_old_analysis = self._create_test_analysis(
            "very_old_summary.md",
            ContentType.COMPLETION_SUMMARY,
            age_days=730
        )
        
        self.test_analyses = [
            self.fresh_analysis,
            self.recent_analysis,
            self.aging_analysis,
            self.stale_analysis,
            self.old_analysis,
            self.very_old_analysis
        ]
    
    def _create_test_analysis(self, filename: str, content_type: ContentType, 
                            age_days: int, word_count: int = 100) -> FileAnalysis:
        """Create a test FileAnalysis object."""
        metadata = ContentMetadata()
        metadata.last_modified = self.current_time - timedelta(days=age_days)
        metadata.word_count = word_count
        metadata.key_topics = [f"topic_{filename.split('.')[0]}"]
        
        return FileAnalysis(
            filepath=Path(filename),
            filename=filename,
            category=Category.FEATURE_DOCS,
            content_type=content_type,
            metadata=metadata,
            preservation_priority=Priority.MEDIUM
        )
    
    def test_identify_outdated_content_basic(self):
        """Test basic outdated content identification."""
        result = self.detector.identify_outdated_content(self.test_analyses)
        
        # Check that all categories are present
        expected_categories = ['potentially_outdated', 'superseded', 'removal_candidates', 'archive_candidates']
        for category in expected_categories:
            self.assertIn(category, result)
            self.assertIsInstance(result[category], list)
    
    def test_identify_timestamp_outdated(self):
        """Test identification of outdated files based on timestamps."""
        outdated_files = self.detector._identify_timestamp_outdated(self.test_analyses)
        
        # Should identify files that exceed their content type thresholds
        outdated_filenames = [f.filename for f in outdated_files]
        
        # Test report (30 day threshold) - 90 days old should be outdated
        self.assertIn("aging_test_report.md", outdated_filenames)
        
        # Feature guide (180 day threshold) - 365 days old should be outdated
        self.assertIn("old_feature.md", outdated_filenames)
        
        # Completion summary (365 day threshold) - 730 days old should be outdated
        self.assertIn("very_old_summary.md", outdated_filenames)
        
        # Fresh files should not be outdated
        self.assertNotIn("fresh_guide.md", outdated_filenames)
        self.assertNotIn("recent_setup.md", outdated_filenames)
    
    def test_identify_superseded_files(self):
        """Test identification of superseded files."""
        # Create versioned files
        v1_analysis = self._create_test_analysis("feature_guide_v1.md", ContentType.FEATURE_GUIDE, 100)
        v2_analysis = self._create_test_analysis("feature_guide_v2.md", ContentType.FEATURE_GUIDE, 50)
        v3_analysis = self._create_test_analysis("feature_guide_v3.md", ContentType.FEATURE_GUIDE, 10)
        
        versioned_analyses = [v1_analysis, v2_analysis, v3_analysis]
        
        superseded_files = self.detector._identify_superseded_files(versioned_analyses)
        superseded_filenames = [f.filename for f in superseded_files]
        
        # Older versions should be superseded
        self.assertIn("feature_guide_v1.md", superseded_filenames)
        self.assertIn("feature_guide_v2.md", superseded_filenames)
        
        # Newest version should not be superseded
        self.assertNotIn("feature_guide_v3.md", superseded_filenames)
    
    def test_identify_removal_candidates(self):
        """Test identification of files that can be removed."""
        # Create test files with different characteristics
        empty_analysis = self._create_test_analysis("empty.md", ContentType.GENERAL_DOC, 10, word_count=5)
        temp_analysis = self._create_test_analysis("temp_notes.md", ContentType.GENERAL_DOC, 10)
        old_test_analysis = self._create_test_analysis("old_test.md", ContentType.TEST_REPORT, 100)
        
        test_analyses = [empty_analysis, temp_analysis, old_test_analysis]
        
        removal_candidates = self.detector._identify_removal_candidates(test_analyses)
        removal_filenames = [f.filename for f in removal_candidates]
        
        # Empty file should be removal candidate
        self.assertIn("empty.md", removal_filenames)
        
        # Temporary file should be removal candidate
        self.assertIn("temp_notes.md", removal_filenames)
        
        # Old test report should be removal candidate
        self.assertIn("old_test.md", removal_filenames)
    
    def test_identify_archive_candidates(self):
        """Test identification of files that should be archived."""
        archive_candidates = self.detector._identify_archive_candidates(self.test_analyses)
        archive_filenames = [f.filename for f in archive_candidates]
        
        # Very old completion summary should be archive candidate
        self.assertIn("very_old_summary.md", archive_filenames)
        
        # Fresh files should not be archive candidates
        self.assertNotIn("fresh_guide.md", archive_filenames)
    
    def test_detect_version_conflicts(self):
        """Test detection of version conflicts between files."""
        # Create conflicting files
        v1_analysis = self._create_test_analysis("setup_v1.md", ContentType.SETUP_PROCEDURE, 100)
        v2_analysis = self._create_test_analysis("setup_v2.md", ContentType.SETUP_PROCEDURE, 50)
        complete1_analysis = self._create_test_analysis("task_complete.md", ContentType.COMPLETION_SUMMARY, 30)
        complete2_analysis = self._create_test_analysis("task_summary.md", ContentType.COMPLETION_SUMMARY, 20)
        
        conflict_analyses = [v1_analysis, v2_analysis, complete1_analysis, complete2_analysis]
        
        conflicts = self.detector.detect_version_conflicts(conflict_analyses)
        
        # Should detect version conflicts
        self.assertGreater(len(conflicts), 0)
        
        # Check that conflicts are properly categorized
        conflict_keys = list(conflicts.keys())
        version_conflicts = [k for k in conflict_keys if 'version_conflict' in k]
        completion_conflicts = [k for k in conflict_keys if 'completion_conflict' in k]
        
        self.assertGreater(len(version_conflicts), 0)
        self.assertGreater(len(completion_conflicts), 0)
    
    def test_create_freshness_indicators(self):
        """Test creation of freshness indicators."""
        indicators = self.detector.create_freshness_indicators(self.test_analyses)
        
        # Check that all files have indicators
        self.assertEqual(len(indicators), len(self.test_analyses))
        
        # Check specific indicators
        self.assertIn("🟢", indicators["fresh_guide.md"])  # Fresh
        self.assertIn("🟡", indicators["recent_setup.md"])  # Recent
        self.assertIn("🔴", indicators["stale_completion.md"])  # Stale
        self.assertIn("⚫", indicators["very_old_summary.md"])  # Old
        
        # Check content-specific recommendations
        self.assertIn("Consider archiving", indicators["very_old_summary.md"])
        self.assertIn("Verify current accuracy", indicators.get("aging_setup.md", ""))
    
    def test_flag_for_archival_or_removal(self):
        """Test flagging files for archival or removal."""
        recommendations = self.detector.flag_for_archival_or_removal(self.test_analyses)
        
        # Check structure
        self.assertIn('archive', recommendations)
        self.assertIn('remove', recommendations)
        
        archive_recs = recommendations['archive']
        remove_recs = recommendations['remove']
        
        # Check archive categories
        self.assertIn('high_priority', archive_recs)
        self.assertIn('medium_priority', archive_recs)
        self.assertIn('low_priority', archive_recs)
        
        # Check removal categories
        self.assertIn('safe_to_remove', remove_recs)
        self.assertIn('review_required', remove_recs)
        self.assertIn('keep_but_consolidate', remove_recs)
    
    def test_extract_base_filename(self):
        """Test extraction of base filename without version indicators."""
        test_cases = [
            ("feature_guide_v1.md", "feature_guide"),
            ("setup_version_2.md", "setup"),
            ("task_2023-01-15.md", "task"),
            ("report_1.md", "report"),
            ("normal_file.md", "normal_file")
        ]
        
        for filename, expected_base in test_cases:
            with self.subTest(filename=filename):
                result = self.detector._extract_base_filename(filename)
                self.assertEqual(result, expected_base)
    
    def test_extract_version_from_filename(self):
        """Test extraction of version information from filename."""
        test_cases = [
            ("feature_v1.2.3.md", "1.2.3"),
            ("setup_version_2.md", "2"),
            ("task_2023-01-15.md", "2023-01-15"),
            ("report_5.md", "5"),
            ("normal_file.md", None)
        ]
        
        for filename, expected_version in test_cases:
            with self.subTest(filename=filename):
                result = self.detector._extract_version_from_filename(filename)
                self.assertEqual(result, expected_version)
    
    def test_is_temporary_file(self):
        """Test identification of temporary files."""
        temp_files = [
            "temp_notes.md",
            "draft_guide.md",
            "backup_config.md",
            "test_scratch.md",
            "old_version.md"
        ]
        
        regular_files = [
            "feature_guide.md",
            "setup_instructions.md",
            "user_manual.md"
        ]
        
        for filename in temp_files:
            with self.subTest(filename=filename):
                self.assertTrue(self.detector._is_temporary_file(filename))
        
        for filename in regular_files:
            with self.subTest(filename=filename):
                self.assertFalse(self.detector._is_temporary_file(filename))
    
    def test_is_deprecated_content(self):
        """Test identification of deprecated content."""
        # Create deprecated analysis
        deprecated_analysis = self._create_test_analysis("deprecated_feature.md", ContentType.FEATURE_GUIDE, 100)
        deprecated_analysis.metadata.key_topics = ["deprecated", "obsolete", "legacy"]
        
        # Create regular analysis
        regular_analysis = self._create_test_analysis("current_feature.md", ContentType.FEATURE_GUIDE, 30)
        regular_analysis.metadata.key_topics = ["current", "active", "supported"]
        
        self.assertTrue(self.detector._is_deprecated_content(deprecated_analysis))
        self.assertFalse(self.detector._is_deprecated_content(regular_analysis))
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with empty list
        result = self.detector.identify_outdated_content([])
        self.assertEqual(len(result['potentially_outdated']), 0)
        
        # Test with file without modification date
        no_date_analysis = self._create_test_analysis("no_date.md", ContentType.GENERAL_DOC, 0)
        no_date_analysis.metadata.last_modified = None
        
        result = self.detector.identify_outdated_content([no_date_analysis])
        # Should handle gracefully without errors
        self.assertIsInstance(result, dict)
    
    def test_processing_notes_added(self):
        """Test that processing notes are added to outdated files."""
        result = self.detector.identify_outdated_content(self.test_analyses)
        
        # Check that outdated files have processing notes
        for outdated_file in result['potentially_outdated']:
            self.assertGreater(len(outdated_file.processing_notes), 0)
            # Should contain outdated information
            notes_text = ' '.join(outdated_file.processing_notes)
            self.assertIn('outdated', notes_text.lower())
        
        for superseded_file in result['superseded']:
            self.assertGreater(len(superseded_file.processing_notes), 0)
            # Should contain superseded information
            notes_text = ' '.join(superseded_file.processing_notes)
            self.assertIn('superseded', notes_text.lower())


class TestOutdatedContentIntegration(unittest.TestCase):
    """Integration tests for outdated content detection with real file scenarios."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.detector = OutdatedContentDetector()
    
    def test_realistic_file_scenario(self):
        """Test with a realistic set of documentation files."""
        # Create a realistic scenario with various file types and ages
        files = [
            # Fresh documentation
            self._create_realistic_analysis("USER_AUTHENTICATION_GUIDE.md", ContentType.FEATURE_GUIDE, 15, 500),
            self._create_realistic_analysis("QUICK_START.md", ContentType.QUICK_REFERENCE, 20, 200),
            
            # Aging documentation
            self._create_realistic_analysis("PAYMENT_SETUP.md", ContentType.SETUP_PROCEDURE, 120, 300),
            self._create_realistic_analysis("test_results_2023.md", ContentType.TEST_REPORT, 45, 150),
            
            # Old documentation
            self._create_realistic_analysis("TASK_1_COMPLETE.md", ContentType.COMPLETION_SUMMARY, 400, 800),
            self._create_realistic_analysis("legacy_tournament_guide.md", ContentType.FEATURE_GUIDE, 500, 600),
            
            # Version conflicts
            self._create_realistic_analysis("api_docs_v1.md", ContentType.INTEGRATION_GUIDE, 200, 400),
            self._create_realistic_analysis("api_docs_v2.md", ContentType.INTEGRATION_GUIDE, 100, 450),
            self._create_realistic_analysis("api_docs_v3.md", ContentType.INTEGRATION_GUIDE, 30, 500),
            
            # Temporary/draft files
            self._create_realistic_analysis("temp_notes.md", ContentType.GENERAL_DOC, 10, 50),
            self._create_realistic_analysis("draft_feature.md", ContentType.FEATURE_GUIDE, 5, 25),
        ]
        
        # Run outdated content detection
        result = self.detector.identify_outdated_content(files)
        
        # Verify results make sense
        self.assertGreater(len(result['potentially_outdated']), 0)
        self.assertGreater(len(result['archive_candidates']), 0)
        
        # Check version conflicts
        conflicts = self.detector.detect_version_conflicts(files)
        self.assertGreater(len(conflicts), 0)
        
        # Check freshness indicators
        indicators = self.detector.create_freshness_indicators(files)
        self.assertEqual(len(indicators), len(files))
        
        # Check archival/removal recommendations
        recommendations = self.detector.flag_for_archival_or_removal(files)
        total_recommendations = (
            sum(len(files) for files in recommendations['archive'].values()) +
            sum(len(files) for files in recommendations['remove'].values())
        )
        self.assertGreater(total_recommendations, 0)
    
    def _create_realistic_analysis(self, filename: str, content_type: ContentType, 
                                 age_days: int, word_count: int) -> FileAnalysis:
        """Create a realistic FileAnalysis object for integration testing."""
        metadata = ContentMetadata()
        metadata.last_modified = datetime.now() - timedelta(days=age_days)
        metadata.word_count = word_count
        
        # Add realistic topics based on filename
        if 'auth' in filename.lower():
            metadata.key_topics = ['authentication', 'login', 'security', 'user']
        elif 'payment' in filename.lower():
            metadata.key_topics = ['payment', 'billing', 'stripe', 'transaction']
        elif 'tournament' in filename.lower():
            metadata.key_topics = ['tournament', 'match', 'bracket', 'competition']
        elif 'api' in filename.lower():
            metadata.key_topics = ['api', 'endpoint', 'integration', 'documentation']
        elif 'test' in filename.lower():
            metadata.key_topics = ['testing', 'validation', 'results', 'coverage']
        else:
            metadata.key_topics = ['general', 'documentation', 'guide']
        
        # Add realistic metadata
        metadata.headings = [f"# {filename.replace('.md', '').replace('_', ' ').title()}"]
        metadata.has_code = 'api' in filename.lower() or 'setup' in filename.lower()
        metadata.has_links = word_count > 100
        
        return FileAnalysis(
            filepath=Path(filename),
            filename=filename,
            category=self._determine_category_from_filename(filename),
            content_type=content_type,
            metadata=metadata,
            preservation_priority=self._determine_priority_from_content(content_type, age_days)
        )
    
    def _determine_category_from_filename(self, filename: str) -> Category:
        """Determine category based on filename patterns."""
        filename_lower = filename.lower()
        
        if 'setup' in filename_lower or 'install' in filename_lower:
            return Category.SETUP_CONFIG
        elif any(feature in filename_lower for feature in ['auth', 'payment', 'tournament']):
            return Category.FEATURE_DOCS
        elif 'complete' in filename_lower or 'task' in filename_lower:
            return Category.IMPLEMENTATION_COMPLETION
        elif 'test' in filename_lower:
            return Category.TESTING_VALIDATION
        elif 'quick' in filename_lower or 'reference' in filename_lower:
            return Category.QUICK_REFERENCES
        elif 'api' in filename_lower or 'integration' in filename_lower:
            return Category.INTEGRATION_GUIDES
        else:
            return Category.UNCATEGORIZED
    
    def _determine_priority_from_content(self, content_type: ContentType, age_days: int) -> Priority:
        """Determine priority based on content type and age."""
        if content_type in [ContentType.SETUP_PROCEDURE, ContentType.FEATURE_GUIDE]:
            return Priority.HIGH if age_days < 90 else Priority.MEDIUM
        elif content_type == ContentType.COMPLETION_SUMMARY:
            return Priority.MEDIUM if age_days < 365 else Priority.LOW
        elif content_type == ContentType.TEST_REPORT:
            return Priority.LOW if age_days > 30 else Priority.MEDIUM
        else:
            return Priority.MEDIUM


if __name__ == '__main__':
    unittest.main()