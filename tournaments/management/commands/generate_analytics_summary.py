"""
Django management command to generate analytics summary reports.
This command should be run periodically (e.g., via cron) to aggregate analytics data.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from tournaments.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate analytics summary reports for specified period'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            choices=['hourly', 'daily', 'weekly', 'monthly'],
            default='daily',
            help='Period type for summary generation (default: daily)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing summaries'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        period_type = options['period']
        force = options['force']
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(f"Generating {period_type} analytics summary...")
        
        try:
            # Generate summary report
            AnalyticsService.generate_summary_report(period_type=period_type)
            
            success_msg = f"Successfully generated {period_type} analytics summary"
            self.stdout.write(self.style.SUCCESS(success_msg))
            
            if verbose:
                self.stdout.write(f"Summary generated at {timezone.now()}")
                
        except Exception as e:
            error_msg = f"Error generating {period_type} analytics summary: {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
            raise