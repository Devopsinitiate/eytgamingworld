"""
Configuration management for the Documentation Consolidation System.

This module handles system configuration, settings, and environment variables
for the documentation consolidation process.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .models import Category, ConsolidationStrategy, Priority


@dataclass
class ConsolidationConfig:
    """Configuration settings for the consolidation system."""
    
    # File system settings
    source_directory: str = "."
    target_directory: str = "docs"
    backup_directory: str = "docs_backup"
    create_backups: bool = True
    
    # Processing settings
    file_extensions: List[str] = field(default_factory=lambda: [".md", ".markdown"])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "node_modules/*", "venv/*", ".git/*", "__pycache__/*", 
        "*.pyc", ".pytest_cache/*", ".hypothesis/*"
    ])
    max_file_size_mb: int = 10
    encoding: str = "utf-8"
    
    # Analysis settings
    min_confidence_score: float = 0.7
    enable_content_analysis: bool = True
    extract_metadata: bool = True
    detect_duplicates: bool = True
    
    # Consolidation settings
    enable_consolidation: bool = True
    max_files_per_group: int = 10
    preserve_chronology: bool = True
    create_cross_references: bool = True
    
    # Output settings
    generate_master_index: bool = True
    include_migration_log: bool = True
    create_archive_section: bool = True
    validate_output: bool = True
    
    # Django-specific settings
    follow_django_conventions: bool = True
    include_api_reference: bool = True
    create_quick_start: bool = True
    
    @classmethod
    def from_env(cls) -> 'ConsolidationConfig':
        """Create configuration from environment variables."""
        return cls(
            source_directory=os.getenv('DOC_SOURCE_DIR', '.'),
            target_directory=os.getenv('DOC_TARGET_DIR', 'docs'),
            backup_directory=os.getenv('DOC_BACKUP_DIR', 'docs_backup'),
            create_backups=os.getenv('DOC_CREATE_BACKUPS', 'true').lower() == 'true',
            max_file_size_mb=int(os.getenv('DOC_MAX_FILE_SIZE_MB', '10')),
            encoding=os.getenv('DOC_ENCODING', 'utf-8'),
            min_confidence_score=float(os.getenv('DOC_MIN_CONFIDENCE', '0.7')),
            enable_consolidation=os.getenv('DOC_ENABLE_CONSOLIDATION', 'true').lower() == 'true',
            max_files_per_group=int(os.getenv('DOC_MAX_FILES_PER_GROUP', '10')),
            follow_django_conventions=os.getenv('DOC_DJANGO_CONVENTIONS', 'true').lower() == 'true'
        )
    
    def validate(self) -> List[str]:
        """Validate configuration settings and return any errors."""
        errors = []
        
        if not os.path.exists(self.source_directory):
            errors.append(f"Source directory does not exist: {self.source_directory}")
        
        if self.max_file_size_mb <= 0:
            errors.append("Max file size must be positive")
        
        if not (0.0 <= self.min_confidence_score <= 1.0):
            errors.append("Confidence score must be between 0.0 and 1.0")
        
        if self.max_files_per_group <= 0:
            errors.append("Max files per group must be positive")
        
        return errors


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the documentation consolidation system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, logs to console only.
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('doc_consolidation')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Enhanced configuration patterns for different file types
# Task 2.2: Implement pattern-based file classification
CATEGORY_PATTERNS = {
    Category.SETUP_CONFIG: [
        # Enhanced setup and configuration patterns
        r'.*[Ss]etup.*\.md$',
        r'.*[Ii]nstall.*\.md$',
        r'.*[Cc]onfig.*\.md$',
        r'.*SETUP.*\.md$',
        r'.*_SETUP\.md$',  # Task 2.2: Add *_SETUP.md pattern
        r'.*INSTALLATION.*\.md$',
        r'.*CONFIGURATION.*\.md$',
        r'.*ENVIRONMENT.*\.md$',
        r'.*DEPLOYMENT.*\.md$',
        r'.*NGROK.*\.md$',
        r'.*REDIS.*\.md$',
        r'.*DATABASE.*\.md$',
        r'.*DOCKER.*\.md$',
        r'.*REQUIREMENTS.*\.md$'
    ],
    Category.FEATURE_DOCS: [
        # Enhanced feature documentation patterns
        r'PAYMENT_.*\.md$',      # Task 2.2: Payment feature pattern
        r'TOURNAMENT_.*\.md$',   # Task 2.2: Tournament feature pattern
        r'AUTH.*\.md$',
        r'AUTHENTICATION_.*\.md$',
        r'NOTIFICATION_.*\.md$',
        r'DASHBOARD_.*\.md$',
        r'COACHING_.*\.md$',
        r'TEAM_.*\.md$',
        r'USER_.*\.md$',
        r'PROFILE_.*\.md$',
        r'MESSAGING_.*\.md$',
        r'SEARCH_.*\.md$',
        r'ADMIN_.*\.md$',
        r'REPORT_.*\.md$'
    ],
    Category.IMPLEMENTATION_COMPLETION: [
        # Enhanced completion file patterns
        r'TASK_.*_COMPLETE\.md$',  # Task 2.2: Specific TASK_*_COMPLETE.md pattern
        r'TASK_.*\.md$',
        r'PHASE_.*_COMPLETE\.md$',
        r'PHASE_.*\.md$',
        r'.*_COMPLETE\.md$',
        r'.*COMPLETE\.md$',
        r'.*_SUMMARY\.md$',
        r'.*SUMMARY\.md$',
        r'Complete_Summary\.md$',
        r'IMPLEMENTATION_.*\.md$',
        r'MILESTONE_.*\.md$',
        r'PROGRESS_.*\.md$',
        r'STATUS_.*\.md$'
    ],
    Category.TESTING_VALIDATION: [
        # Enhanced testing documentation patterns
        r'test_.*\.md$',
        r'.*[Tt]est.*\.md$',
        r'.*[Vv]alidation.*\.md$',
        r'.*TEST.*\.md$',
        r'.*TESTING.*\.md$',
        r'.*COVERAGE.*\.md$',
        r'.*REPORT.*\.md$',
        r'.*RESULTS.*\.md$',
        r'.*BENCHMARK.*\.md$',
        r'.*PERFORMANCE.*\.md$',
        r'run_.*\.js$',  # Test runner files
        r'.*_test\.md$',
        r'.*_tests\.md$',
        r'QA_.*\.md$',
        r'QUALITY_.*\.md$'
    ],
    Category.QUICK_REFERENCES: [
        # Enhanced quick reference patterns
        r'QUICK_.*\.md$',
        r'.*QUICK.*\.md$',
        r'.*REFERENCE.*\.md$',
        r'.*[Rr]eference.*\.md$',
        r'START_.*\.md$',
        r'CHEAT_.*\.md$',
        r'.*CHEAT.*\.md$',
        r'GUIDE_.*\.md$',
        r'HOWTO_.*\.md$',
        r'.*HOWTO.*\.md$',
        r'FAQ.*\.md$',
        r'.*FAQ.*\.md$'
    ],
    Category.INTEGRATION_GUIDES: [
        # Enhanced integration guide patterns
        r'.*INTEGRATION.*\.md$',
        r'.*API.*\.md$',
        r'.*[Ii]ntegration.*\.md$',
        r'DEVELOPER_.*\.md$',
        r'.*ROADMAP.*\.md$',
        r'.*ARCHITECTURE.*\.md$',
        r'.*DESIGN.*\.md$',
        r'.*WORKFLOW.*\.md$',
        r'.*PROCESS.*\.md$',
        r'.*GUIDELINES.*\.md$',
        r'.*STANDARDS.*\.md$'
    ]
}

# Consolidation strategies for different patterns
CONSOLIDATION_STRATEGIES = {
    'completion_files': ConsolidationStrategy.COMBINE_SUMMARIES,
    'feature_files': ConsolidationStrategy.MERGE_TOPICAL,
    'setup_files': ConsolidationStrategy.MERGE_CHRONOLOGICAL,
    'test_files': ConsolidationStrategy.CREATE_INDEX,
    'reference_files': ConsolidationStrategy.MERGE_TOPICAL
}

# Priority assignments based on file patterns
PRIORITY_PATTERNS = {
    Priority.CRITICAL: [
        r'README\.md$',
        r'.*CRITICAL.*\.md$',
        r'.*SECURITY.*\.md$'
    ],
    Priority.HIGH: [
        r'.*SETUP.*\.md$',
        r'.*INSTALLATION.*\.md$',
        r'DEVELOPER_.*\.md$',
        r'START_.*\.md$'
    ],
    Priority.MEDIUM: [
        r'.*_COMPLETE.*\.md$',
        r'TASK_.*\.md$',
        r'.*IMPLEMENTATION.*\.md$'
    ],
    Priority.LOW: [
        r'debug_.*\.py$',
        r'test_.*\.html$',
        r'.*[Dd]ebug.*\.md$'
    ],
    Priority.ARCHIVE: [
        r'.*[Oo]ld.*\.md$',
        r'.*[Dd]eprecated.*\.md$',
        r'.*backup.*\.md$'
    ]
}


def get_default_config() -> ConsolidationConfig:
    """Get default configuration with sensible defaults."""
    return ConsolidationConfig()


def load_config_from_file(config_path: str) -> ConsolidationConfig:
    """
    Load configuration from a file (JSON format).
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        ConsolidationConfig instance
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file format is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Create config with defaults, then override with file values
        config = ConsolidationConfig()
        
        # Override with values from config file
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                # Log unknown configuration keys but don't fail
                print(f"Warning: Unknown configuration key '{key}' ignored")
        
        return config
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Error reading configuration file: {e}")


def create_default_config_file(output_path: str) -> None:
    """
    Create a default configuration file for user customization.
    
    Args:
        output_path: Path where to create the config file
    """
    # Create a sample configuration as JSON
    default_config = {
        "source_directory": ".",
        "target_directory": "docs",
        "backup_directory": "docs_backup",
        "create_backups": True,
        "file_extensions": [".md", ".markdown"],
        "exclude_patterns": [
            "node_modules/*", "venv/*", ".git/*", "__pycache__/*", 
            "*.pyc", ".pytest_cache/*", ".hypothesis/*"
        ],
        "max_file_size_mb": 10,
        "encoding": "utf-8",
        "min_confidence_score": 0.7,
        "enable_content_analysis": True,
        "extract_metadata": True,
        "detect_duplicates": True,
        "enable_consolidation": True,
        "max_files_per_group": 10,
        "preserve_chronology": True,
        "create_cross_references": True,
        "generate_master_index": True,
        "include_migration_log": True,
        "create_archive_section": True,
        "validate_output": True,
        "follow_django_conventions": True,
        "include_api_reference": True,
        "create_quick_start": True
    }
    
    # Write JSON configuration file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2)
    
    # Also create a commented version for reference
    comment_path = output_path.replace('.json', '_commented.json')
    config_content = '''{
  // Documentation Consolidation System Configuration
  // 
  // This file contains configuration settings for the documentation
  // consolidation process. Modify these settings as needed for your project.
  
  // File system settings
  "source_directory": ".",              // Directory to scan for files
  "target_directory": "docs",           // Where to create organized structure
  "backup_directory": "docs_backup",    // Backup location for original files
  "create_backups": true,               // Whether to create backups
  
  // File processing settings
  "file_extensions": [".md", ".markdown"],  // File types to process
  "exclude_patterns": [                     // Patterns to exclude
    "node_modules/*", "venv/*", ".git/*", "__pycache__/*", 
    "*.pyc", ".pytest_cache/*", ".hypothesis/*"
  ],
  "max_file_size_mb": 10,               // Maximum file size to process
  "encoding": "utf-8",                  // File encoding
  
  // Analysis settings
  "min_confidence_score": 0.7,          // Minimum confidence for categorization
  "enable_content_analysis": true,      // Analyze file content
  "extract_metadata": true,             // Extract metadata from files
  "detect_duplicates": true,            // Detect duplicate content
  
  // Consolidation settings
  "enable_consolidation": true,         // Enable file consolidation
  "max_files_per_group": 10,           // Maximum files per consolidation group
  "preserve_chronology": true,          // Maintain chronological order
  "create_cross_references": true,      // Generate cross-references
  
  // Output settings
  "generate_master_index": true,        // Create master index file
  "include_migration_log": true,        // Include migration report
  "create_archive_section": true,       // Create archive for old files
  "validate_output": true,              // Validate generated structure
  
  // Django-specific settings
  "follow_django_conventions": true,    // Follow Django documentation patterns
  "include_api_reference": true,        // Include API reference section
  "create_quick_start": true            // Create quick start guide
}'''
    
    with open(comment_path, 'w', encoding='utf-8') as f:
        f.write(config_content)