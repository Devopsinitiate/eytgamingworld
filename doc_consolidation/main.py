"""
Main application entry point for the Documentation Consolidation System.

This module provides the primary interface for running the documentation
consolidation process, including command-line interface and orchestration
of all system components.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional, Dict
from collections import defaultdict

try:
    from .analyzer import ContentAnalyzer
    from .engine import ConsolidationEngine
    from .generator import StructureGenerator
    from .models import DocumentationStructure, MigrationLog
    from .config import ConsolidationConfig, setup_logging, get_default_config, load_config_from_file
    from .config_manager import config_manager
    from .filesystem import FileSystem
    from .pipeline import DocumentationPipeline, PipelineResult
except ImportError:
    from analyzer import ContentAnalyzer
    from engine import ConsolidationEngine
    from generator import StructureGenerator
    from models import DocumentationStructure, MigrationLog
    from config import ConsolidationConfig, setup_logging, get_default_config, load_config_from_file
    from config_manager import config_manager
    from filesystem import FileSystem
    from pipeline import DocumentationPipeline, PipelineResult


class ProgressReporter:
    """Progress reporting utility for user feedback."""
    
    def __init__(self, total_steps: int = 100, show_progress: bool = True):
        self.total_steps = total_steps
        self.current_step = 0
        self.show_progress = show_progress
        self.start_time = time.time()
        self.last_update = 0
    
    def update(self, step: int, message: str = ""):
        """Update progress and display to user."""
        self.current_step = step
        
        if not self.show_progress:
            return
        
        # Only update every 5% or if message changes
        progress_percent = (step / self.total_steps) * 100
        if progress_percent - self.last_update >= 5 or message:
            elapsed = time.time() - self.start_time
            
            # Create progress bar
            bar_length = 40
            filled_length = int(bar_length * step // self.total_steps)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            
            # Estimate remaining time
            if step > 0:
                eta = (elapsed / step) * (self.total_steps - step)
                eta_str = f" ETA: {int(eta)}s" if eta > 0 else ""
            else:
                eta_str = ""
            
            print(f'\r|{bar}| {progress_percent:.1f}%{eta_str} {message}', end='', flush=True)
            self.last_update = progress_percent
    
    def finish(self, message: str = "Complete"):
        """Finish progress reporting."""
        if self.show_progress:
            elapsed = time.time() - self.start_time
            print(f'\r|{"█" * 40}| 100.0% ({elapsed:.1f}s) {message}')


class DocumentationConsolidator:
    """
    Main orchestrator for the documentation consolidation process.
    
    This class provides a high-level interface that uses the DocumentationPipeline
    to coordinate all components and provide user-friendly progress reporting.
    """
    
    def __init__(self, config: Optional[ConsolidationConfig] = None, show_progress: bool = True):
        """
        Initialize the documentation consolidator.
        
        Args:
            config: Configuration object. If None, uses default configuration.
            show_progress: Whether to show progress indicators to user.
        """
        self.config = config or get_default_config()
        self.show_progress = show_progress
        self.logger = setup_logging(
            log_level="INFO",
            log_file="doc_consolidation.log" if self.config.create_backups else None
        )
        
        # Initialize the processing pipeline
        self.pipeline = DocumentationPipeline(self.config)
        
        # Initialize progress reporter
        self.progress = ProgressReporter(show_progress=self.show_progress)
        
        self.logger.info("Documentation Consolidator initialized")
    
    def run_consolidation(self) -> bool:
        """
        Run the complete documentation consolidation process.
        
        Returns:
            True if consolidation completed successfully, False otherwise
        """
        self.logger.info("Starting documentation consolidation process")
        
        try:
            # Define progress callback
            def progress_callback(step: int, total: int, message: str):
                progress_percent = int((step / total) * 100)
                self.progress.update(progress_percent, message)
            
            # Run the pipeline
            result = self.pipeline.run(progress_callback if self.show_progress else None)
            
            if result.success:
                self.progress.finish("Documentation consolidation completed!")
                self.logger.info("Documentation consolidation completed successfully")
                self._print_summary(result)
                return True
            else:
                if self.show_progress:
                    print(f"\nConsolidation failed: {result.errors[-1] if result.errors else 'Unknown error'}")
                self.logger.error("Documentation consolidation failed")
                self._print_summary(result)
                return False
            
        except Exception as e:
            error_msg = f"Consolidation process failed: {e}"
            self.logger.error(error_msg)
            if self.show_progress:
                print(f"\nError: {error_msg}")
            return False
    
    def _print_summary(self, result: PipelineResult):
        """Print a summary of the consolidation process."""
        print("\n" + "="*60)
        print("DOCUMENTATION CONSOLIDATION SUMMARY")
        print("="*60)
        print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Files Processed: {result.files_processed}")
        print(f"Files Moved: {result.files_moved}")
        print(f"Files Consolidated: {result.files_consolidated}")
        print(f"Files Archived: {result.files_archived}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"Target Directory: {result.target_directory}")
        
        if result.errors:
            print("\nERRORS:")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more")
        
        if result.warnings:
            print("\nWARNINGS:")
            for warning in result.warnings[:5]:  # Show first 5 warnings
                print(f"  - {warning}")
            if len(result.warnings) > 5:
                print(f"  ... and {len(result.warnings) - 5} more")
        
        if result.success:
            print("\nNext Steps:")
            print("1. Review the generated documentation structure")
            print("2. Check the migration report in docs/archive/migration-log.md")
            print("3. Update any build scripts to use the new structure")
            print("4. Verify that all important information was preserved")
        else:
            print("\nTroubleshooting:")
            print("1. Check the error messages above")
            print("2. Review the log file for detailed information")
            print("3. Ensure source directory contains markdown files")
            print("4. Verify file permissions and disk space")
        
        print("="*60)
    
    def get_statistics(self) -> Dict[str, any]:
        """Get detailed processing statistics."""
        return self.pipeline.get_processing_statistics()


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Documentation Consolidation System - Organize scattered markdown files into a structured documentation hierarchy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m doc_consolidation.main                    # Use default settings
  python -m doc_consolidation.main --source ./docs   # Specify source directory
  python -m doc_consolidation.main --no-backup       # Skip backup creation
  python -m doc_consolidation.main --dry-run         # Preview changes only
  python -m doc_consolidation.main --config config.json  # Use custom config
  python -m doc_consolidation.main --quiet           # Minimal output
  python -m doc_consolidation.main --verbose         # Detailed output

Configuration:
  The system can be configured via command-line arguments, environment variables,
  or configuration files. Command-line arguments take precedence over config files,
  which take precedence over environment variables.

  Environment variables:
    DOC_SOURCE_DIR, DOC_TARGET_DIR, DOC_BACKUP_DIR, DOC_CREATE_BACKUPS,
    DOC_ENABLE_CONSOLIDATION, DOC_LOG_LEVEL

Output:
  The system creates a structured documentation hierarchy in the target directory
  with organized files, master index, and migration report. All operations are
  logged and can be reviewed in the migration report.
        """
    )
    
    # Input/Output options
    io_group = parser.add_argument_group('Input/Output Options')
    io_group.add_argument(
        '--source', '-s',
        default='.',
        help='Source directory to scan for documentation files (default: current directory)'
    )
    
    io_group.add_argument(
        '--target', '-t',
        default='docs',
        help='Target directory for organized documentation (default: docs)'
    )
    
    io_group.add_argument(
        '--backup-dir', '-b',
        default='docs_backup',
        help='Directory for backup files (default: docs_backup)'
    )
    
    # Processing options
    process_group = parser.add_argument_group('Processing Options')
    process_group.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup files (not recommended)'
    )
    
    process_group.add_argument(
        '--no-consolidation',
        action='store_true',
        help='Skip file consolidation, only organize existing files'
    )
    
    process_group.add_argument(
        '--no-cross-references',
        action='store_true',
        help='Skip generating cross-references between documents'
    )
    
    process_group.add_argument(
        '--max-file-size',
        type=int,
        default=10,
        help='Maximum file size to process in MB (default: 10)'
    )
    
    # Output control options
    output_group = parser.add_argument_group('Output Control')
    output_group.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    output_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output, only show errors and final summary'
    )
    
    output_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output with detailed progress information'
    )
    
    output_group.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar display'
    )
    
    # Advanced options
    advanced_group = parser.add_argument_group('Advanced Options')
    advanced_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without actually modifying files'
    )
    
    advanced_group.add_argument(
        '--config',
        help='Path to configuration file (JSON format)'
    )
    
    advanced_group.add_argument(
        '--create-config',
        help='Create a default configuration file at the specified path'
    )
    
    advanced_group.add_argument(
        '--force',
        action='store_true',
        help='Force operation even if target directory exists'
    )
    
    advanced_group.add_argument(
        '--exclude-patterns',
        nargs='+',
        help='Additional file patterns to exclude (e.g., "*.tmp" "debug_*")'
    )
    
    return parser


def main():
    """Main entry point for the command-line interface."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # Handle special commands first
        if args.create_config:
            config_manager.export_configuration(
                get_default_config(), 
                args.create_config, 
                include_comments=True
            )
            print(f"Default configuration file created at: {args.create_config}")
            print("Edit this file to customize the consolidation process.")
            sys.exit(0)
        
        # Determine output verbosity
        if args.quiet:
            log_level = 'ERROR'
            show_progress = False
        elif args.verbose:
            log_level = 'DEBUG'
            show_progress = not args.no_progress
        else:
            log_level = args.log_level
            show_progress = not args.no_progress
        
        # Create configuration using advanced configuration manager
        cli_overrides = {
            'source_directory': args.source,
            'target_directory': args.target,
            'backup_directory': args.backup_dir,
            'create_backups': not args.no_backup,
            'enable_consolidation': not args.no_consolidation,
            'create_cross_references': not args.no_cross_references,
            'max_file_size_mb': args.max_file_size,
        }
        
        # Add additional exclude patterns if specified
        if args.exclude_patterns:
            cli_overrides['exclude_patterns'] = args.exclude_patterns
        
        try:
            config = config_manager.load_configuration(
                config_file=args.config,
                env_prefix="DOC_",
                cli_overrides=cli_overrides
            )
            if not args.quiet and args.config:
                print(f"Loaded configuration from: {args.config}")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)
        
        # Check if target directory exists and handle force option
        target_path = Path(config.target_directory)
        if target_path.exists() and not args.force and not args.dry_run:
            print(f"Target directory '{config.target_directory}' already exists.")
            print("Use --force to overwrite or choose a different target directory.")
            sys.exit(1)
        
        # Set up logging
        setup_logging(log_level)
        
        if args.dry_run:
            print("DRY RUN MODE: Analyzing files and showing what would be done...")
            print("=" * 60)
            
            # Create a dry-run version of the consolidator
            config.create_backups = False  # Don't create backups in dry run
            consolidator = DocumentationConsolidator(config, show_progress=show_progress)
            
            # Run analysis phase only
            discovered_files = consolidator.analyzer.discover_files(config.source_directory)
            if not discovered_files:
                print("No files found for processing.")
                sys.exit(0)
            
            print(f"Found {len(discovered_files)} files to process:")
            for file_path in discovered_files[:10]:  # Show first 10
                print(f"  - {file_path}")
            if len(discovered_files) > 10:
                print(f"  ... and {len(discovered_files) - 10} more files")
            
            # Analyze files
            file_analyses = []
            for file_path in discovered_files:
                try:
                    analysis = consolidator.analyzer.analyze_file(file_path)
                    file_analyses.append(analysis)
                except Exception as e:
                    print(f"  Warning: Could not analyze {file_path}: {e}")
            
            # Show categorization results
            from collections import defaultdict
            categories = defaultdict(list)
            for analysis in file_analyses:
                categories[analysis.category].append(analysis.filename)
            
            print(f"\nFile categorization results:")
            for category, files in categories.items():
                print(f"  {category.value}: {len(files)} files")
                for file in files[:3]:  # Show first 3 files per category
                    print(f"    - {file}")
                if len(files) > 3:
                    print(f"    ... and {len(files) - 3} more")
            
            # Show consolidation opportunities
            consolidation_groups = consolidator.analyzer.identify_consolidation_candidates(file_analyses)
            if consolidation_groups:
                print(f"\nConsolidation opportunities: {len(consolidation_groups)} groups")
                for group in consolidation_groups[:5]:  # Show first 5 groups
                    print(f"  - {group.group_id}: {group.total_files} files -> {group.output_filename}")
                if len(consolidation_groups) > 5:
                    print(f"  ... and {len(consolidation_groups) - 5} more groups")
            else:
                print("\nNo consolidation opportunities identified.")
            
            # Show what directories would be created
            doc_structure = DocumentationStructure()
            paths = doc_structure.get_all_paths()
            print(f"\nDirectories that would be created:")
            for path in sorted(paths):
                print(f"  - {path}")
            
            print("\n" + "=" * 60)
            print("Dry run complete. Use without --dry-run to perform actual consolidation.")
            sys.exit(0)
        
        # Print startup information
        if not args.quiet:
            print("Documentation Consolidation System")
            print("=" * 40)
            print(f"Source directory: {config.source_directory}")
            print(f"Target directory: {config.target_directory}")
            print(f"Backup directory: {config.backup_directory}")
            print(f"Create backups: {config.create_backups}")
            print(f"Enable consolidation: {config.enable_consolidation}")
            print("=" * 40)
        
        # Run consolidation
        consolidator = DocumentationConsolidator(config, show_progress=show_progress)
        success = consolidator.run_consolidation()
        
        if not args.quiet:
            if success:
                print("\n✓ Documentation consolidation completed successfully!")
                print(f"Check the results in: {config.target_directory}")
            else:
                print("\n✗ Documentation consolidation failed!")
                print("Check the logs for details.")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nConsolidation interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()