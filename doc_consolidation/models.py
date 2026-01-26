"""
Core data models for the Documentation Consolidation System.

This module defines the primary data structures used throughout the system
for analyzing, categorizing, and organizing documentation files.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set


class Category(Enum):
    """File categorization types based on content and naming patterns."""
    SETUP_CONFIG = "setup_config"
    FEATURE_DOCS = "feature_docs"
    IMPLEMENTATION_COMPLETION = "implementation_completion"
    TESTING_VALIDATION = "testing_validation"
    QUICK_REFERENCES = "quick_references"
    INTEGRATION_GUIDES = "integration_guides"
    HISTORICAL_ARCHIVE = "historical_archive"
    UNCATEGORIZED = "uncategorized"


class ContentType(Enum):
    """Content type classification for processing strategies."""
    COMPLETION_SUMMARY = "completion_summary"
    FEATURE_GUIDE = "feature_guide"
    SETUP_PROCEDURE = "setup_procedure"
    TEST_REPORT = "test_report"
    QUICK_REFERENCE = "quick_reference"
    INTEGRATION_GUIDE = "integration_guide"
    HISTORICAL_DOC = "historical_doc"
    GENERAL_DOC = "general_doc"


class Priority(Enum):
    """Preservation priority levels for content handling."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ARCHIVE = "archive"


class ConsolidationStrategy(Enum):
    """Strategies for consolidating related files."""
    MERGE_CHRONOLOGICAL = "merge_chronological"
    MERGE_TOPICAL = "merge_topical"
    MERGE_SEQUENTIAL = "merge_sequential"
    COMBINE_SUMMARIES = "combine_summaries"
    CREATE_INDEX = "create_index"
    ARCHIVE_PRESERVE = "archive_preserve"
    NO_CONSOLIDATION = "no_consolidation"


@dataclass
class ContentMetadata:
    """Metadata extracted from file content."""
    creation_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    author: Optional[str] = None
    word_count: int = 0
    key_topics: List[str] = field(default_factory=list)
    internal_links: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    headings: List[str] = field(default_factory=list)
    code_blocks: int = 0
    has_tables: bool = False
    has_images: bool = False


@dataclass
class FileAnalysis:
    """Complete analysis result for a single markdown file."""
    filepath: Path
    filename: str
    category: Category
    content_type: ContentType
    metadata: ContentMetadata
    consolidation_candidates: List[str] = field(default_factory=list)
    preservation_priority: Priority = Priority.MEDIUM
    confidence_score: float = 0.0
    processing_notes: List[str] = field(default_factory=list)
    
    @property
    def file_size(self) -> int:
        """Get file size in bytes."""
        try:
            return self.filepath.stat().st_size
        except (OSError, FileNotFoundError):
            return 0
    
    @property
    def is_outdated(self) -> bool:
        """Check if file appears to be outdated based on metadata."""
        if not self.metadata.last_modified:
            return False
        
        # Consider files older than 6 months as potentially outdated
        cutoff_date = datetime.now().replace(month=datetime.now().month - 6)
        return self.metadata.last_modified < cutoff_date


@dataclass
class ConsolidationGroup:
    """Group of related files identified for consolidation."""
    group_id: str
    category: Category
    primary_file: str
    related_files: List[str] = field(default_factory=list)
    consolidation_strategy: ConsolidationStrategy = ConsolidationStrategy.NO_CONSOLIDATION
    output_filename: str = ""
    cross_references: List[str] = field(default_factory=list)
    merge_order: List[str] = field(default_factory=list)
    preservation_notes: List[str] = field(default_factory=list)
    
    @property
    def total_files(self) -> int:
        """Total number of files in this consolidation group."""
        return 1 + len(self.related_files)  # primary + related
    
    def add_related_file(self, filepath: str) -> None:
        """Add a related file to this consolidation group."""
        if filepath not in self.related_files and filepath != self.primary_file:
            self.related_files.append(filepath)


@dataclass
class DirectoryConfig:
    """Configuration for a documentation directory."""
    path: str
    description: str
    subdirectories: List[str] = field(default_factory=list)
    index_file: Optional[str] = None
    file_patterns: List[str] = field(default_factory=list)


@dataclass
class IndexConfig:
    """Configuration for master index generation."""
    filename: str = "README.md"
    title: str = "Documentation Index"
    include_quick_start: bool = True
    include_search_tips: bool = True
    category_order: List[Category] = field(default_factory=list)
    
    def __post_init__(self):
        """Set default category order if not provided."""
        if not self.category_order:
            self.category_order = [
                Category.SETUP_CONFIG,
                Category.FEATURE_DOCS,
                Category.INTEGRATION_GUIDES,
                Category.TESTING_VALIDATION,
                Category.QUICK_REFERENCES,
                Category.IMPLEMENTATION_COMPLETION,
                Category.HISTORICAL_ARCHIVE
            ]


@dataclass
class ArchiveConfig:
    """Configuration for archive section."""
    path: str = "archive"
    include_deprecated: bool = True
    include_migration_log: bool = True
    retention_policy: str = "preserve_all"


@dataclass
class MigrationLog:
    """Log of all operations performed during consolidation."""
    timestamp: datetime = field(default_factory=datetime.now)
    operations: List[Dict[str, str]] = field(default_factory=list)
    files_processed: int = 0
    files_moved: int = 0
    files_consolidated: int = 0
    files_archived: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_operation(self, operation_type: str, source: str, 
                     destination: str = "", details: str = "") -> None:
        """Add an operation to the migration log."""
        self.operations.append({
            'type': operation_type,
            'source': source,
            'destination': destination,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_error(self, error_message: str) -> None:
        """Add an error to the migration log."""
        self.errors.append(f"{datetime.now().isoformat()}: {error_message}")
    
    def add_warning(self, warning_message: str) -> None:
        """Add a warning to the migration log."""
        self.warnings.append(f"{datetime.now().isoformat()}: {warning_message}")


@dataclass
class DocumentationStructure:
    """Complete documentation structure configuration."""
    root_path: str = "docs/"
    categories: Dict[Category, DirectoryConfig] = field(default_factory=dict)
    master_index: IndexConfig = field(default_factory=IndexConfig)
    archive_section: ArchiveConfig = field(default_factory=ArchiveConfig)
    migration_log: MigrationLog = field(default_factory=MigrationLog)
    
    def __post_init__(self):
        """Initialize default directory structure if not provided."""
        if not self.categories:
            self.categories = {
                Category.SETUP_CONFIG: DirectoryConfig(
                    path="setup",
                    description="Installation and configuration guides",
                    subdirectories=[],
                    file_patterns=["*_SETUP.md", "*setup*", "*install*", "*config*"]
                ),
                Category.FEATURE_DOCS: DirectoryConfig(
                    path="features",
                    description="Feature-specific documentation",
                    subdirectories=["authentication", "payments", "tournaments", 
                                  "notifications", "dashboard"],
                    file_patterns=["PAYMENT_*", "TOURNAMENT_*", "AUTH_*", 
                                 "NOTIFICATION_*", "DASHBOARD_*"]
                ),
                Category.INTEGRATION_GUIDES: DirectoryConfig(
                    path="development",
                    description="Developer guides and integration documentation",
                    subdirectories=[],
                    file_patterns=["*_INTEGRATION*", "*_API*", "*QUICK_START*"]
                ),
                Category.TESTING_VALIDATION: DirectoryConfig(
                    path="testing",
                    description="Testing documentation and reports",
                    subdirectories=["test-reports", "validation-results"],
                    file_patterns=["test_*", "*_TEST*", "*validation*"]
                ),
                Category.QUICK_REFERENCES: DirectoryConfig(
                    path="reference",
                    description="Quick references and troubleshooting guides",
                    subdirectories=[],
                    file_patterns=["QUICK_*", "*_REFERENCE*", "*troubleshoot*"]
                ),
                Category.IMPLEMENTATION_COMPLETION: DirectoryConfig(
                    path="implementation",
                    description="Implementation history and completion records",
                    subdirectories=["completion-summaries", "phase-summaries", 
                                  "task-histories"],
                    file_patterns=["*_COMPLETE*", "TASK_*", "PHASE_*"]
                ),
                Category.HISTORICAL_ARCHIVE: DirectoryConfig(
                    path="archive",
                    description="Historical documentation and deprecated content",
                    subdirectories=["deprecated"],
                    file_patterns=[]
                )
            }
    
    def get_category_path(self, category: Category) -> str:
        """Get the full path for a category directory."""
        if category not in self.categories:
            return f"{self.root_path}uncategorized"
        return f"{self.root_path}{self.categories[category].path}"
    
    def get_all_paths(self) -> Set[str]:
        """Get all directory paths that will be created."""
        paths = {self.root_path}
        
        for category_config in self.categories.values():
            category_path = f"{self.root_path}{category_config.path}"
            paths.add(category_path)
            
            for subdir in category_config.subdirectories:
                paths.add(f"{category_path}/{subdir}")
        
        # Add archive path
        archive_path = f"{self.root_path}{self.archive_section.path}"
        paths.add(archive_path)
        
        return paths