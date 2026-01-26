"""
Base interfaces for the Documentation Consolidation System components.

This module defines the abstract base classes and interfaces that establish
the contracts for the Content Analyzer, Consolidation Engine, and Structure
Generator components.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from .models import (
        FileAnalysis, ConsolidationGroup, DocumentationStructure,
        Category, ContentMetadata, MigrationLog
    )
    from .config import ConsolidationConfig
except ImportError:
    from doc_consolidation.models import (
        FileAnalysis, ConsolidationGroup, DocumentationStructure,
        Category, ContentMetadata, MigrationLog
    )
    from doc_consolidation.config import ConsolidationConfig


class ContentAnalyzerInterface(ABC):
    """
    Abstract interface for the Content Analyzer component.
    
    The Content Analyzer is responsible for discovering, analyzing, and
    categorizing markdown files in the source directory.
    """
    
    @abstractmethod
    def __init__(self, config: ConsolidationConfig):
        """Initialize the content analyzer with configuration."""
        pass
    
    @abstractmethod
    def discover_files(self, source_directory: str) -> List[Path]:
        """
        Discover all markdown files in the source directory.
        
        Args:
            source_directory: Path to directory to scan for files
            
        Returns:
            List of Path objects for discovered markdown files
        """
        pass
    
    @abstractmethod
    def analyze_file(self, filepath: Path) -> FileAnalysis:
        """
        Analyze a single file to determine its category and metadata.
        
        Args:
            filepath: Path to the file to analyze
            
        Returns:
            FileAnalysis object containing categorization and metadata
        """
        pass
    
    @abstractmethod
    def classify_by_pattern(self, filename: str) -> Tuple[Category, float]:
        """
        Classify a file based on its filename pattern.
        
        Args:
            filename: Name of the file to classify
            
        Returns:
            Tuple of (Category, confidence_score)
        """
        pass
    
    @abstractmethod
    def extract_content_metadata(self, content: str) -> ContentMetadata:
        """
        Extract metadata from file content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            ContentMetadata object with extracted information
        """
        pass
    
    @abstractmethod
    def identify_consolidation_candidates(self, 
                                        analyses: List[FileAnalysis]) -> List[ConsolidationGroup]:
        """
        Identify groups of files that should be consolidated together.
        
        Args:
            analyses: List of FileAnalysis objects for all discovered files
            
        Returns:
            List of ConsolidationGroup objects representing consolidation opportunities
        """
        pass
    
    @abstractmethod
    def validate_analysis(self, analysis: FileAnalysis) -> List[str]:
        """
        Validate an analysis result and return any issues found.
        
        Args:
            analysis: FileAnalysis object to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass


class ConsolidationEngineInterface(ABC):
    """
    Abstract interface for the Consolidation Engine component.
    
    The Consolidation Engine processes groups of related files to create
    unified, comprehensive documentation while preserving all important information.
    """
    
    @abstractmethod
    def __init__(self, config: ConsolidationConfig):
        """Initialize the consolidation engine with configuration."""
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def preserve_chronology(self, files: List[str], 
                          file_analyses: Dict[str, FileAnalysis]) -> List[str]:
        """
        Order files chronologically for consolidation.
        
        Args:
            files: List of file paths to order
            file_analyses: Dictionary mapping file paths to their analyses
            
        Returns:
            List of file paths ordered chronologically
        """
        pass
    
    @abstractmethod
    def eliminate_redundancy(self, contents: List[str]) -> str:
        """
        Remove duplicate information while preserving unique content.
        
        Args:
            contents: List of markdown content strings to deduplicate
            
        Returns:
            Deduplicated markdown content
        """
        pass
    
    @abstractmethod
    def create_cross_references(self, consolidated_docs: Dict[str, str], 
                              original_groups: List[ConsolidationGroup]) -> Dict[str, List[str]]:
        """
        Generate cross-references between consolidated documents.
        
        Args:
            consolidated_docs: Dictionary mapping output filenames to content
            original_groups: List of ConsolidationGroup objects that were processed
            
        Returns:
            Dictionary mapping document names to lists of related document references
        """
        pass
    
    @abstractmethod
    def create_backup(self, source_files: List[str], backup_directory: str) -> bool:
        """
        Create backup copies of files before consolidation.
        
        Args:
            source_files: List of file paths to backup
            backup_directory: Directory where backups should be stored
            
        Returns:
            True if backup was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def log_operations(self, operations: List[Dict[str, str]], 
                      migration_log: MigrationLog) -> None:
        """
        Log consolidation operations to the migration log.
        
        Args:
            operations: List of operation dictionaries to log
            migration_log: MigrationLog object to update
        """
        pass


class StructureGeneratorInterface(ABC):
    """
    Abstract interface for the Structure Generator component.
    
    The Structure Generator creates the final organized documentation hierarchy
    with proper navigation and places all processed files in their appropriate locations.
    """
    
    @abstractmethod
    def __init__(self, config: ConsolidationConfig):
        """Initialize the structure generator with configuration."""
        pass
    
    @abstractmethod
    def create_directory_structure(self, structure: DocumentationStructure) -> bool:
        """
        Create the complete directory hierarchy for organized documentation.
        
        Args:
            structure: DocumentationStructure defining the target organization
            
        Returns:
            True if directory creation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def generate_master_index(self, structure: DocumentationStructure,
                            file_analyses: List[FileAnalysis],
                            consolidated_groups: List[ConsolidationGroup]) -> str:
        """
        Generate the master README.md index for navigation.
        
        Args:
            structure: DocumentationStructure with configuration
            file_analyses: List of all file analyses
            consolidated_groups: List of consolidation groups that were processed
            
        Returns:
            Master index content as markdown string
        """
        pass
    
    @abstractmethod
    def organize_files(self, file_analyses: List[FileAnalysis],
                      consolidated_docs: Dict[str, str],
                      structure: DocumentationStructure) -> Dict[str, str]:
        """
        Move and organize files into their appropriate directory locations.
        
        Args:
            file_analyses: List of FileAnalysis objects for all files
            consolidated_docs: Dictionary of consolidated document content
            structure: DocumentationStructure defining target organization
            
        Returns:
            Dictionary mapping original file paths to new locations
        """
        pass
    
    @abstractmethod
    def create_category_indexes(self, structure: DocumentationStructure,
                              organized_files: Dict[str, str]) -> Dict[str, str]:
        """
        Create index files for each category directory.
        
        Args:
            structure: DocumentationStructure with category definitions
            organized_files: Dictionary mapping files to their new locations
            
        Returns:
            Dictionary mapping category paths to their index content
        """
        pass
    
    @abstractmethod
    def validate_structure(self, structure: DocumentationStructure) -> List[str]:
        """
        Validate the generated documentation structure.
        
        Args:
            structure: DocumentationStructure to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass
    
    @abstractmethod
    def generate_migration_report(self, migration_log: MigrationLog,
                                output_path: str) -> bool:
        """
        Generate a comprehensive report of all consolidation operations.
        
        Args:
            migration_log: MigrationLog with all recorded operations
            output_path: Path where the report should be saved
            
        Returns:
            True if report generation was successful, False otherwise
        """
        pass


class FileSystemInterface(ABC):
    """
    Abstract interface for file system operations.
    
    This interface abstracts file system operations to enable testing
    and provide a consistent API for file operations across components.
    """
    
    @abstractmethod
    def read_file(self, filepath: Path, encoding: str = 'utf-8') -> str:
        """
        Read content from a file.
        
        Args:
            filepath: Path to the file to read
            encoding: Text encoding to use
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If encoding is incorrect
        """
        pass
    
    @abstractmethod
    def write_file(self, filepath: Path, content: str, 
                  encoding: str = 'utf-8') -> bool:
        """
        Write content to a file.
        
        Args:
            filepath: Path where to write the file
            content: Content to write
            encoding: Text encoding to use
            
        Returns:
            True if write was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def copy_file(self, source: Path, destination: Path) -> bool:
        """
        Copy a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if copy was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def move_file(self, source: Path, destination: Path) -> bool:
        """
        Move a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if move was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def create_directory(self, directory: Path) -> bool:
        """
        Create a directory and any necessary parent directories.
        
        Args:
            directory: Directory path to create
            
        Returns:
            True if creation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        """
        List files in a directory matching a pattern.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern to match files
            
        Returns:
            List of matching file paths
        """
        pass
    
    @abstractmethod
    def file_exists(self, filepath: Path) -> bool:
        """
        Check if a file exists.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_file_stats(self, filepath: Path) -> Dict[str, any]:
        """
        Get file statistics (size, modification time, etc.).
        
        Args:
            filepath: Path to the file
            
        Returns:
            Dictionary with file statistics
        """
        pass