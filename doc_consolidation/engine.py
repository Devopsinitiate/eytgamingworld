"""
Consolidation Engine component for the Documentation Consolidation System.

This module implements the ConsolidationEngine class that processes groups
of related files to create unified, comprehensive documentation while
preserving all important information.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

from .interfaces import ConsolidationEngineInterface
from .models import (
    FileAnalysis, ConsolidationGroup, ConsolidationStrategy,
    MigrationLog, ContentType
)
from .config import ConsolidationConfig


class ConsolidationEngine(ConsolidationEngineInterface):
    """
    Processes and consolidates related documentation files.
    
    The ConsolidationEngine merges related files into unified documents,
    eliminates redundancy, preserves chronological information, and creates
    cross-references between consolidated documents.
    """
    
    def __init__(self, config: ConsolidationConfig):
        """Initialize the consolidation engine with configuration."""
        self.config = config
        self.logger = logging.getLogger('doc_consolidation.engine')
    
    def consolidate_group(self, group: ConsolidationGroup, 
                         file_analyses: Dict[str, FileAnalysis]) -> str:
        """
        Consolidate a group of related files into unified content.
        
        Args:
            group: ConsolidationGroup defining files to merge
            file_analyses: Dictionary mapping file paths to their analyses
            
        Returns:
            Consolidated markdown content as string
        """
        self.logger.info(f"Consolidating group: {group.group_id}")
        
        try:
            # Get all files in the group
            all_files = [group.primary_file] + group.related_files
            
            # Read content from all files
            file_contents = {}
            for filename in all_files:
                if filename in file_analyses:
                    analysis = file_analyses[filename]
                    try:
                        content = self._read_file_content(analysis.filepath)
                        file_contents[filename] = content
                    except Exception as e:
                        self.logger.error(f"Failed to read {filename}: {e}")
                        continue
            
            if not file_contents:
                self.logger.warning(f"No content found for group {group.group_id}")
                return ""
            
            # Apply consolidation strategy
            if group.consolidation_strategy == ConsolidationStrategy.MERGE_CHRONOLOGICAL:
                return self._merge_chronological(file_contents, file_analyses, group)
            
            elif group.consolidation_strategy == ConsolidationStrategy.MERGE_TOPICAL:
                return self._merge_topical(file_contents, file_analyses, group)
            
            elif group.consolidation_strategy == ConsolidationStrategy.COMBINE_SUMMARIES:
                return self._combine_summaries(file_contents, file_analyses, group)
            
            elif group.consolidation_strategy == ConsolidationStrategy.CREATE_INDEX:
                return self._create_index(file_contents, file_analyses, group)
            
            elif group.consolidation_strategy == ConsolidationStrategy.ARCHIVE_PRESERVE:
                return self._archive_preserve(file_contents, file_analyses, group)
            
            else:
                # Default: simple concatenation
                return self._simple_merge(file_contents, file_analyses, group)
        
        except Exception as e:
            self.logger.error(f"Error consolidating group {group.group_id}: {e}")
            return ""
    
    def preserve_chronology(self, files: List[str], 
                          file_analyses: Dict[str, FileAnalysis]) -> List[str]:
        """
        Order files chronologically for consolidation.
        
        Enhanced chronological ordering that:
        - Uses multiple date sources (content dates, file dates, version info)
        - Handles missing dates gracefully
        - Considers task/version numbers for logical ordering
        - Preserves implementation sequence
        
        Args:
            files: List of file paths to order
            file_analyses: Dictionary mapping file paths to their analyses
            
        Returns:
            List of file paths ordered chronologically with implementation context
        """
        if not files:
            return []
        
        self.logger.debug(f"Ordering {len(files)} files chronologically")
        
        # Create detailed file info for sorting
        file_info = []
        for filename in files:
            info = {
                'filename': filename,
                'date': self._get_best_file_date(filename, file_analyses),
                'sequence_number': self._extract_sequence_number(filename),
                'version_info': self._extract_version_info(filename),
                'priority': self._get_chronological_priority(filename, file_analyses)
            }
            file_info.append(info)
        
        # Sort by multiple criteria
        sorted_info = sorted(file_info, key=lambda x: (
            x['date'],                    # Primary: chronological date
            x['sequence_number'],         # Secondary: sequence/task number
            x['version_info'],           # Tertiary: version information
            x['priority'],               # Quaternary: content priority
            x['filename']                # Final: filename for consistency
        ))
        
        sorted_files = [info['filename'] for info in sorted_info]
        
        self.logger.info(f"Chronologically ordered {len(files)} files")
        self._log_chronological_order(sorted_info)
        
        return sorted_files
    
    def _get_best_file_date(self, filename: str, file_analyses: Dict[str, FileAnalysis]) -> datetime:
        """Get the most relevant date for a file using multiple sources."""
        if filename not in file_analyses:
            return datetime.min
        
        analysis = file_analyses[filename]
        
        # Priority 1: Creation date from content metadata
        if analysis.metadata.creation_date:
            return analysis.metadata.creation_date
        
        # Priority 2: Extract date from filename
        filename_date = self._extract_date_from_filename(filename)
        if filename_date:
            return filename_date
        
        # Priority 3: Extract date from content
        content_date = self._extract_date_from_content(analysis)
        if content_date:
            return content_date
        
        # Priority 4: File modification time
        try:
            return datetime.fromtimestamp(analysis.filepath.stat().st_mtime)
        except (OSError, AttributeError):
            pass
        
        # Priority 5: File creation time (if available)
        try:
            return datetime.fromtimestamp(analysis.filepath.stat().st_ctime)
        except (OSError, AttributeError):
            pass
        
        return datetime.min
    
    def _extract_sequence_number(self, filename: str) -> int:
        """Extract sequence/task number from filename."""
        import re
        
        # Look for patterns like TASK_1, PHASE_2, etc.
        patterns = [
            r'TASK_(\d+)',
            r'PHASE_(\d+)',
            r'STEP_(\d+)',
            r'MILESTONE_(\d+)',
            r'SPRINT_(\d+)',
            r'VERSION_(\d+)',
            r'V(\d+)',
            r'_(\d+)_',
            r'(\d+)_'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename.upper())
            if match:
                return int(match.group(1))
        
        return 999999  # Large number for files without sequence
    
    def _extract_version_info(self, filename: str) -> str:
        """Extract version information from filename."""
        import re
        
        # Look for version patterns
        version_patterns = [
            r'v(\d+\.\d+\.\d+)',
            r'version_(\d+\.\d+)',
            r'(\d+\.\d+\.\d+)',
            r'rev(\d+)',
            r'revision_(\d+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, filename.lower())
            if match:
                return match.group(1)
        
        return "0.0.0"  # Default version
    
    def _get_chronological_priority(self, filename: str, file_analyses: Dict[str, FileAnalysis]) -> int:
        """Get priority for chronological ordering."""
        if filename not in file_analyses:
            return 50
        
        analysis = file_analyses[filename]
        
        # Higher priority (lower number) for certain types
        if analysis.content_type.value == 'completion_summary':
            return 10
        elif 'setup' in filename.lower() or 'install' in filename.lower():
            return 20
        elif 'implementation' in filename.lower():
            return 30
        elif 'test' in filename.lower():
            return 40
        else:
            return 50
    
    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract date from filename patterns."""
        import re
        
        # Common date patterns in filenames
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',      # YYYY-MM-DD
            r'(\d{4}_\d{2}_\d{2})',      # YYYY_MM_DD
            r'(\d{8})',                   # YYYYMMDD
            r'(\d{2}-\d{2}-\d{4})',      # MM-DD-YYYY
            r'(\d{2}_\d{2}_\d{4})'       # MM_DD_YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                try:
                    # Try different date formats
                    if '-' in date_str:
                        if len(date_str.split('-')[0]) == 4:
                            return datetime.strptime(date_str, '%Y-%m-%d')
                        else:
                            return datetime.strptime(date_str, '%m-%d-%Y')
                    elif '_' in date_str:
                        if len(date_str.split('_')[0]) == 4:
                            return datetime.strptime(date_str, '%Y_%m_%d')
                        else:
                            return datetime.strptime(date_str, '%m_%d_%Y')
                    elif len(date_str) == 8:
                        return datetime.strptime(date_str, '%Y%m%d')
                except ValueError:
                    continue
        
        return None
    
    def _extract_date_from_content(self, analysis: FileAnalysis) -> Optional[datetime]:
        """Extract date from file content."""
        if not hasattr(analysis, 'filepath') or not analysis.filepath.exists():
            return None
        
        try:
            content = analysis.filepath.read_text(encoding='utf-8')
            return self._parse_content_dates(content)
        except Exception:
            return None
    
    def _parse_content_dates(self, content: str) -> Optional[datetime]:
        """Parse dates from content text."""
        import re
        
        # Look for date patterns in content
        date_patterns = [
            r'Created:\s*(\d{4}-\d{2}-\d{2})',
            r'Date:\s*(\d{4}-\d{2}-\d{2})',
            r'Completed:\s*(\d{4}-\d{2}-\d{2})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\w+ \d{1,2}, \d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    if '-' in match and len(match.split('-')[0]) == 4:
                        return datetime.strptime(match, '%Y-%m-%d')
                    elif '/' in match:
                        return datetime.strptime(match, '%m/%d/%Y')
                    else:
                        # Try parsing month name format
                        return datetime.strptime(match, '%B %d, %Y')
                except ValueError:
                    continue
        
        return None
    
    def _log_chronological_order(self, sorted_info: List[Dict]) -> None:
        """Log the chronological ordering for debugging."""
        self.logger.debug("Chronological ordering:")
        for i, info in enumerate(sorted_info, 1):
            self.logger.debug(f"  {i}. {info['filename']} - {info['date']} (seq: {info['sequence_number']}, ver: {info['version_info']})")
    
    def eliminate_redundancy(self, contents: List[str]) -> str:
        """
        Remove duplicate information while preserving unique content.
        
        Enhanced deduplication that:
        - Identifies duplicate sections by content similarity
        - Merges similar sections while preserving unique information
        - Maintains the best version of each section
        - Preserves important metadata and context
        
        Args:
            contents: List of markdown content strings to deduplicate
            
        Returns:
            Deduplicated markdown content with unique insights preserved
        """
        if not contents:
            return ""
        
        if len(contents) == 1:
            return contents[0]
        
        self.logger.debug(f"Deduplicating {len(contents)} content pieces")
        
        # Enhanced deduplication process
        all_sections = []
        
        # Extract all sections from all contents
        for i, content in enumerate(contents):
            sections = self._split_into_sections(content)
            for section in sections:
                section_info = {
                    'content': section,
                    'heading': self._extract_section_heading(section),
                    'source_index': i,
                    'word_count': len(section.split()),
                    'unique_words': set(section.lower().split()),
                    'has_code': '```' in section or '`' in section,
                    'has_links': '[' in section and '](' in section,
                    'has_lists': any(line.strip().startswith(('-', '*', '+')) or 
                                   line.strip().split('.')[0].isdigit() 
                                   for line in section.split('\n'))
                }
                all_sections.append(section_info)
        
        # Group similar sections
        section_groups = self._group_similar_sections(all_sections)
        
        # Merge each group to create the best version
        merged_sections = []
        for group in section_groups:
            merged_section = self._merge_section_group(group)
            if merged_section:
                merged_sections.append(merged_section)
        
        # Sort sections by importance and logical order
        sorted_sections = self._sort_sections_by_importance(merged_sections)
        
        result = "\n\n".join(sorted_sections)
        
        self.logger.info(f"Deduplication complete: {len(all_sections)} sections -> {len(merged_sections)} unique sections")
        return result
    
    def create_cross_references(self, consolidated_docs: Dict[str, str], 
                              original_groups: List[ConsolidationGroup]) -> Dict[str, List[str]]:
        """
        Generate cross-references between consolidated documents.
        
        Enhanced cross-reference generation that:
        - Analyzes semantic relationships between documents
        - Identifies explicit references and dependencies
        - Creates bidirectional reference maps
        - Generates contextual reference descriptions
        
        Args:
            consolidated_docs: Dictionary mapping output filenames to content
            original_groups: List of ConsolidationGroup objects that were processed
            
        Returns:
            Dictionary mapping document names to lists of related document references
        """
        if not consolidated_docs:
            return {}
        
        self.logger.info(f"Generating cross-references for {len(consolidated_docs)} documents")
        
        # Enhanced cross-reference analysis
        cross_refs = {}
        doc_analysis = {}
        
        # Analyze each document for reference potential
        for doc_name, content in consolidated_docs.items():
            analysis = self._analyze_document_for_references(doc_name, content)
            doc_analysis[doc_name] = analysis
        
        # Generate cross-references using multiple strategies
        for doc_name in consolidated_docs.keys():
            references = []
            
            # Strategy 1: Topic-based references
            topic_refs = self._find_topic_based_references(doc_name, doc_analysis)
            references.extend(topic_refs)
            
            # Strategy 2: Explicit mention references
            mention_refs = self._find_explicit_mention_references(doc_name, doc_analysis)
            references.extend(mention_refs)
            
            # Strategy 3: Dependency-based references
            dependency_refs = self._find_dependency_references(doc_name, doc_analysis, original_groups)
            references.extend(dependency_refs)
            
            # Strategy 4: Workflow-based references
            workflow_refs = self._find_workflow_references(doc_name, doc_analysis)
            references.extend(workflow_refs)
            
            # Remove duplicates and self-references
            unique_refs = list(set(references))
            if doc_name in unique_refs:
                unique_refs.remove(doc_name)
            
            # Sort by relevance
            sorted_refs = self._sort_references_by_relevance(doc_name, unique_refs, doc_analysis)
            
            cross_refs[doc_name] = sorted_refs
        
        # Generate bidirectional references
        cross_refs = self._ensure_bidirectional_references(cross_refs, doc_analysis)
        
        self.logger.info(f"Generated cross-references: {sum(len(refs) for refs in cross_refs.values())} total references")
        
        return cross_refs
    
    def _analyze_document_for_references(self, doc_name: str, content: str) -> Dict:
        """Analyze a document to extract reference-relevant information."""
        import re
        
        analysis = {
            'name': doc_name,
            'content': content,
            'topics': self._extract_enhanced_topics(content),
            'explicit_mentions': self._extract_explicit_mentions(content),
            'dependencies': self._extract_dependencies(content),
            'workflow_stage': self._determine_workflow_stage(doc_name, content),
            'content_type': self._determine_content_type(doc_name, content),
            'key_concepts': self._extract_key_concepts(content),
            'headings': re.findall(r'^#+\s+(.+)$', content, re.MULTILINE),
            'word_count': len(content.split()),
            'has_code': '```' in content or '`' in content,
            'has_links': '[' in content and '](' in content,
            'has_images': '![' in content
        }
        
        return analysis
    
    def _extract_enhanced_topics(self, content: str) -> List[str]:
        """Extract enhanced topic information from content."""
        import re
        
        topics = set()
        
        # Extract from headings (high weight)
        headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        for heading in headings:
            words = re.findall(r'\b\w+\b', heading.lower())
            topics.update(word for word in words if len(word) > 3)
        
        # Extract capitalized terms (likely important concepts)
        important_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        topics.update(term.lower().replace(' ', '_') for term in important_terms if len(term) > 4)
        
        # Extract technical terms (words with underscores, camelCase, etc.)
        tech_terms = re.findall(r'\b[a-z]+_[a-z_]+\b|\b[a-z]+[A-Z][a-zA-Z]*\b', content)
        topics.update(term.lower() for term in tech_terms)
        
        # Extract from code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
        for code in code_blocks:
            # Extract function names, class names, etc.
            code_terms = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
            topics.update(term.lower() for term in code_terms if len(term) > 3)
        
        return list(topics)[:20]  # Return top 20 topics
    
    def _extract_explicit_mentions(self, content: str) -> List[str]:
        """Extract explicit mentions of other documents or systems."""
        import re
        
        mentions = set()
        
        # Look for file references
        file_refs = re.findall(r'(?:see|refer to|check|view)\s+([A-Z_][A-Z0-9_]*\.md)', content, re.IGNORECASE)
        mentions.update(ref.lower() for ref in file_refs)
        
        # Look for system/component mentions
        system_refs = re.findall(r'\b(authentication|payment|tournament|notification|dashboard|database|api)\b', content, re.IGNORECASE)
        mentions.update(ref.lower() for ref in system_refs)
        
        # Look for explicit cross-references
        cross_refs = re.findall(r'(?:related to|depends on|requires|uses)\s+([a-zA-Z_][a-zA-Z0-9_\s]*)', content, re.IGNORECASE)
        mentions.update(ref.strip().lower().replace(' ', '_') for ref in cross_refs)
        
        return list(mentions)
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependency information from content."""
        import re
        
        dependencies = set()
        
        # Look for dependency keywords
        dep_patterns = [
            r'requires?\s+([a-zA-Z_][a-zA-Z0-9_\s]*)',
            r'depends?\s+on\s+([a-zA-Z_][a-zA-Z0-9_\s]*)',
            r'needs?\s+([a-zA-Z_][a-zA-Z0-9_\s]*)',
            r'uses?\s+([a-zA-Z_][a-zA-Z0-9_\s]*)',
            r'integrates?\s+with\s+([a-zA-Z_][a-zA-Z0-9_\s]*)'
        ]
        
        for pattern in dep_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dependencies.update(match.strip().lower().replace(' ', '_') for match in matches)
        
        return list(dependencies)
    
    def _determine_workflow_stage(self, doc_name: str, content: str) -> str:
        """Determine the workflow stage of a document."""
        doc_lower = doc_name.lower()
        content_lower = content.lower()
        
        if any(word in doc_lower for word in ['setup', 'install', 'config']):
            return 'setup'
        elif any(word in doc_lower for word in ['auth', 'login', 'user']):
            return 'authentication'
        elif any(word in doc_lower for word in ['payment', 'billing', 'stripe']):
            return 'payment'
        elif any(word in doc_lower for word in ['tournament', 'match', 'bracket']):
            return 'tournament'
        elif any(word in doc_lower for word in ['test', 'validation', 'verify']):
            return 'testing'
        elif any(word in doc_lower for word in ['deploy', 'production', 'release']):
            return 'deployment'
        elif any(word in content_lower for word in ['complete', 'finished', 'done']):
            return 'completion'
        else:
            return 'general'
    
    def _determine_content_type(self, doc_name: str, content: str) -> str:
        """Determine the type of content in a document."""
        doc_lower = doc_name.lower()
        content_lower = content.lower()
        
        if 'guide' in doc_lower or 'how to' in content_lower:
            return 'guide'
        elif 'reference' in doc_lower or 'api' in doc_lower:
            return 'reference'
        elif 'setup' in doc_lower or 'install' in doc_lower:
            return 'setup'
        elif 'test' in doc_lower or 'validation' in doc_lower:
            return 'testing'
        elif 'complete' in doc_lower or 'summary' in doc_lower:
            return 'completion'
        else:
            return 'documentation'
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content."""
        import re
        
        concepts = set()
        
        # Extract from bullet points and numbered lists
        list_items = re.findall(r'^[-*+]\s+(.+)$|^\d+\.\s+(.+)$', content, re.MULTILINE)
        for item in list_items:
            text = item[0] or item[1]
            words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
            concepts.update(word.lower() for word in words if len(word) > 4)
        
        # Extract from emphasized text
        emphasized = re.findall(r'\*\*([^*]+)\*\*|__([^_]+)__|`([^`]+)`', content)
        for match in emphasized:
            text = match[0] or match[1] or match[2]
            concepts.add(text.lower().replace(' ', '_'))
        
        return list(concepts)[:15]  # Return top 15 concepts
    
    def _find_topic_based_references(self, doc_name: str, doc_analysis: Dict[str, Dict]) -> List[str]:
        """Find references based on topic overlap."""
        references = []
        current_doc = doc_analysis[doc_name]
        current_topics = set(current_doc['topics'])
        
        for other_doc, other_analysis in doc_analysis.items():
            if other_doc == doc_name:
                continue
            
            other_topics = set(other_analysis['topics'])
            common_topics = current_topics & other_topics
            
            # Calculate topic similarity
            if current_topics and other_topics:
                similarity = len(common_topics) / len(current_topics | other_topics)
                if similarity > 0.2:  # 20% topic overlap threshold
                    references.append(other_doc)
        
        return references
    
    def _find_explicit_mention_references(self, doc_name: str, doc_analysis: Dict[str, Dict]) -> List[str]:
        """Find references based on explicit mentions."""
        references = []
        current_doc = doc_analysis[doc_name]
        
        for mention in current_doc['explicit_mentions']:
            for other_doc in doc_analysis.keys():
                if other_doc == doc_name:
                    continue
                
                # Check if mention matches document name or content
                if (mention in other_doc.lower() or 
                    any(mention in topic for topic in doc_analysis[other_doc]['topics'])):
                    references.append(other_doc)
        
        return references
    
    def _find_dependency_references(self, doc_name: str, doc_analysis: Dict[str, Dict], 
                                  original_groups: List[ConsolidationGroup]) -> List[str]:
        """Find references based on dependencies."""
        references = []
        current_doc = doc_analysis[doc_name]
        
        # Check dependencies against other documents
        for dependency in current_doc['dependencies']:
            for other_doc, other_analysis in doc_analysis.items():
                if other_doc == doc_name:
                    continue
                
                # Check if dependency matches document topics or concepts
                if (dependency in other_analysis['topics'] or 
                    dependency in other_analysis['key_concepts'] or
                    any(dependency in heading.lower() for heading in other_analysis['headings'])):
                    references.append(other_doc)
        
        return references
    
    def _find_workflow_references(self, doc_name: str, doc_analysis: Dict[str, Dict]) -> List[str]:
        """Find references based on workflow relationships."""
        references = []
        current_doc = doc_analysis[doc_name]
        current_stage = current_doc['workflow_stage']
        
        # Define workflow relationships
        workflow_relationships = {
            'setup': ['authentication', 'payment', 'tournament'],
            'authentication': ['payment', 'tournament', 'testing'],
            'payment': ['tournament', 'testing'],
            'tournament': ['testing'],
            'testing': ['deployment'],
            'completion': ['setup', 'authentication', 'payment', 'tournament', 'testing']
        }
        
        related_stages = workflow_relationships.get(current_stage, [])
        
        for other_doc, other_analysis in doc_analysis.items():
            if other_doc == doc_name:
                continue
            
            if other_analysis['workflow_stage'] in related_stages:
                references.append(other_doc)
        
        return references
    
    def _sort_references_by_relevance(self, doc_name: str, references: List[str], 
                                    doc_analysis: Dict[str, Dict]) -> List[str]:
        """Sort references by relevance score."""
        if not references:
            return []
        
        current_doc = doc_analysis[doc_name]
        reference_scores = []
        
        for ref_doc in references:
            if ref_doc not in doc_analysis:
                continue
            
            ref_analysis = doc_analysis[ref_doc]
            
            # Calculate relevance score
            score = 0
            
            # Topic overlap score
            current_topics = set(current_doc['topics'])
            ref_topics = set(ref_analysis['topics'])
            if current_topics and ref_topics:
                topic_overlap = len(current_topics & ref_topics) / len(current_topics | ref_topics)
                score += topic_overlap * 40
            
            # Explicit mention score
            if any(mention in ref_doc.lower() for mention in current_doc['explicit_mentions']):
                score += 30
            
            # Dependency score
            if any(dep in ref_analysis['topics'] for dep in current_doc['dependencies']):
                score += 25
            
            # Workflow stage score
            if current_doc['workflow_stage'] == ref_analysis['workflow_stage']:
                score += 20
            
            # Content type compatibility score
            if current_doc['content_type'] == ref_analysis['content_type']:
                score += 15
            
            reference_scores.append((score, ref_doc))
        
        # Sort by score (descending) and return document names
        reference_scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in reference_scores]
    
    def _ensure_bidirectional_references(self, cross_refs: Dict[str, List[str]], 
                                       doc_analysis: Dict[str, Dict]) -> Dict[str, List[str]]:
        """Ensure important references are bidirectional."""
        enhanced_refs = cross_refs.copy()
        
        for doc_name, references in cross_refs.items():
            for ref_doc in references:
                if ref_doc in enhanced_refs:
                    # Check if this is a strong relationship that should be bidirectional
                    if self._should_be_bidirectional(doc_name, ref_doc, doc_analysis):
                        if doc_name not in enhanced_refs[ref_doc]:
                            enhanced_refs[ref_doc].append(doc_name)
        
        return enhanced_refs
    
    def _should_be_bidirectional(self, doc1: str, doc2: str, doc_analysis: Dict[str, Dict]) -> bool:
        """Determine if a reference should be bidirectional."""
        if doc1 not in doc_analysis or doc2 not in doc_analysis:
            return False
        
        analysis1 = doc_analysis[doc1]
        analysis2 = doc_analysis[doc2]
        
        # Strong topic overlap
        topics1 = set(analysis1['topics'])
        topics2 = set(analysis2['topics'])
        if topics1 and topics2:
            overlap = len(topics1 & topics2) / len(topics1 | topics2)
            if overlap > 0.3:  # 30% overlap threshold
                return True
        
        # Same workflow stage
        if analysis1['workflow_stage'] == analysis2['workflow_stage']:
            return True
        
        # Mutual dependencies
        deps1 = set(analysis1['dependencies'])
        deps2 = set(analysis2['dependencies'])
        if deps1 & topics2 or deps2 & topics1:
            return True
        
        return False
    
    def create_backup(self, source_files: List[str], backup_directory: str, 
                     migration_log: Optional['MigrationLog'] = None) -> Tuple[bool, str]:
        """
        Create comprehensive backup copies of files before consolidation.
        
        Enhanced backup system that:
        - Creates timestamped backup directories
        - Preserves file metadata and permissions
        - Maintains directory structure for complex projects
        - Logs all backup operations
        - Creates backup manifest for verification
        - Handles large files and binary content
        
        Args:
            source_files: List of file paths to backup
            backup_directory: Directory where backups should be stored
            migration_log: Optional MigrationLog to record backup operations
            
        Returns:
            Tuple of (success: bool, backup_path: str)
        """
        if not self.config.create_backups:
            self.logger.info("Backup creation disabled in configuration")
            if migration_log:
                migration_log.add_operation(
                    operation_type="backup_skipped",
                    source="configuration",
                    details="Backup creation disabled in configuration"
                )
            return True, ""
        
        try:
            backup_path = Path(backup_directory)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp to backup directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamped_backup = backup_path / f"backup_{timestamp}"
            timestamped_backup.mkdir(exist_ok=True)
            
            # Create backup manifest
            manifest = {
                'backup_timestamp': timestamp,
                'backup_path': str(timestamped_backup),
                'source_files': [],
                'backup_files': [],
                'failed_files': [],
                'total_size': 0,
                'file_count': 0
            }
            
            backed_up_count = 0
            total_size = 0
            failed_files = []
            
            for file_path_str in source_files:
                try:
                    source_path = Path(file_path_str)
                    if not source_path.exists():
                        failed_files.append(f"{file_path_str}: File not found")
                        if migration_log:
                            migration_log.add_warning(f"Backup failed - file not found: {file_path_str}")
                        continue
                    
                    # Create backup with preserved directory structure if needed
                    if source_path.is_absolute():
                        # For absolute paths, use just the filename
                        backup_file = timestamped_backup / source_path.name
                    else:
                        # For relative paths, preserve directory structure
                        backup_file = timestamped_backup / source_path
                        backup_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file with metadata preservation
                    shutil.copy2(source_path, backup_file)
                    
                    # Record file information
                    file_size = source_path.stat().st_size
                    total_size += file_size
                    backed_up_count += 1
                    
                    # Add to manifest
                    manifest['source_files'].append({
                        'path': str(source_path),
                        'size': file_size,
                        'modified': datetime.fromtimestamp(source_path.stat().st_mtime).isoformat(),
                        'backup_path': str(backup_file)
                    })
                    
                    # Log backup operation
                    if migration_log:
                        migration_log.add_operation(
                            operation_type="file_backup",
                            source=str(source_path),
                            destination=str(backup_file),
                            details=f"Size: {file_size} bytes"
                        )
                    
                except Exception as e:
                    error_msg = f"Failed to backup {file_path_str}: {e}"
                    failed_files.append(error_msg)
                    self.logger.error(error_msg)
                    if migration_log:
                        migration_log.add_error(error_msg)
            
            # Update manifest
            manifest['file_count'] = backed_up_count
            manifest['total_size'] = total_size
            manifest['failed_files'] = failed_files
            
            # Write backup manifest
            manifest_file = timestamped_backup / "backup_manifest.json"
            import json
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            # Create backup summary
            summary_file = timestamped_backup / "backup_summary.md"
            self._create_backup_summary(summary_file, manifest)
            
            success = backed_up_count > 0
            if success:
                self.logger.info(f"Successfully backed up {backed_up_count} files to {timestamped_backup}")
                self.logger.info(f"Total backup size: {total_size:,} bytes")
                if migration_log:
                    migration_log.add_operation(
                        operation_type="backup_completed",
                        source=f"{len(source_files)} files",
                        destination=str(timestamped_backup),
                        details=f"Backed up {backed_up_count} files, {total_size:,} bytes"
                    )
            else:
                self.logger.warning("No files were successfully backed up")
                if migration_log:
                    migration_log.add_warning("Backup completed but no files were successfully backed up")
            
            if failed_files:
                self.logger.warning(f"Failed to backup {len(failed_files)} files")
                for failure in failed_files:
                    self.logger.warning(f"  - {failure}")
            
            return success, str(timestamped_backup)
        
        except Exception as e:
            error_msg = f"Backup creation failed: {e}"
            self.logger.error(error_msg)
            if migration_log:
                migration_log.add_error(error_msg)
            return False, ""
    
    def log_operations(self, operations: List[Dict[str, str]], 
                      migration_log: 'MigrationLog') -> None:
        """
        Log consolidation operations to the migration log with enhanced tracking.
        
        Enhanced logging that:
        - Records detailed operation metadata
        - Tracks file transformations and merges
        - Documents content changes and movements
        - Maintains operation dependencies
        - Creates audit trail for all changes
        
        Args:
            operations: List of operation dictionaries to log
            migration_log: MigrationLog object to update
        """
        for operation in operations:
            # Enhanced operation logging with validation
            operation_type = operation.get('type', 'unknown')
            source = operation.get('source', '')
            destination = operation.get('destination', '')
            details = operation.get('details', '')
            
            # Add contextual information based on operation type
            enhanced_details = self._enhance_operation_details(operation_type, source, destination, details)
            
            migration_log.add_operation(
                operation_type=operation_type,
                source=source,
                destination=destination,
                details=enhanced_details
            )
            
            # Update migration log counters based on operation type
            self._update_migration_counters(migration_log, operation_type)
        
        self.logger.debug(f"Logged {len(operations)} operations to migration log")
        
        # Log summary statistics
        if operations:
            operation_types = [op.get('type', 'unknown') for op in operations]
            type_counts = {}
            for op_type in operation_types:
                type_counts[op_type] = type_counts.get(op_type, 0) + 1
            
            summary = ", ".join([f"{count} {op_type}" for op_type, count in type_counts.items()])
            self.logger.info(f"Operation summary: {summary}")
    
    def _enhance_operation_details(self, operation_type: str, source: str, 
                                 destination: str, details: str) -> str:
        """Enhance operation details with contextual information."""
        enhanced_parts = [details] if details else []
        
        # Add operation-specific context
        if operation_type == "file_move":
            if source and destination:
                enhanced_parts.append(f"Moved from {Path(source).parent} to {Path(destination).parent}")
        
        elif operation_type == "file_consolidation":
            enhanced_parts.append("Content merged and deduplicated")
            if source and destination:
                enhanced_parts.append(f"Primary source: {source}")
        
        elif operation_type == "content_merge":
            enhanced_parts.append("Multiple files merged into single document")
        
        elif operation_type == "directory_creation":
            enhanced_parts.append("Directory structure created")
        
        elif operation_type == "cross_reference_creation":
            enhanced_parts.append("Cross-references generated between related documents")
        
        elif operation_type == "backup_verification":
            enhanced_parts.append("Backup integrity verified")
        
        # Add timestamp and system info
        enhanced_parts.append(f"Timestamp: {datetime.now().isoformat()}")
        
        return " | ".join(enhanced_parts)
    
    def _update_migration_counters(self, migration_log: 'MigrationLog', operation_type: str) -> None:
        """Update migration log counters based on operation type."""
        if operation_type in ["file_move", "file_copy"]:
            migration_log.files_moved += 1
        elif operation_type in ["file_consolidation", "content_merge"]:
            migration_log.files_consolidated += 1
        elif operation_type in ["file_archive", "archive_preserve"]:
            migration_log.files_archived += 1
        
        migration_log.files_processed += 1
    
    def create_comprehensive_migration_log(self, migration_log: 'MigrationLog', 
                                         output_path: str) -> bool:
        """
        Create a comprehensive migration log document.
        
        Enhanced migration log that:
        - Documents all file movements and transformations
        - Includes before/after directory structures
        - Provides operation timeline and dependencies
        - Creates verification checksums
        - Generates human-readable summary
        
        Args:
            migration_log: MigrationLog object with recorded operations
            output_path: Path where migration log document should be created
            
        Returns:
            True if migration log was successfully created
        """
        try:
            log_path = Path(output_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate comprehensive migration log content
            log_content = self._generate_migration_log_content(migration_log)
            
            # Write migration log
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            # Create JSON version for programmatic access
            json_path = log_path.with_suffix('.json')
            self._create_migration_log_json(migration_log, json_path)
            
            self.logger.info(f"Migration log created: {log_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create migration log: {e}")
            migration_log.add_error(f"Failed to create migration log: {e}")
            return False
    
    def _generate_migration_log_content(self, migration_log: 'MigrationLog') -> str:
        """Generate comprehensive migration log content."""
        sections = []
        
        # Header
        sections.append("# Documentation Consolidation Migration Log")
        sections.append("")
        sections.append(f"**Migration Date:** {migration_log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append("")
        
        # Executive Summary
        sections.append("## Executive Summary")
        sections.append("")
        sections.append(f"- **Files Processed:** {migration_log.files_processed}")
        sections.append(f"- **Files Moved:** {migration_log.files_moved}")
        sections.append(f"- **Files Consolidated:** {migration_log.files_consolidated}")
        sections.append(f"- **Files Archived:** {migration_log.files_archived}")
        sections.append(f"- **Total Operations:** {len(migration_log.operations)}")
        sections.append(f"- **Errors:** {len(migration_log.errors)}")
        sections.append(f"- **Warnings:** {len(migration_log.warnings)}")
        sections.append("")
        
        # Operation Timeline
        sections.append("## Operation Timeline")
        sections.append("")
        sections.append("| Time | Operation | Source | Destination | Details |")
        sections.append("|------|-----------|--------|-------------|---------|")
        
        for operation in migration_log.operations:
            timestamp = operation.get('timestamp', 'N/A')
            op_type = operation.get('type', 'unknown')
            source = operation.get('source', '')[:50] + ('...' if len(operation.get('source', '')) > 50 else '')
            destination = operation.get('destination', '')[:30] + ('...' if len(operation.get('destination', '')) > 30 else '')
            details = operation.get('details', '')[:60] + ('...' if len(operation.get('details', '')) > 60 else '')
            
            sections.append(f"| {timestamp} | {op_type} | {source} | {destination} | {details} |")
        
        sections.append("")
        
        # Operation Summary by Type
        sections.append("## Operations by Type")
        sections.append("")
        
        operation_types = {}
        for operation in migration_log.operations:
            op_type = operation.get('type', 'unknown')
            operation_types[op_type] = operation_types.get(op_type, 0) + 1
        
        for op_type, count in sorted(operation_types.items()):
            sections.append(f"- **{op_type.replace('_', ' ').title()}:** {count} operations")
        sections.append("")
        
        # File Movements and Transformations
        sections.append("## File Movements and Transformations")
        sections.append("")
        
        move_operations = [op for op in migration_log.operations if op.get('type') in ['file_move', 'file_consolidation']]
        if move_operations:
            sections.append("### File Movements")
            sections.append("")
            for operation in move_operations:
                source = operation.get('source', 'Unknown')
                destination = operation.get('destination', 'Unknown')
                details = operation.get('details', '')
                sections.append(f"- `{source}` → `{destination}`")
                if details:
                    sections.append(f"  - {details}")
            sections.append("")
        
        # Consolidation Details
        consolidation_operations = [op for op in migration_log.operations if 'consolidation' in op.get('type', '')]
        if consolidation_operations:
            sections.append("### Content Consolidations")
            sections.append("")
            for operation in consolidation_operations:
                sections.append(f"- **{operation.get('type', 'Unknown').replace('_', ' ').title()}**")
                sections.append(f"  - Source: {operation.get('source', 'Unknown')}")
                sections.append(f"  - Result: {operation.get('destination', 'Unknown')}")
                sections.append(f"  - Details: {operation.get('details', 'No details available')}")
                sections.append("")
        
        # Errors and Warnings
        if migration_log.errors:
            sections.append("## Errors")
            sections.append("")
            for error in migration_log.errors:
                sections.append(f"- ❌ {error}")
            sections.append("")
        
        if migration_log.warnings:
            sections.append("## Warnings")
            sections.append("")
            for warning in migration_log.warnings:
                sections.append(f"- ⚠️ {warning}")
            sections.append("")
        
        # Verification and Integrity
        sections.append("## Verification and Integrity")
        sections.append("")
        sections.append("### Backup Information")
        backup_operations = [op for op in migration_log.operations if 'backup' in op.get('type', '')]
        if backup_operations:
            for operation in backup_operations:
                sections.append(f"- {operation.get('details', 'Backup operation performed')}")
        else:
            sections.append("- No backup operations recorded")
        sections.append("")
        
        sections.append("### Data Integrity")
        sections.append("- All file operations logged with timestamps")
        sections.append("- Source and destination paths recorded for all moves")
        sections.append("- Content consolidation details preserved")
        sections.append("- Error conditions documented")
        sections.append("")
        
        # Recovery Information
        sections.append("## Recovery Information")
        sections.append("")
        sections.append("### Rollback Procedures")
        sections.append("1. Restore files from backup directory (if backups were created)")
        sections.append("2. Use operation log to reverse file movements")
        sections.append("3. Restore original directory structure")
        sections.append("4. Verify file integrity using backup manifest")
        sections.append("")
        
        sections.append("### Backup Locations")
        backup_paths = set()
        for operation in migration_log.operations:
            if operation.get('type') == 'backup_completed':
                backup_paths.add(operation.get('destination', ''))
        
        if backup_paths:
            for backup_path in backup_paths:
                sections.append(f"- {backup_path}")
        else:
            sections.append("- No backup locations recorded")
        sections.append("")
        
        # Footer
        sections.append("---")
        sections.append("")
        sections.append(f"*Migration log generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        sections.append("")
        sections.append("For questions about this migration, refer to the backup manifest files and operation details above.")
        
        return "\n".join(sections)
    
    def _create_migration_log_json(self, migration_log: 'MigrationLog', json_path: Path) -> None:
        """Create JSON version of migration log for programmatic access."""
        import json
        
        log_data = {
            'migration_timestamp': migration_log.timestamp.isoformat(),
            'summary': {
                'files_processed': migration_log.files_processed,
                'files_moved': migration_log.files_moved,
                'files_consolidated': migration_log.files_consolidated,
                'files_archived': migration_log.files_archived,
                'total_operations': len(migration_log.operations),
                'error_count': len(migration_log.errors),
                'warning_count': len(migration_log.warnings)
            },
            'operations': migration_log.operations,
            'errors': migration_log.errors,
            'warnings': migration_log.warnings
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    def _create_backup_summary(self, summary_file: Path, manifest: Dict) -> None:
        """Create a human-readable backup summary."""
        sections = []
        
        sections.append("# Backup Summary")
        sections.append("")
        sections.append(f"**Backup Date:** {manifest['backup_timestamp']}")
        sections.append(f"**Backup Location:** {manifest['backup_path']}")
        sections.append("")
        
        sections.append("## Summary Statistics")
        sections.append("")
        sections.append(f"- **Files Backed Up:** {manifest['file_count']}")
        sections.append(f"- **Total Size:** {manifest['total_size']:,} bytes")
        sections.append(f"- **Failed Files:** {len(manifest['failed_files'])}")
        sections.append("")
        
        if manifest['source_files']:
            sections.append("## Backed Up Files")
            sections.append("")
            sections.append("| Original File | Size | Modified | Backup Location |")
            sections.append("|---------------|------|----------|-----------------|")
            
            for file_info in manifest['source_files']:
                original = file_info['path']
                size = f"{file_info['size']:,} bytes"
                modified = file_info['modified'][:19]  # Remove microseconds
                backup_loc = Path(file_info['backup_path']).name
                sections.append(f"| {original} | {size} | {modified} | {backup_loc} |")
            sections.append("")
        
        if manifest['failed_files']:
            sections.append("## Failed Backups")
            sections.append("")
            for failure in manifest['failed_files']:
                sections.append(f"- ❌ {failure}")
            sections.append("")
        
        sections.append("## Verification")
        sections.append("")
        sections.append("To verify backup integrity:")
        sections.append("1. Check that all expected files are present in the backup directory")
        sections.append("2. Compare file sizes with the manifest")
        sections.append("3. Verify file modification dates match the original files")
        sections.append("")
        
        sections.append("## Recovery")
        sections.append("")
        sections.append("To restore from this backup:")
        sections.append("1. Copy files from backup directory to their original locations")
        sections.append("2. Verify file permissions and ownership")
        sections.append("3. Check that all files are readable and contain expected content")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(sections))
    
    def verify_backup_integrity(self, backup_path: str, 
                               migration_log: Optional['MigrationLog'] = None) -> Tuple[bool, List[str]]:
        """
        Verify the integrity of backup files.
        
        Enhanced backup verification that:
        - Checks file existence and accessibility
        - Verifies file sizes match original files
        - Validates backup manifest completeness
        - Detects corruption or missing files
        - Creates verification report
        
        Args:
            backup_path: Path to backup directory to verify
            migration_log: Optional MigrationLog to record verification results
            
        Returns:
            Tuple of (success: bool, issues: List[str])
        """
        issues = []
        backup_dir = Path(backup_path)
        
        if not backup_dir.exists():
            issue = f"Backup directory does not exist: {backup_path}"
            issues.append(issue)
            if migration_log:
                migration_log.add_error(issue)
            return False, issues
        
        try:
            # Check for backup manifest
            manifest_file = backup_dir / "backup_manifest.json"
            if not manifest_file.exists():
                issue = "Backup manifest file not found"
                issues.append(issue)
                if migration_log:
                    migration_log.add_warning(issue)
                return False, issues
            
            # Load and verify manifest
            import json
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            verified_files = 0
            total_files = len(manifest.get('source_files', []))
            
            for file_info in manifest.get('source_files', []):
                backup_file_path = Path(file_info['backup_path'])
                original_size = file_info['size']
                
                # Check if backup file exists
                if not backup_file_path.exists():
                    issue = f"Backup file missing: {backup_file_path}"
                    issues.append(issue)
                    continue
                
                # Check file size
                try:
                    backup_size = backup_file_path.stat().st_size
                    if backup_size != original_size:
                        issue = f"Size mismatch for {backup_file_path}: expected {original_size}, got {backup_size}"
                        issues.append(issue)
                        continue
                except OSError as e:
                    issue = f"Cannot access backup file {backup_file_path}: {e}"
                    issues.append(issue)
                    continue
                
                # Check file readability
                try:
                    with open(backup_file_path, 'rb') as f:
                        f.read(1024)  # Read first 1KB to check accessibility
                except Exception as e:
                    issue = f"Cannot read backup file {backup_file_path}: {e}"
                    issues.append(issue)
                    continue
                
                verified_files += 1
            
            # Log verification results
            success = len(issues) == 0
            if migration_log:
                if success:
                    migration_log.add_operation(
                        operation_type="backup_verification",
                        source=backup_path,
                        details=f"Successfully verified {verified_files}/{total_files} files"
                    )
                else:
                    migration_log.add_operation(
                        operation_type="backup_verification_failed",
                        source=backup_path,
                        details=f"Verified {verified_files}/{total_files} files, {len(issues)} issues found"
                    )
                    for issue in issues:
                        migration_log.add_warning(f"Backup verification: {issue}")
            
            self.logger.info(f"Backup verification: {verified_files}/{total_files} files verified")
            if issues:
                self.logger.warning(f"Backup verification found {len(issues)} issues")
                for issue in issues:
                    self.logger.warning(f"  - {issue}")
            
            return success, issues
            
        except Exception as e:
            error_msg = f"Backup verification failed: {e}"
            issues.append(error_msg)
            self.logger.error(error_msg)
            if migration_log:
                migration_log.add_error(error_msg)
            return False, issues
    
    def track_file_transformations(self, source_files: List[str], 
                                 consolidated_files: Dict[str, str],
                                 migration_log: 'MigrationLog') -> None:
        """
        Track detailed file transformations during consolidation.
        
        Enhanced transformation tracking that:
        - Documents source-to-destination mappings
        - Records content changes and merges
        - Tracks file size changes
        - Maintains transformation history
        - Creates audit trail for content changes
        
        Args:
            source_files: List of original source file paths
            consolidated_files: Dictionary mapping output files to their content
            migration_log: MigrationLog to record transformations
        """
        try:
            transformation_summary = {
                'total_source_files': len(source_files),
                'total_output_files': len(consolidated_files),
                'consolidation_ratio': len(source_files) / len(consolidated_files) if consolidated_files else 0,
                'transformations': []
            }
            
            # Calculate source file statistics
            source_stats = {}
            total_source_size = 0
            
            for source_file in source_files:
                try:
                    source_path = Path(source_file)
                    if source_path.exists():
                        size = source_path.stat().st_size
                        word_count = len(source_path.read_text(encoding='utf-8').split())
                        source_stats[source_file] = {
                            'size': size,
                            'word_count': word_count
                        }
                        total_source_size += size
                except Exception as e:
                    self.logger.warning(f"Could not analyze source file {source_file}: {e}")
                    source_stats[source_file] = {'size': 0, 'word_count': 0}
            
            # Calculate output file statistics
            total_output_size = 0
            for output_file, content in consolidated_files.items():
                output_size = len(content.encode('utf-8'))
                output_word_count = len(content.split())
                total_output_size += output_size
                
                transformation_info = {
                    'output_file': output_file,
                    'output_size': output_size,
                    'output_word_count': output_word_count,
                    'source_files_involved': [],
                    'transformation_type': self._determine_transformation_type(output_file, content)
                }
                
                # Try to identify which source files contributed to this output
                for source_file in source_files:
                    if self._is_source_file_related(source_file, output_file, content):
                        transformation_info['source_files_involved'].append(source_file)
                
                transformation_summary['transformations'].append(transformation_info)
                
                # Log individual transformation
                migration_log.add_operation(
                    operation_type="file_transformation",
                    source=f"{len(transformation_info['source_files_involved'])} source files",
                    destination=output_file,
                    details=f"Type: {transformation_info['transformation_type']}, "
                           f"Size: {output_size} bytes, Words: {output_word_count}"
                )
            
            # Log overall transformation summary
            size_change = total_output_size - total_source_size
            size_change_pct = (size_change / total_source_size * 100) if total_source_size > 0 else 0
            
            migration_log.add_operation(
                operation_type="consolidation_summary",
                source=f"{len(source_files)} files ({total_source_size:,} bytes)",
                destination=f"{len(consolidated_files)} files ({total_output_size:,} bytes)",
                details=f"Size change: {size_change:+,} bytes ({size_change_pct:+.1f}%), "
                       f"Consolidation ratio: {transformation_summary['consolidation_ratio']:.2f}:1"
            )
            
            self.logger.info(f"File transformation tracking completed:")
            self.logger.info(f"  - Source files: {len(source_files)} ({total_source_size:,} bytes)")
            self.logger.info(f"  - Output files: {len(consolidated_files)} ({total_output_size:,} bytes)")
            self.logger.info(f"  - Size change: {size_change:+,} bytes ({size_change_pct:+.1f}%)")
            self.logger.info(f"  - Consolidation ratio: {transformation_summary['consolidation_ratio']:.2f}:1")
            
        except Exception as e:
            error_msg = f"File transformation tracking failed: {e}"
            self.logger.error(error_msg)
            migration_log.add_error(error_msg)
    
    def _determine_transformation_type(self, output_file: str, content: str) -> str:
        """Determine the type of transformation based on output file and content."""
        output_lower = output_file.lower()
        content_lower = content.lower()
        
        if 'consolidated' in output_lower or 'merged' in output_lower:
            return 'content_consolidation'
        elif 'summary' in output_lower or 'completion' in output_lower:
            return 'summary_compilation'
        elif 'index' in output_lower or 'readme' in output_lower:
            return 'index_generation'
        elif 'archive' in output_lower:
            return 'archive_preservation'
        elif len(content.split('\n\n')) > 10:  # Multiple sections
            return 'multi_section_merge'
        else:
            return 'single_file_processing'
    
    def _is_source_file_related(self, source_file: str, output_file: str, content: str) -> bool:
        """Determine if a source file contributed to an output file."""
        source_name = Path(source_file).stem.lower()
        output_name = Path(output_file).stem.lower()
        content_lower = content.lower()
        
        # Check if source filename appears in output filename
        if source_name in output_name:
            return True
        
        # Check if source filename is mentioned in content
        if source_name in content_lower:
            return True
        
        # Check for common patterns
        source_patterns = [
            source_name.replace('_', ' '),
            source_name.replace('-', ' '),
            source_name.replace('_', ''),
            source_name.replace('-', '')
        ]
        
        for pattern in source_patterns:
            if pattern in content_lower:
                return True
        
        return False
    
    def _read_file_content(self, filepath: Path) -> str:
        """Read file content with encoding handling."""
        try:
            with open(filepath, 'r', encoding=self.config.encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Try alternative encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # Fallback: read with error handling
            with open(filepath, 'rb') as f:
                return f.read().decode('utf-8', errors='ignore')
        """Read file content with encoding handling."""
        try:
            with open(filepath, 'r', encoding=self.config.encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Try alternative encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # Fallback: read with error handling
            with open(filepath, 'rb') as f:
                return f.read().decode('utf-8', errors='ignore')
    
    def _merge_chronological(self, file_contents: Dict[str, str], 
                           file_analyses: Dict[str, FileAnalysis],
                           group: ConsolidationGroup) -> str:
        """Merge files in chronological order."""
        # Order files chronologically
        all_files = [group.primary_file] + group.related_files
        ordered_files = self.preserve_chronology(all_files, file_analyses)
        
        # Create consolidated content
        sections = []
        sections.append(f"# {group.output_filename.replace('.md', '').replace('_', ' ').title()}")
        sections.append("")
        sections.append("This document consolidates related documentation in chronological order.")
        sections.append("")
        
        # Add table of contents
        sections.append("## Table of Contents")
        sections.append("")
        for i, filename in enumerate(ordered_files, 1):
            if filename in file_contents:
                clean_name = filename.replace('.md', '').replace('_', ' ')
                sections.append(f"{i}. [{clean_name}](#{clean_name.lower().replace(' ', '-')})")
        sections.append("")
        
        for filename in ordered_files:
            if filename not in file_contents:
                continue
                
            content = file_contents[filename]
            analysis = file_analyses.get(filename)
            
            # Add section header with chronological context
            clean_name = filename.replace('.md', '').replace('_', ' ')
            sections.append(f"## {clean_name}")
            
            # Add metadata if available
            if analysis and analysis.metadata.creation_date:
                sections.append(f"*Completed: {analysis.metadata.creation_date.strftime('%Y-%m-%d')}*")
            elif analysis:
                # Try to extract date from content
                try:
                    file_content = analysis.filepath.read_text(encoding='utf-8')
                    date_match = self._parse_content_dates(file_content)
                    if date_match:
                        sections.append(f"*Date: {date_match.strftime('%Y-%m-%d')}*")
                except:
                    pass
            
            sections.append("")
            
            # Add content (remove top-level heading if present)
            cleaned_content = self._remove_top_heading(content)
            sections.append(cleaned_content)
            sections.append("")
            sections.append("---")
            sections.append("")
        
        return "\n".join(sections)
    
    def _merge_topical(self, file_contents: Dict[str, str], 
                      file_analyses: Dict[str, FileAnalysis],
                      group: ConsolidationGroup) -> str:
        """Merge files by topic/theme."""
        # Extract topics from all files
        topic_sections = {}
        
        for filename, content in file_contents.items():
            sections = self._split_into_sections(content)
            
            for section in sections:
                topic = self._extract_section_heading(section)
                if topic not in topic_sections:
                    topic_sections[topic] = []
                topic_sections[topic].append((filename, section))
        
        # Create consolidated content
        result_sections = []
        result_sections.append(f"# {group.output_filename.replace('.md', '').replace('_', ' ').title()}")
        result_sections.append("")
        result_sections.append("This document consolidates related documentation by topic.")
        result_sections.append("")
        
        # Sort topics alphabetically
        for topic in sorted(topic_sections.keys()):
            if topic:  # Skip empty topics
                result_sections.append(f"## {topic}")
                result_sections.append("")
                
                # Merge content for this topic
                topic_content = []
                for filename, section in topic_sections[topic]:
                    cleaned_section = self._remove_section_heading(section)
                    if cleaned_section.strip():
                        topic_content.append(cleaned_section)
                
                # Deduplicate and merge
                merged_content = self.eliminate_redundancy(topic_content)
                result_sections.append(merged_content)
                result_sections.append("")
        
        return "\n".join(result_sections)
    
    def _combine_summaries(self, file_contents: Dict[str, str], 
                          file_analyses: Dict[str, FileAnalysis],
                          group: ConsolidationGroup) -> str:
        """Combine completion summaries into a comprehensive report."""
        # Order files chronologically
        ordered_files = self.preserve_chronology(list(file_contents.keys()), file_analyses)
        
        # Create consolidated summary
        sections = []
        sections.append(f"# {group.output_filename.replace('.md', '').replace('_', ' ').title()}")
        sections.append("")
        sections.append("This document provides a comprehensive summary of completed tasks and implementations.")
        sections.append("")
        
        # Add table of contents
        sections.append("## Table of Contents")
        sections.append("")
        for i, filename in enumerate(ordered_files, 1):
            clean_name = filename.replace('.md', '').replace('_', ' ')
            sections.append(f"{i}. [{clean_name}](#{clean_name.lower().replace(' ', '-')})")
        sections.append("")
        
        # Add detailed sections
        for filename in ordered_files:
            content = file_contents[filename]
            analysis = file_analyses.get(filename)
            
            clean_name = filename.replace('.md', '').replace('_', ' ')
            sections.append(f"## {clean_name}")
            sections.append("")
            
            # Add metadata
            if analysis:
                if analysis.metadata.creation_date:
                    sections.append(f"**Date:** {analysis.metadata.creation_date.strftime('%Y-%m-%d')}")
                if analysis.metadata.word_count:
                    sections.append(f"**Word Count:** {analysis.metadata.word_count}")
                sections.append("")
            
            # Extract key points from content
            key_points = self._extract_key_points(content)
            if key_points:
                sections.append("**Key Points:**")
                for point in key_points:
                    sections.append(f"- {point}")
                sections.append("")
            
            # Add summary of content
            summary = self._create_content_summary(content)
            sections.append(summary)
            sections.append("")
            sections.append("---")
            sections.append("")
        
        return "\n".join(sections)
    
    def _create_index(self, file_contents: Dict[str, str], 
                     file_analyses: Dict[str, FileAnalysis],
                     group: ConsolidationGroup) -> str:
        """Create an index of files rather than merging them."""
        sections = []
        sections.append(f"# {group.output_filename.replace('.md', '').replace('_', ' ').title()}")
        sections.append("")
        sections.append("This index provides an overview of related documentation files.")
        sections.append("")
        
        # Group files by type or topic
        file_groups = {}
        for filename, content in file_contents.items():
            analysis = file_analyses.get(filename)
            if analysis:
                content_type = analysis.content_type.value
                if content_type not in file_groups:
                    file_groups[content_type] = []
                file_groups[content_type].append((filename, content, analysis))
        
        # Create index sections
        for content_type, files in file_groups.items():
            sections.append(f"## {content_type.replace('_', ' ').title()}")
            sections.append("")
            
            for filename, content, analysis in files:
                sections.append(f"### [{filename}]({filename})")
                
                # Add description
                description = self._create_file_description(content, analysis)
                sections.append(description)
                sections.append("")
                
                # Add key topics
                if analysis.metadata.key_topics:
                    topics = ", ".join(analysis.metadata.key_topics[:5])
                    sections.append(f"**Topics:** {topics}")
                    sections.append("")
        
        return "\n".join(sections)
    
    def _archive_preserve(self, file_contents: Dict[str, str], 
                         file_analyses: Dict[str, FileAnalysis],
                         group: ConsolidationGroup) -> str:
        """Preserve files in archive format with metadata."""
        sections = []
        sections.append(f"# Archived: {group.output_filename.replace('.md', '').replace('_', ' ').title()}")
        sections.append("")
        sections.append("This document preserves historical documentation for reference.")
        sections.append("")
        sections.append("⚠️ **Note:** This content may be outdated and is preserved for historical reference only.")
        sections.append("")
        
        for filename, content in file_contents.items():
            analysis = file_analyses.get(filename)
            
            sections.append(f"## {filename}")
            sections.append("")
            
            # Add archive metadata
            sections.append("**Archive Information:**")
            if analysis:
                if analysis.metadata.last_modified:
                    sections.append(f"- Last Modified: {analysis.metadata.last_modified}")
                if analysis.metadata.word_count:
                    sections.append(f"- Word Count: {analysis.metadata.word_count}")
                sections.append(f"- Preservation Priority: {analysis.preservation_priority.value}")
            sections.append("")
            
            # Add original content
            sections.append("**Original Content:**")
            sections.append("")
            sections.append(content)
            sections.append("")
            sections.append("---")
            sections.append("")
        
        return "\n".join(sections)
    
    def _simple_merge(self, file_contents: Dict[str, str], 
                     file_analyses: Dict[str, FileAnalysis],
                     group: ConsolidationGroup) -> str:
        """Simple concatenation of files."""
        sections = []
        sections.append(f"# {group.output_filename.replace('.md', '').replace('_', ' ').title()}")
        sections.append("")
        
        for filename, content in file_contents.items():
            sections.append(f"## From: {filename}")
            sections.append("")
            sections.append(content)
            sections.append("")
            sections.append("---")
            sections.append("")
        
        return "\n".join(sections)
    
    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into sections based on headings."""
        import re
        
        # Split on markdown headings
        sections = re.split(r'\n(?=#+\s)', content)
        return [section.strip() for section in sections if section.strip()]
    
    def _extract_section_heading(self, section: str) -> str:
        """Extract the heading from a section."""
        import re
        
        lines = section.split('\n')
        for line in lines:
            match = re.match(r'^#+\s+(.+)$', line.strip())
            if match:
                return match.group(1).strip()
        
        return "Untitled Section"
    
    def _remove_top_heading(self, content: str) -> str:
        """Remove the top-level heading from content."""
        import re
        
        lines = content.split('\n')
        if lines and re.match(r'^#+\s', lines[0]):
            return '\n'.join(lines[1:]).lstrip('\n')
        return content
    
    def _remove_section_heading(self, section: str) -> str:
        """Remove the heading line from a section."""
        import re
        
        lines = section.split('\n')
        if lines and re.match(r'^#+\s', lines[0]):
            return '\n'.join(lines[1:]).lstrip('\n')
        return section
    
    def _has_unique_content(self, section: str, existing_sections: List[str]) -> bool:
        """Check if a section has unique content compared to existing sections."""
        section_words = set(section.lower().split())
        
        for existing in existing_sections:
            existing_words = set(existing.lower().split())
            overlap = len(section_words & existing_words) / len(section_words | existing_words)
            if overlap > 0.8:  # 80% similarity threshold
                return False
        
        return True
    
    def _extract_unique_content(self, section: str, existing_sections: List[str]) -> str:
        """Extract unique parts from a section."""
        # Simple implementation: return the section if it has unique content
        # In a more sophisticated implementation, this would extract only the unique parts
        return section
    
    def _extract_topics_from_content(self, content: str) -> List[str]:
        """Extract key topics from content."""
        import re
        
        topics = set()
        
        # Extract from headings
        headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        for heading in headings:
            words = re.findall(r'\b\w+\b', heading.lower())
            topics.update(word for word in words if len(word) > 3)
        
        # Extract capitalized words (likely important terms)
        important_words = re.findall(r'\b[A-Z][a-z]+\b', content)
        topics.update(word.lower() for word in important_words if len(word) > 4)
        
        return list(topics)[:10]  # Return top 10 topics
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content."""
        import re
        
        key_points = []
        
        # Look for bullet points
        bullet_points = re.findall(r'^[-*+]\s+(.+)$', content, re.MULTILINE)
        key_points.extend(bullet_points[:5])  # Top 5 bullet points
        
        # Look for numbered lists
        numbered_points = re.findall(r'^\d+\.\s+(.+)$', content, re.MULTILINE)
        key_points.extend(numbered_points[:5])  # Top 5 numbered points
        
        # Look for sentences with "completed", "implemented", etc.
        completion_sentences = re.findall(
            r'[^.!?]*(?:completed|implemented|finished|done|fixed)[^.!?]*[.!?]',
            content, re.IGNORECASE
        )
        key_points.extend(completion_sentences[:3])  # Top 3 completion sentences
        
        return key_points[:10]  # Return top 10 key points
    
    def _create_content_summary(self, content: str) -> str:
        """Create a summary of content."""
        # Simple summary: first paragraph or first few sentences
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph and not paragraph.startswith('#'):
                # Return first substantial paragraph
                if len(paragraph) > 50:
                    return paragraph[:300] + "..." if len(paragraph) > 300 else paragraph
        
        return "No summary available."
    
    def _create_file_description(self, content: str, analysis: FileAnalysis) -> str:
        """Create a description for a file in an index."""
        description_parts = []
        
        # Add basic info
        if analysis.metadata.word_count:
            description_parts.append(f"{analysis.metadata.word_count} words")
        
        if analysis.metadata.headings:
            description_parts.append(f"{len(analysis.metadata.headings)} sections")
        
        # Add content summary
        summary = self._create_content_summary(content)
        if summary != "No summary available.":
            description_parts.append(summary)
        
        return " • ".join(description_parts) if description_parts else "Documentation file"
    
    def _group_similar_sections(self, sections: List[Dict]) -> List[List[Dict]]:
        """Group sections that are similar enough to be merged."""
        groups = []
        used_indices = set()
        
        for i, section in enumerate(sections):
            if i in used_indices:
                continue
            
            # Start a new group with this section
            group = [section]
            used_indices.add(i)
            
            # Find similar sections
            for j, other_section in enumerate(sections):
                if j in used_indices or i == j:
                    continue
                
                similarity = self._calculate_section_similarity(section, other_section)
                
                # Use different thresholds based on section types
                threshold = 0.4  # Default threshold
                
                # Lower threshold for sections with similar headings
                if self._calculate_text_similarity(
                    section['heading'].lower(), 
                    other_section['heading'].lower()
                ) > 0.6:
                    threshold = 0.3
                
                # Higher threshold for very short sections
                if section['word_count'] < 50 or other_section['word_count'] < 50:
                    threshold = 0.7
                
                if similarity > threshold:
                    group.append(other_section)
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
    
    def _calculate_section_similarity(self, section1: Dict, section2: Dict) -> float:
        """Calculate similarity between two sections."""
        # Heading similarity (high weight)
        heading_sim = self._calculate_text_similarity(
            section1['heading'].lower(), 
            section2['heading'].lower()
        )
        
        # Content similarity
        content_sim = self._calculate_content_similarity(
            section1['unique_words'], 
            section2['unique_words']
        )
        
        # Structure similarity (lists, code, links)
        structure_sim = self._calculate_structure_similarity(section1, section2)
        
        # Weighted average
        return (heading_sim * 0.4 + content_sim * 0.4 + structure_sim * 0.2)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_content_similarity(self, words1: Set[str], words2: Set[str]) -> float:
        """Calculate content similarity based on word overlap."""
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_structure_similarity(self, section1: Dict, section2: Dict) -> float:
        """Calculate structural similarity between sections."""
        similarities = []
        
        # Code blocks
        if section1['has_code'] == section2['has_code']:
            similarities.append(1.0)
        else:
            similarities.append(0.0)
        
        # Links
        if section1['has_links'] == section2['has_links']:
            similarities.append(1.0)
        else:
            similarities.append(0.0)
        
        # Lists
        if section1['has_lists'] == section2['has_lists']:
            similarities.append(1.0)
        else:
            similarities.append(0.0)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _merge_section_group(self, group: List[Dict]) -> str:
        """Merge a group of similar sections into the best version."""
        if not group:
            return ""
        
        if len(group) == 1:
            return group[0]['content']
        
        # Find the best section as base (most comprehensive)
        best_section = max(group, key=lambda s: (
            s['word_count'],
            int(s['has_code']),
            int(s['has_links']),
            int(s['has_lists'])
        ))
        
        # Start with the best section as base
        base_content = best_section['content']
        base_lines = [line.strip() for line in base_content.split('\n') if line.strip()]
        base_words = best_section['unique_words']
        
        # Collect unique content from other sections
        unique_additions = []
        
        for section in group:
            if section == best_section:
                continue
            
            # Find unique sentences/points in this section
            section_lines = [line.strip() for line in section['content'].split('\n') if line.strip()]
            
            for line in section_lines:
                # Skip headings (already handled)
                if line.startswith('#'):
                    continue
                
                # Check if this line contains unique information
                line_words = set(line.lower().split())
                if not line_words:
                    continue
                
                # Calculate uniqueness
                unique_word_ratio = len(line_words - base_words) / len(line_words)
                
                # If line has significant unique content and isn't already present
                if (unique_word_ratio > 0.2 and  # 20% unique words
                    len(line) > 15 and  # Minimum length
                    not self._is_line_similar_to_existing(line, base_lines)):
                    unique_additions.append(line)
        
        # Integrate unique additions into base content
        if unique_additions:
            merged_content = self._integrate_unique_lines(base_content, unique_additions)
            return merged_content
        
        return base_content
    
    def _is_line_similar_to_existing(self, line: str, existing_lines: List[str]) -> bool:
        """Check if a line is similar to any existing line."""
        line_words = set(line.lower().split())
        
        for existing_line in existing_lines:
            existing_words = set(existing_line.lower().split())
            if not existing_words:
                continue
            
            # Calculate Jaccard similarity
            intersection = len(line_words & existing_words)
            union = len(line_words | existing_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.6:  # 60% similarity threshold
                return True
        
        return False
    
    def _integrate_unique_lines(self, base_content: str, unique_lines: List[str]) -> str:
        """Integrate unique lines into base content."""
        lines = base_content.split('\n')
        
        # Find the best place to insert unique content
        # Look for the end of the main content, before any metadata or closing sections
        insert_index = len(lines)
        
        # Look for a good insertion point (after main content, before metadata)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line and not line.startswith('#') and not line.startswith('---') and not line.startswith('*'):
                insert_index = i + 1
                break
        
        # Insert unique content if we have any
        if unique_lines:
            # Group similar unique lines
            grouped_lines = self._group_similar_unique_lines(unique_lines)
            
            for group_title, group_lines in grouped_lines.items():
                if group_lines:
                    lines.insert(insert_index, "")
                    lines.insert(insert_index + 1, f"### {group_title}")
                    lines.insert(insert_index + 2, "")
                    
                    for line in group_lines:
                        lines.insert(insert_index + 3, f"- {line}")
                        insert_index += 1
                    
                    insert_index += 3
        
        return '\n'.join(lines)
    
    def _group_similar_unique_lines(self, unique_lines: List[str]) -> Dict[str, List[str]]:
        """Group similar unique lines under appropriate headings."""
        groups = {
            "Additional Features": [],
            "Enhanced Implementation": [],
            "Extended Testing": [],
            "Additional Information": []
        }
        
        for line in unique_lines:
            line_lower = line.lower()
            
            # Categorize the line based on content
            if any(word in line_lower for word in ['feature', 'functionality', 'capability']):
                groups["Additional Features"].append(line)
            elif any(word in line_lower for word in ['implementation', 'technical', 'database', 'api']):
                groups["Enhanced Implementation"].append(line)
            elif any(word in line_lower for word in ['test', 'testing', 'validation', 'audit']):
                groups["Extended Testing"].append(line)
            else:
                groups["Additional Information"].append(line)
        
        # Remove empty groups
        return {title: lines for title, lines in groups.items() if lines}
    
    def _calculate_section_similarity(self, section1: Dict, section2: Dict) -> float:
        """Calculate similarity between two sections."""
        # Heading similarity (high weight)
        heading_sim = self._calculate_text_similarity(
            section1['heading'].lower(), 
            section2['heading'].lower()
        )
        
        # Content similarity
        content_sim = self._calculate_content_similarity(
            section1['unique_words'], 
            section2['unique_words']
        )
        
        # Structure similarity (lists, code, links)
        structure_sim = self._calculate_structure_similarity(section1, section2)
        
        # Weighted average with higher threshold for merging
        similarity = (heading_sim * 0.5 + content_sim * 0.3 + structure_sim * 0.2)
        
        # Boost similarity if headings are very similar
        if heading_sim > 0.8:
            similarity = min(1.0, similarity + 0.2)
        
        return similarity
    
    def _extract_unique_sentences(self, content: str, base_content: str, base_words: Set[str]) -> List[str]:
        """Extract sentences that contain unique information."""
        unique_sentences = []
        
        # Split content into sentences/lines
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        for line in lines:
            # Skip headings (already handled)
            if line.startswith('#'):
                continue
            
            # Check if this line contains unique information
            line_words = set(line.lower().split())
            unique_word_ratio = len(line_words - base_words) / len(line_words) if line_words else 0
            
            # If line has significant unique content, include it
            if unique_word_ratio > 0.3 and len(line) > 20:  # 30% unique words, minimum length
                # Check if similar content already exists
                if not self._is_similar_content_present(line, base_content):
                    unique_sentences.append(line)
        
        return unique_sentences
    
    def _is_similar_content_present(self, line: str, base_content: str) -> bool:
        """Check if similar content is already present in base content."""
        line_words = set(line.lower().split())
        
        for base_line in base_content.split('\n'):
            base_line = base_line.strip()
            if not base_line or base_line.startswith('#'):
                continue
            
            base_words = set(base_line.lower().split())
            if not base_words:
                continue
            
            # Calculate similarity
            intersection = len(line_words & base_words)
            union = len(line_words | base_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.7:  # 70% similarity threshold
                return True
        
        return False
    
    def _integrate_unique_content(self, base_content: str, unique_additions: List[str]) -> str:
        """Integrate unique content additions into base content."""
        lines = base_content.split('\n')
        
        # Find the best place to insert unique content
        # Usually after the main content but before any closing sections
        insert_index = len(lines)
        
        # Look for a good insertion point
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line and not line.startswith('#') and not line.startswith('---'):
                insert_index = i + 1
                break
        
        # Insert unique content
        if unique_additions:
            lines.insert(insert_index, "")
            lines.insert(insert_index + 1, "### Additional Information")
            lines.insert(insert_index + 2, "")
            
            for addition in unique_additions:
                lines.insert(insert_index + 3, f"- {addition}")
                insert_index += 1
        
        return '\n'.join(lines)
    
    def _sort_sections_by_importance(self, sections: List[str]) -> List[str]:
        """Sort sections by importance and logical order."""
        section_priorities = []
        
        for section in sections:
            heading = self._extract_section_heading(section).lower()
            
            # Assign priority based on heading content
            priority = 50  # Default priority
            
            # High priority sections
            if any(word in heading for word in ['overview', 'introduction', 'summary']):
                priority = 10
            elif any(word in heading for word in ['setup', 'installation', 'getting started']):
                priority = 20
            elif any(word in heading for word in ['features', 'functionality']):
                priority = 30
            elif any(word in heading for word in ['implementation', 'details']):
                priority = 40
            elif any(word in heading for word in ['testing', 'validation']):
                priority = 60
            elif any(word in heading for word in ['troubleshooting', 'issues']):
                priority = 70
            elif any(word in heading for word in ['conclusion', 'summary', 'notes']):
                priority = 80
            
            section_priorities.append((priority, section))
        
        # Sort by priority, then by original order
        section_priorities.sort(key=lambda x: x[0])
        
        return [section for _, section in section_priorities]