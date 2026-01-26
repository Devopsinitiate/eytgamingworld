"""
Outdated Content Detection module for the Documentation Consolidation System.

This module implements outdated content detection functionality as part of Task 6.1.
It provides methods to identify potentially outdated content based on timestamps,
detect version conflicts, and flag files for archival or removal.

Requirements implemented: 7.1, 7.2, 7.5
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from .models import FileAnalysis, ContentType, Priority


class OutdatedContentDetector:
    """
    Detects and categorizes outdated content in documentation files.
    
    This class implements the outdated content detection functionality
    required by Task 6.1, including timestamp analysis, version conflict
    detection, and archival/removal recommendations.
    """
    
    def __init__(self):
        """Initialize the outdated content detector."""
        self.logger = logging.getLogger('doc_consolidation.outdated_detector')
    
    def identify_outdated_content(self, analyses: List[FileAnalysis]) -> Dict[str, List[FileAnalysis]]:
        """
        Identify potentially outdated content based on timestamps and references.
        
        Implements Requirement 7.1: Identify potentially outdated content based on 
        timestamps and references.
        
        Args:
            analyses: List of FileAnalysis objects for all discovered files
            
        Returns:
            Dictionary categorizing files by outdated status:
            - 'potentially_outdated': Files that appear outdated based on timestamps
            - 'superseded': Files that may be superseded by newer versions
            - 'removal_candidates': Files that can be safely removed
            - 'archive_candidates': Files that should be archived but preserved
        """
        self.logger.info("Identifying outdated content based on timestamps and references")
        
        outdated_content = {
            'potentially_outdated': [],
            'superseded': [],
            'removal_candidates': [],
            'archive_candidates': []
        }
        
        # Sort analyses by modification date for comparison
        sorted_analyses = sorted(analyses, key=lambda x: x.metadata.last_modified or datetime.min)
        
        # Identify potentially outdated files based on timestamps
        outdated_content['potentially_outdated'] = self._identify_timestamp_outdated(analyses)
        
        # Identify superseded files (newer versions exist)
        outdated_content['superseded'] = self._identify_superseded_files(analyses)
        
        # Identify removal candidates
        outdated_content['removal_candidates'] = self._identify_removal_candidates(analyses)
        
        # Identify archive candidates
        outdated_content['archive_candidates'] = self._identify_archive_candidates(analyses)
        
        # Log summary
        total_outdated = sum(len(files) for files in outdated_content.values())
        self.logger.info(f"Identified {total_outdated} files with outdated content issues:")
        for category, files in outdated_content.items():
            if files:
                self.logger.info(f"  {category}: {len(files)} files")
        
        return outdated_content
    
    def _identify_timestamp_outdated(self, analyses: List[FileAnalysis]) -> List[FileAnalysis]:
        """
        Identify files that are potentially outdated based on timestamps.
        
        Implements Requirement 7.1: Analyze file timestamps to identify potentially outdated content.
        
        Args:
            analyses: List of FileAnalysis objects
            
        Returns:
            List of FileAnalysis objects for potentially outdated files
        """
        outdated_files = []
        current_time = datetime.now()
        
        # Define age thresholds for different content types
        age_thresholds = {
            ContentType.COMPLETION_SUMMARY: 365,  # 1 year for completion summaries
            ContentType.FEATURE_GUIDE: 180,      # 6 months for feature guides
            ContentType.SETUP_PROCEDURE: 90,     # 3 months for setup procedures
            ContentType.TEST_REPORT: 30,         # 1 month for test reports
            ContentType.QUICK_REFERENCE: 180,    # 6 months for quick references
            ContentType.INTEGRATION_GUIDE: 120,  # 4 months for integration guides
            ContentType.HISTORICAL_DOC: 0,       # Historical docs are expected to be old
            ContentType.GENERAL_DOC: 365         # 1 year for general docs
        }
        
        for analysis in analyses:
            if not analysis.metadata.last_modified:
                continue
            
            # Calculate file age in days
            age_days = (current_time - analysis.metadata.last_modified).days
            
            # Get threshold for this content type
            threshold = age_thresholds.get(analysis.content_type, 365)
            
            # Skip historical documents as they're expected to be old
            if analysis.content_type == ContentType.HISTORICAL_DOC:
                continue
            
            # Check if file exceeds age threshold
            if age_days > threshold:
                analysis.processing_notes.append(
                    f"Potentially outdated: {age_days} days old (threshold: {threshold} days)"
                )
                outdated_files.append(analysis)
                self.logger.debug(f"Identified outdated file: {analysis.filename} "
                                f"({age_days} days old, threshold: {threshold})")
        
        return outdated_files
    
    def _identify_superseded_files(self, analyses: List[FileAnalysis]) -> List[FileAnalysis]:
        """
        Identify files that may be superseded by newer versions.
        
        Implements Requirement 7.2: Detect version conflicts and superseded files.
        
        Args:
            analyses: List of FileAnalysis objects
            
        Returns:
            List of FileAnalysis objects for superseded files
        """
        superseded_files = []
        
        # Group files by base name to find version conflicts
        file_groups = {}
        for analysis in analyses:
            base_name = self._extract_base_filename(analysis.filename)
            if base_name not in file_groups:
                file_groups[base_name] = []
            file_groups[base_name].append(analysis)
        
        # Check each group for version conflicts
        for base_name, group in file_groups.items():
            if len(group) <= 1:
                continue
            
            # Sort by modification date (newest first)
            sorted_group = sorted(group, 
                                key=lambda x: x.metadata.last_modified or datetime.min, 
                                reverse=True)
            
            # Check for version patterns
            versioned_files = []
            for analysis in sorted_group:
                version_info = self._extract_version_from_filename(analysis.filename)
                if version_info:
                    versioned_files.append((analysis, version_info))
            
            # If we have versioned files, mark older versions as superseded
            if len(versioned_files) > 1:
                # Sort by version (newest first)
                versioned_files.sort(key=lambda x: x[1], reverse=True)
                
                # Mark all but the newest as superseded
                for analysis, version in versioned_files[1:]:
                    analysis.processing_notes.append(
                        f"Superseded by newer version: {versioned_files[0][0].filename}"
                    )
                    superseded_files.append(analysis)
                    self.logger.debug(f"Identified superseded file: {analysis.filename} "
                                    f"(version {version}, superseded by {versioned_files[0][1]})")
            
            # Check for completion files with similar names
            completion_files = [a for a in sorted_group 
                              if 'complete' in a.filename.lower() or 'summary' in a.filename.lower()]
            
            if len(completion_files) > 1:
                # Mark older completion files as superseded
                for analysis in completion_files[1:]:
                    analysis.processing_notes.append(
                        f"Superseded by newer completion file: {completion_files[0].filename}"
                    )
                    superseded_files.append(analysis)
                    self.logger.debug(f"Identified superseded completion file: {analysis.filename}")
        
        return superseded_files
    
    def _identify_removal_candidates(self, analyses: List[FileAnalysis]) -> List[FileAnalysis]:
        """
        Identify files that can be safely removed after consolidation.
        
        Implements Requirement 7.5: Suggest which files can be safely removed.
        
        Args:
            analyses: List of FileAnalysis objects
            
        Returns:
            List of FileAnalysis objects for removal candidates
        """
        removal_candidates = []
        
        for analysis in analyses:
            should_remove = False
            removal_reason = ""
            
            # Check for empty or minimal content files
            if analysis.metadata.word_count < 10:
                should_remove = True
                removal_reason = f"Minimal content ({analysis.metadata.word_count} words)"
            
            # Check for duplicate content (very similar files)
            elif self._is_duplicate_content(analysis, analyses):
                should_remove = True
                removal_reason = "Duplicate content detected"
            
            # Check for temporary or draft files
            elif self._is_temporary_file(analysis.filename):
                should_remove = True
                removal_reason = "Temporary or draft file"
            
            # Check for very old test reports or logs
            elif (analysis.content_type == ContentType.TEST_REPORT and 
                  analysis.metadata.last_modified and
                  (datetime.now() - analysis.metadata.last_modified).days > 90):
                should_remove = True
                removal_reason = "Old test report (>90 days)"
            
            if should_remove:
                analysis.processing_notes.append(f"Removal candidate: {removal_reason}")
                removal_candidates.append(analysis)
                self.logger.debug(f"Identified removal candidate: {analysis.filename} ({removal_reason})")
        
        return removal_candidates
    
    def _identify_archive_candidates(self, analyses: List[FileAnalysis]) -> List[FileAnalysis]:
        """
        Identify files that should be archived but preserved.
        
        Implements Requirement 7.5: Flag files for archival.
        
        Args:
            analyses: List of FileAnalysis objects
            
        Returns:
            List of FileAnalysis objects for archive candidates
        """
        archive_candidates = []
        
        for analysis in analyses:
            should_archive = False
            archive_reason = ""
            
            # Archive very old completion summaries
            if (analysis.content_type == ContentType.COMPLETION_SUMMARY and
                analysis.metadata.last_modified and
                (datetime.now() - analysis.metadata.last_modified).days > 365):
                should_archive = True
                archive_reason = "Old completion summary (>1 year)"
            
            # Archive deprecated feature documentation
            elif self._is_deprecated_content(analysis):
                should_archive = True
                archive_reason = "Deprecated feature documentation"
            
            # Archive old setup procedures that may still have reference value
            elif (analysis.content_type == ContentType.SETUP_PROCEDURE and
                  analysis.metadata.last_modified and
                  (datetime.now() - analysis.metadata.last_modified).days > 180):
                should_archive = True
                archive_reason = "Old setup procedure (>6 months)"
            
            # Archive files with historical value but outdated information
            elif (analysis.preservation_priority == Priority.LOW and
                  analysis.metadata.last_modified and
                  (datetime.now() - analysis.metadata.last_modified).days > 180):
                should_archive = True
                archive_reason = "Low priority historical content"
            
            if should_archive:
                analysis.processing_notes.append(f"Archive candidate: {archive_reason}")
                archive_candidates.append(analysis)
                self.logger.debug(f"Identified archive candidate: {analysis.filename} ({archive_reason})")
        
        return archive_candidates
    
    def detect_version_conflicts(self, analyses: List[FileAnalysis]) -> Dict[str, List[FileAnalysis]]:
        """
        Detect version conflicts between files.
        
        Implements Requirement 7.2: Detect version conflicts and superseded files.
        
        Args:
            analyses: List of FileAnalysis objects
            
        Returns:
            Dictionary mapping conflict groups to lists of conflicting files
        """
        self.logger.info("Detecting version conflicts between files")
        
        conflicts = {}
        
        # Group files by similar base names
        base_name_groups = {}
        for analysis in analyses:
            base_name = self._extract_base_filename(analysis.filename)
            if base_name not in base_name_groups:
                base_name_groups[base_name] = []
            base_name_groups[base_name].append(analysis)
        
        # Check each group for conflicts
        for base_name, group in base_name_groups.items():
            if len(group) <= 1:
                continue
            
            # Look for version conflicts
            versioned_files = []
            completion_files = []
            similar_files = []
            
            for analysis in group:
                if self._extract_version_from_filename(analysis.filename):
                    versioned_files.append(analysis)
                elif 'complete' in analysis.filename.lower() or 'summary' in analysis.filename.lower():
                    completion_files.append(analysis)
                else:
                    similar_files.append(analysis)
            
            # Report version conflicts
            if len(versioned_files) > 1:
                conflict_key = f"version_conflict_{base_name}"
                conflicts[conflict_key] = versioned_files
                self.logger.warning(f"Version conflict detected for {base_name}: "
                                  f"{[f.filename for f in versioned_files]}")
            
            # Report completion file conflicts
            if len(completion_files) > 1:
                conflict_key = f"completion_conflict_{base_name}"
                conflicts[conflict_key] = completion_files
                self.logger.warning(f"Completion file conflict detected for {base_name}: "
                                  f"{[f.filename for f in completion_files]}")
            
            # Report similar file conflicts
            if len(similar_files) > 1:
                # Check if they're actually similar content
                if self._are_files_similar_content(similar_files):
                    conflict_key = f"content_conflict_{base_name}"
                    conflicts[conflict_key] = similar_files
                    self.logger.warning(f"Content conflict detected for {base_name}: "
                                      f"{[f.filename for f in similar_files]}")
        
        self.logger.info(f"Detected {len(conflicts)} version conflicts")
        return conflicts
    
    def create_freshness_indicators(self, analyses: List[FileAnalysis]) -> Dict[str, str]:
        """
        Create freshness indicators for content.
        
        Implements Requirement 7.4: Provide clear indicators about content freshness.
        
        Args:
            analyses: List of FileAnalysis objects
            
        Returns:
            Dictionary mapping filenames to freshness indicators
        """
        self.logger.info("Creating freshness indicators for content")
        
        freshness_indicators = {}
        current_time = datetime.now()
        
        for analysis in analyses:
            if not analysis.metadata.last_modified:
                freshness_indicators[analysis.filename] = "⚠️ Unknown age"
                continue
            
            age_days = (current_time - analysis.metadata.last_modified).days
            
            # Create freshness indicator based on age and content type
            if age_days <= 7:
                indicator = "🟢 Fresh (updated within 1 week)"
            elif age_days <= 30:
                indicator = "🟡 Recent (updated within 1 month)"
            elif age_days <= 90:
                indicator = "🟠 Aging (updated within 3 months)"
            elif age_days <= 180:
                indicator = "🔴 Stale (updated within 6 months)"
            else:
                indicator = f"⚫ Old (last updated {age_days} days ago)"
            
            # Add content-specific context
            if analysis.content_type == ContentType.COMPLETION_SUMMARY:
                if age_days > 365:
                    indicator += " - Consider archiving"
                elif age_days > 180:
                    indicator += " - May need review"
            
            elif analysis.content_type == ContentType.SETUP_PROCEDURE:
                if age_days > 90:
                    indicator += " - Verify current accuracy"
                elif age_days > 30:
                    indicator += " - Check for updates"
            
            elif analysis.content_type == ContentType.TEST_REPORT:
                if age_days > 30:
                    indicator += " - Likely outdated"
                elif age_days > 7:
                    indicator += " - May be outdated"
            
            elif analysis.content_type == ContentType.FEATURE_GUIDE:
                if age_days > 180:
                    indicator += " - Verify feature status"
                elif age_days > 90:
                    indicator += " - Check for changes"
            
            freshness_indicators[analysis.filename] = indicator
        
        self.logger.info(f"Created freshness indicators for {len(freshness_indicators)} files")
        return freshness_indicators
    
    def flag_for_archival_or_removal(self, analyses: List[FileAnalysis]) -> Dict[str, Dict[str, List[FileAnalysis]]]:
        """
        Flag files for archival or removal with detailed recommendations.
        
        Implements Requirement 7.5: Flag files for archival or removal.
        
        Args:
            analyses: List of FileAnalysis objects
            
        Returns:
            Dictionary with archival and removal recommendations
        """
        self.logger.info("Flagging files for archival or removal")
        
        recommendations = {
            'archive': {
                'high_priority': [],
                'medium_priority': [],
                'low_priority': []
            },
            'remove': {
                'safe_to_remove': [],
                'review_required': [],
                'keep_but_consolidate': []
            }
        }
        
        for analysis in analyses:
            # Determine archival recommendations
            archive_priority = self._determine_archive_priority(analysis)
            if archive_priority:
                recommendations['archive'][archive_priority].append(analysis)
            
            # Determine removal recommendations
            removal_category = self._determine_removal_category(analysis)
            if removal_category:
                recommendations['remove'][removal_category].append(analysis)
        
        # Log summary
        total_archive = sum(len(files) for files in recommendations['archive'].values())
        total_remove = sum(len(files) for files in recommendations['remove'].values())
        
        self.logger.info(f"Archival recommendations: {total_archive} files")
        for priority, files in recommendations['archive'].items():
            if files:
                self.logger.info(f"  {priority}: {len(files)} files")
        
        self.logger.info(f"Removal recommendations: {total_remove} files")
        for category, files in recommendations['remove'].items():
            if files:
                self.logger.info(f"  {category}: {len(files)} files")
        
        return recommendations
    
    # Helper methods
    
    def _extract_base_filename(self, filename: str) -> str:
        """Extract base filename without version indicators."""
        import re
        
        # Remove common version patterns
        base_name = re.sub(r'_v\d+', '', filename, flags=re.IGNORECASE)
        base_name = re.sub(r'_version_\d+', '', base_name, flags=re.IGNORECASE)
        base_name = re.sub(r'_\d{4}-\d{2}-\d{2}', '', base_name)
        base_name = re.sub(r'_\d+$', '', base_name.replace('.md', ''))
        
        return base_name
    
    def _extract_version_from_filename(self, filename: str) -> Optional[str]:
        """Extract version information from filename."""
        import re
        
        version_patterns = [
            r'_v(\d+(?:\.\d+)*)',
            r'_version_(\d+(?:\.\d+)*)',
            r'_(\d{4}-\d{2}-\d{2})',
            r'_(\d+)\.md$'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _is_duplicate_content(self, analysis: FileAnalysis, all_analyses: List[FileAnalysis]) -> bool:
        """Check if file content is duplicate of another file."""
        if analysis.metadata.word_count < 20:  # Too small to reliably detect duplicates
            return False
        
        current_topics = set(analysis.metadata.key_topics)
        
        for other_analysis in all_analyses:
            if other_analysis.filename == analysis.filename:
                continue
            
            # Compare word counts (similar size)
            word_count_ratio = min(analysis.metadata.word_count, other_analysis.metadata.word_count) / \
                             max(analysis.metadata.word_count, other_analysis.metadata.word_count)
            
            if word_count_ratio < 0.8:  # Different sizes, likely not duplicates
                continue
            
            # Compare topics
            other_topics = set(other_analysis.metadata.key_topics)
            if current_topics and other_topics:
                topic_overlap = len(current_topics & other_topics) / len(current_topics | other_topics)
                if topic_overlap > 0.8:  # 80% topic overlap
                    return True
        
        return False
    
    def _is_temporary_file(self, filename: str) -> bool:
        """Check if filename indicates a temporary or draft file."""
        temp_indicators = [
            'temp', 'tmp', 'draft', 'backup', 'copy', 'old', 'bak',
            'test_', '_test', 'scratch', 'notes', 'wip'
        ]
        
        filename_lower = filename.lower()
        return any(indicator in filename_lower for indicator in temp_indicators)
    
    def _is_deprecated_content(self, analysis: FileAnalysis) -> bool:
        """Check if content appears to be deprecated."""
        deprecated_indicators = [
            'deprecated', 'obsolete', 'legacy', 'old_', 'archived',
            'removed', 'discontinued', 'superseded'
        ]
        
        filename_lower = analysis.filename.lower()
        
        # Check filename for deprecated indicators
        if any(indicator in filename_lower for indicator in deprecated_indicators):
            return True
        
        # Check topics for deprecated indicators
        topics_text = ' '.join(analysis.metadata.key_topics).lower()
        if any(indicator in topics_text for indicator in deprecated_indicators):
            return True
        
        return False
    
    def _are_files_similar_content(self, files: List[FileAnalysis]) -> bool:
        """Check if files have similar content."""
        if len(files) < 2:
            return False
        
        # Compare the first file with all others
        base_file = files[0]
        base_topics = set(base_file.metadata.key_topics)
        
        for other_file in files[1:]:
            other_topics = set(other_file.metadata.key_topics)
            
            if base_topics and other_topics:
                overlap = len(base_topics & other_topics) / len(base_topics | other_topics)
                if overlap > 0.6:  # 60% topic overlap
                    return True
        
        return False
    
    def _determine_archive_priority(self, analysis: FileAnalysis) -> Optional[str]:
        """Determine archive priority for a file."""
        if not analysis.metadata.last_modified:
            return None
        
        age_days = (datetime.now() - analysis.metadata.last_modified).days
        
        # High priority archival
        if (analysis.content_type == ContentType.COMPLETION_SUMMARY and age_days > 365):
            return 'high_priority'
        
        if (analysis.content_type == ContentType.TEST_REPORT and age_days > 90):
            return 'high_priority'
        
        # Medium priority archival
        if (analysis.content_type == ContentType.SETUP_PROCEDURE and age_days > 180):
            return 'medium_priority'
        
        if (analysis.content_type == ContentType.FEATURE_GUIDE and age_days > 365):
            return 'medium_priority'
        
        # Low priority archival
        if (analysis.preservation_priority == Priority.LOW and age_days > 180):
            return 'low_priority'
        
        if self._is_deprecated_content(analysis):
            return 'medium_priority'
        
        return None
    
    def _determine_removal_category(self, analysis: FileAnalysis) -> Optional[str]:
        """Determine removal category for a file."""
        # Safe to remove
        if analysis.metadata.word_count < 10:
            return 'safe_to_remove'
        
        if self._is_temporary_file(analysis.filename):
            return 'safe_to_remove'
        
        if (analysis.content_type == ContentType.TEST_REPORT and 
            analysis.metadata.last_modified and
            (datetime.now() - analysis.metadata.last_modified).days > 90):
            return 'safe_to_remove'
        
        # Review required
        if self._is_duplicate_content(analysis, []):  # Would need full list in real implementation
            return 'review_required'
        
        # Keep but consolidate
        if (analysis.content_type == ContentType.COMPLETION_SUMMARY and
            len(analysis.metadata.key_topics) > 0):
            return 'keep_but_consolidate'
        
        return None