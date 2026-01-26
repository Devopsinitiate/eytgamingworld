"""
File system operations for the Documentation Consolidation System.

This module provides a concrete implementation of file system operations
that can be used by the consolidation components.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .interfaces import FileSystemInterface


class FileSystem(FileSystemInterface):
    """
    Concrete implementation of file system operations.
    
    This class provides real file system operations for the documentation
    consolidation system, with proper error handling and logging.
    """
    
    def __init__(self):
        """Initialize the file system interface."""
        self.logger = logging.getLogger('doc_consolidation.filesystem')
    
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
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.logger.debug(f"Read file: {filepath} ({len(content)} characters)")
            return content
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {filepath}")
            raise
        
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error reading {filepath}: {e}")
            
            # Try alternative encodings
            for alt_encoding in ['utf-8', 'latin-1', 'cp1252']:
                if alt_encoding != encoding:
                    try:
                        with open(filepath, 'r', encoding=alt_encoding) as f:
                            content = f.read()
                        
                        self.logger.warning(f"Used {alt_encoding} encoding for {filepath}")
                        return content
                    
                    except UnicodeDecodeError:
                        continue
            
            # Final fallback: read with error handling
            try:
                with open(filepath, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')
                
                self.logger.warning(f"Used fallback decoding for {filepath}")
                return content
            
            except Exception:
                raise UnicodeDecodeError(encoding, b'', 0, 1, f"Could not decode {filepath}")
    
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
        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(content)
            
            self.logger.debug(f"Wrote file: {filepath} ({len(content)} characters)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write file {filepath}: {e}")
            return False
    
    def copy_file(self, source: Path, destination: Path) -> bool:
        """
        Copy a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if copy was successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            
            self.logger.debug(f"Copied file: {source} -> {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy {source} to {destination}: {e}")
            return False
    
    def move_file(self, source: Path, destination: Path) -> bool:
        """
        Move a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if move was successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), destination)
            
            self.logger.debug(f"Moved file: {source} -> {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move {source} to {destination}: {e}")
            return False
    
    def create_directory(self, directory: Path) -> bool:
        """
        Create a directory and any necessary parent directories.
        
        Args:
            directory: Directory path to create
            
        Returns:
            True if creation was successful, False otherwise
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            
            self.logger.debug(f"Created directory: {directory}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create directory {directory}: {e}")
            return False
    
    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        """
        List files in a directory matching a pattern.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern to match files
            
        Returns:
            List of matching file paths
        """
        try:
            if not directory.exists():
                self.logger.warning(f"Directory does not exist: {directory}")
                return []
            
            files = list(directory.glob(pattern))
            
            # Filter to only include files (not directories)
            files = [f for f in files if f.is_file()]
            
            self.logger.debug(f"Found {len(files)} files in {directory} matching '{pattern}'")
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list files in {directory}: {e}")
            return []
    
    def file_exists(self, filepath: Path) -> bool:
        """
        Check if a file exists.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        exists = filepath.exists() and filepath.is_file()
        self.logger.debug(f"File exists check: {filepath} -> {exists}")
        return exists
    
    def get_file_stats(self, filepath: Path) -> Dict[str, any]:
        """
        Get file statistics (size, modification time, etc.).
        
        Args:
            filepath: Path to the file
            
        Returns:
            Dictionary with file statistics
        """
        try:
            if not filepath.exists():
                return {}
            
            stat = filepath.stat()
            
            stats = {
                'size': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'is_file': filepath.is_file(),
                'is_directory': filepath.is_dir(),
                'permissions': oct(stat.st_mode)[-3:]
            }
            
            self.logger.debug(f"Got stats for {filepath}: {stats['size']} bytes")
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get stats for {filepath}: {e}")
            return {}
    
    def ensure_directory_exists(self, directory: Path) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory: Directory path to ensure exists
            
        Returns:
            True if directory exists or was created successfully
        """
        if directory.exists():
            return directory.is_dir()
        
        return self.create_directory(directory)
    
    def get_directory_size(self, directory: Path) -> int:
        """
        Get the total size of all files in a directory.
        
        Args:
            directory: Directory to measure
            
        Returns:
            Total size in bytes
        """
        try:
            total_size = 0
            
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        continue
            
            self.logger.debug(f"Directory {directory} total size: {total_size} bytes")
            return total_size
            
        except Exception as e:
            self.logger.error(f"Failed to calculate directory size for {directory}: {e}")
            return 0
    
    def cleanup_empty_directories(self, root_directory: Path) -> int:
        """
        Remove empty directories within a root directory.
        
        Args:
            root_directory: Root directory to clean up
            
        Returns:
            Number of directories removed
        """
        removed_count = 0
        
        try:
            # Get all directories, sorted by depth (deepest first)
            directories = [d for d in root_directory.rglob('*') if d.is_dir()]
            directories.sort(key=lambda x: len(x.parts), reverse=True)
            
            for directory in directories:
                try:
                    # Check if directory is empty
                    if not any(directory.iterdir()):
                        directory.rmdir()
                        removed_count += 1
                        self.logger.debug(f"Removed empty directory: {directory}")
                
                except OSError:
                    # Directory not empty or permission error
                    continue
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} empty directories")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup empty directories in {root_directory}: {e}")
            return 0