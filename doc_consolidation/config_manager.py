"""
Advanced configuration management for the Documentation Consolidation System.

This module provides advanced configuration management capabilities including
configuration validation, environment variable handling, and configuration
file merging.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .config import ConsolidationConfig, get_default_config
from .models import Category, ConsolidationStrategy, Priority


class ConfigurationManager:
    """
    Advanced configuration manager that handles multiple configuration sources
    and provides validation and merging capabilities.
    """
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.config_sources = []
        self.validation_rules = self._setup_validation_rules()
    
    def load_configuration(self, 
                          config_file: Optional[str] = None,
                          env_prefix: str = "DOC_",
                          cli_overrides: Optional[Dict[str, Any]] = None) -> ConsolidationConfig:
        """
        Load configuration from multiple sources with proper precedence.
        
        Precedence order (highest to lowest):
        1. CLI overrides
        2. Configuration file
        3. Environment variables
        4. Default configuration
        
        Args:
            config_file: Path to configuration file (JSON)
            env_prefix: Prefix for environment variables
            cli_overrides: Dictionary of CLI argument overrides
            
        Returns:
            ConsolidationConfig with merged settings
        """
        # Start with default configuration
        config = get_default_config()
        
        # Apply environment variables
        env_config = self._load_from_environment(env_prefix)
        config = self._merge_configurations(config, env_config)
        
        # Apply configuration file
        if config_file:
            file_config = self._load_from_file(config_file)
            config = self._merge_configurations(config, file_config)
        
        # Apply CLI overrides
        if cli_overrides:
            cli_config = self._create_config_from_dict(cli_overrides)
            config = self._merge_configurations(config, cli_config)
        
        # Validate final configuration
        validation_errors = self.validate_configuration(config)
        if validation_errors:
            raise ValueError(f"Configuration validation failed: {validation_errors}")
        
        return config
    
    def _load_from_environment(self, prefix: str) -> ConsolidationConfig:
        """Load configuration from environment variables."""
        env_values = {}
        
        # Define environment variable mappings
        env_mappings = {
            f"{prefix}SOURCE_DIR": "source_directory",
            f"{prefix}TARGET_DIR": "target_directory",
            f"{prefix}BACKUP_DIR": "backup_directory",
            f"{prefix}CREATE_BACKUPS": "create_backups",
            f"{prefix}MAX_FILE_SIZE_MB": "max_file_size_mb",
            f"{prefix}ENCODING": "encoding",
            f"{prefix}MIN_CONFIDENCE": "min_confidence_score",
            f"{prefix}ENABLE_CONSOLIDATION": "enable_consolidation",
            f"{prefix}MAX_FILES_PER_GROUP": "max_files_per_group",
            f"{prefix}DJANGO_CONVENTIONS": "follow_django_conventions",
            f"{prefix}LOG_LEVEL": "log_level"
        }
        
        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Convert string values to appropriate types
                if config_key in ["create_backups", "enable_consolidation", "follow_django_conventions"]:
                    env_values[config_key] = value.lower() in ["true", "1", "yes", "on"]
                elif config_key in ["max_file_size_mb", "max_files_per_group"]:
                    env_values[config_key] = int(value)
                elif config_key == "min_confidence_score":
                    env_values[config_key] = float(value)
                else:
                    env_values[config_key] = value
        
        return self._create_config_from_dict(env_values)
    
    def _load_from_file(self, config_file: str) -> ConsolidationConfig:
        """Load configuration from a JSON file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return self._create_config_from_dict(config_data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error reading configuration file: {e}")
    
    def _create_config_from_dict(self, config_dict: Dict[str, Any]) -> ConsolidationConfig:
        """Create a ConsolidationConfig from a dictionary."""
        # Start with default config
        config = get_default_config()
        
        # Update with provided values
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def _merge_configurations(self, base_config: ConsolidationConfig, 
                            override_config: ConsolidationConfig) -> ConsolidationConfig:
        """Merge two configurations, with override taking precedence."""
        # Convert to dictionaries for easier merging
        base_dict = asdict(base_config)
        override_dict = asdict(override_config)
        
        # Merge dictionaries
        merged_dict = base_dict.copy()
        for key, value in override_dict.items():
            if value is not None:  # Only override non-None values
                merged_dict[key] = value
        
        # Create new config from merged dictionary
        return self._create_config_from_dict(merged_dict)
    
    def validate_configuration(self, config: ConsolidationConfig) -> List[str]:
        """
        Validate configuration against defined rules.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Use built-in validation first
        errors.extend(config.validate())
        
        # Additional custom validation rules
        for rule_name, rule_func in self.validation_rules.items():
            try:
                rule_errors = rule_func(config)
                if rule_errors:
                    errors.extend([f"{rule_name}: {error}" for error in rule_errors])
            except Exception as e:
                errors.append(f"Validation rule '{rule_name}' failed: {e}")
        
        return errors
    
    def _setup_validation_rules(self) -> Dict[str, callable]:
        """Set up custom validation rules."""
        return {
            "directory_accessibility": self._validate_directory_accessibility,
            "file_extension_validity": self._validate_file_extensions,
            "pattern_consistency": self._validate_pattern_consistency,
            "resource_limits": self._validate_resource_limits
        }
    
    def _validate_directory_accessibility(self, config: ConsolidationConfig) -> List[str]:
        """Validate that directories are accessible."""
        errors = []
        
        # Check source directory
        source_path = Path(config.source_directory)
        if not source_path.exists():
            errors.append(f"Source directory does not exist: {config.source_directory}")
        elif not source_path.is_dir():
            errors.append(f"Source path is not a directory: {config.source_directory}")
        elif not os.access(source_path, os.R_OK):
            errors.append(f"Source directory is not readable: {config.source_directory}")
        
        # Check target directory parent
        target_path = Path(config.target_directory)
        target_parent = target_path.parent
        if not target_parent.exists():
            errors.append(f"Target directory parent does not exist: {target_parent}")
        elif not os.access(target_parent, os.W_OK):
            errors.append(f"Cannot write to target directory parent: {target_parent}")
        
        # Check backup directory parent if backups are enabled
        if config.create_backups:
            backup_path = Path(config.backup_directory)
            backup_parent = backup_path.parent
            if not backup_parent.exists():
                errors.append(f"Backup directory parent does not exist: {backup_parent}")
            elif not os.access(backup_parent, os.W_OK):
                errors.append(f"Cannot write to backup directory parent: {backup_parent}")
        
        return errors
    
    def _validate_file_extensions(self, config: ConsolidationConfig) -> List[str]:
        """Validate file extension configuration."""
        errors = []
        
        if not config.file_extensions:
            errors.append("No file extensions specified")
        
        for ext in config.file_extensions:
            if not ext.startswith('.'):
                errors.append(f"File extension should start with dot: {ext}")
            if len(ext) < 2:
                errors.append(f"File extension too short: {ext}")
        
        return errors
    
    def _validate_pattern_consistency(self, config: ConsolidationConfig) -> List[str]:
        """Validate pattern consistency."""
        errors = []
        
        # Check for conflicting patterns in exclude list
        if config.exclude_patterns:
            for pattern in config.exclude_patterns:
                if not pattern.strip():
                    errors.append("Empty exclude pattern found")
        
        return errors
    
    def _validate_resource_limits(self, config: ConsolidationConfig) -> List[str]:
        """Validate resource limit settings."""
        errors = []
        
        if config.max_file_size_mb <= 0:
            errors.append("Max file size must be positive")
        elif config.max_file_size_mb > 1000:  # 1GB limit
            errors.append("Max file size seems too large (>1GB)")
        
        if config.max_files_per_group <= 0:
            errors.append("Max files per group must be positive")
        elif config.max_files_per_group > 100:
            errors.append("Max files per group seems too large (>100)")
        
        if not (0.0 <= config.min_confidence_score <= 1.0):
            errors.append("Confidence score must be between 0.0 and 1.0")
        
        return errors
    
    def export_configuration(self, config: ConsolidationConfig, 
                           output_path: str, include_comments: bool = True) -> None:
        """
        Export configuration to a file.
        
        Args:
            config: Configuration to export
            output_path: Path where to save the configuration
            include_comments: Whether to include explanatory comments
        """
        config_dict = asdict(config)
        
        if include_comments:
            # Create commented version
            commented_config = self._add_configuration_comments(config_dict)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(commented_config)
        else:
            # Create clean JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
    
    def _add_configuration_comments(self, config_dict: Dict[str, Any]) -> str:
        """Add explanatory comments to configuration."""
        comments = {
            "source_directory": "Directory to scan for documentation files",
            "target_directory": "Where to create organized documentation structure",
            "backup_directory": "Location for backup files",
            "create_backups": "Whether to create backups before processing",
            "file_extensions": "File extensions to process",
            "exclude_patterns": "Patterns to exclude from processing",
            "max_file_size_mb": "Maximum file size to process (MB)",
            "encoding": "Text encoding for file operations",
            "min_confidence_score": "Minimum confidence for automatic categorization",
            "enable_content_analysis": "Whether to analyze file content",
            "extract_metadata": "Whether to extract metadata from files",
            "detect_duplicates": "Whether to detect duplicate content",
            "enable_consolidation": "Whether to consolidate related files",
            "max_files_per_group": "Maximum files per consolidation group",
            "preserve_chronology": "Whether to maintain chronological order",
            "create_cross_references": "Whether to generate cross-references",
            "generate_master_index": "Whether to create master index",
            "include_migration_log": "Whether to include migration report",
            "create_archive_section": "Whether to create archive section",
            "validate_output": "Whether to validate generated structure",
            "follow_django_conventions": "Whether to follow Django conventions",
            "include_api_reference": "Whether to include API reference",
            "create_quick_start": "Whether to create quick start guide"
        }
        
        lines = ["// Documentation Consolidation System Configuration", "//"]
        lines.append("// This file contains all configuration settings for the")
        lines.append("// documentation consolidation process.")
        lines.append("//")
        lines.append("{")
        
        for key, value in config_dict.items():
            comment = comments.get(key, "")
            if comment:
                lines.append(f'  // {comment}')
            
            if isinstance(value, str):
                lines.append(f'  "{key}": "{value}",')
            elif isinstance(value, list):
                lines.append(f'  "{key}": {json.dumps(value)},')
            else:
                lines.append(f'  "{key}": {json.dumps(value)},')
            lines.append("")
        
        # Remove trailing comma from last item
        if lines[-2].endswith(','):
            lines[-2] = lines[-2][:-1]
        
        lines.append("}")
        
        return '\n'.join(lines)


# Global configuration manager instance
config_manager = ConfigurationManager()