"""
Django management command to verify backend integration compatibility

Usage:
    python manage.py verify_backend_integration

This command runs comprehensive tests to ensure the enhanced Tournament Detail UI
maintains full compatibility with existing backend systems.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from tournaments.backend_integration_verification import run_backend_integration_verification


class Command(BaseCommand):
    help = 'Verify backend integration compatibility for enhanced Tournament Detail UI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Backend Integration Compatibility Verification...')
        )
        
        try:
            # Run verification in a transaction that gets rolled back
            # This ensures test data doesn't persist in the database
            with transaction.atomic():
                success = run_backend_integration_verification()
                
                # Always rollback the transaction to clean up test data
                transaction.set_rollback(True)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            '\n✅ Backend Integration Compatibility Verification PASSED!\n'
                            'The enhanced Tournament Detail UI maintains full compatibility '
                            'with existing backend systems.'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            '\n❌ Backend Integration Compatibility Verification FAILED!\n'
                            'Some compatibility issues were found. Please review the report above.'
                        )
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Verification failed with error: {str(e)}')
            )