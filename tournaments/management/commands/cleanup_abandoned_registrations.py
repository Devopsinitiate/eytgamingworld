"""
Management command to clean up abandoned tournament registrations
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tournaments.models import Participant


class Command(BaseCommand):
    help = 'Clean up abandoned tournament registrations (pending_payment for more than 24 hours)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Number of hours after which to consider a registration abandoned (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Find abandoned registrations
        abandoned = Participant.objects.filter(
            status='pending_payment',
            registered_at__lt=cutoff_time
        ).select_related('tournament', 'user')
        
        count = abandoned.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No abandoned registrations found'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would delete {count} abandoned registrations:'))
            for participant in abandoned:
                user_name = participant.user.get_display_name() if participant.user else participant.team.name
                self.stdout.write(f'  - {user_name} from {participant.tournament.name} (registered {participant.registered_at})')
        else:
            self.stdout.write(f'Deleting {count} abandoned registrations...')
            deleted_count, _ = abandoned.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {deleted_count} abandoned registrations'))
