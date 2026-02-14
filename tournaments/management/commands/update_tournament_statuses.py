"""
Management command to manually update tournament statuses.
This can be run manually or via cron job as a backup to Celery.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tournaments.models import Tournament


class Command(BaseCommand):
    help = 'Update tournament statuses based on current time and schedule'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        now = timezone.now()
        
        self.stdout.write(f"Checking tournament statuses at {now}")
        
        # Check for tournaments that should open registration
        draft_tournaments = Tournament.objects.filter(
            status='draft',
            registration_start__lte=now,
            registration_end__gt=now
        )
        
        if draft_tournaments.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Found {draft_tournaments.count()} tournaments ready to open registration:"
                )
            )
            
            for tournament in draft_tournaments:
                if verbose:
                    self.stdout.write(f"  - {tournament.name} (slug: {tournament.slug})")
                
                if not dry_run:
                    tournament.status = 'registration'
                    tournament.published_at = now
                    tournament.save()
                    
                    # Send notification
                    from tournaments.tasks import send_registration_opened_notification
                    send_registration_opened_notification.delay(tournament.id)
        else:
            self.stdout.write("No tournaments ready to open registration")
        
        # Check for tournaments that should move to check-in
        registration_tournaments = Tournament.objects.filter(
            status='registration',
            registration_end__lte=now,
            check_in_start__lte=now
        )
        
        if registration_tournaments.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Found {registration_tournaments.count()} tournaments ready for check-in:"
                )
            )
            
            for tournament in registration_tournaments:
                if verbose:
                    self.stdout.write(f"  - {tournament.name} (slug: {tournament.slug})")
                
                if not dry_run:
                    tournament.status = 'check_in'
                    tournament.save()
                    
                    # Send notification
                    from tournaments.tasks import send_check_in_notifications
                    send_check_in_notifications.delay(tournament.id)
        else:
            self.stdout.write("No tournaments ready for check-in")
        
        # Check for tournaments that should start
        checkin_tournaments = Tournament.objects.filter(
            status='check_in',
            start_datetime__lte=now
        )
        
        ready_to_start = []
        not_ready = []
        
        for tournament in checkin_tournaments:
            if tournament.total_checked_in >= tournament.min_participants:
                ready_to_start.append(tournament)
            else:
                not_ready.append(tournament)
        
        if ready_to_start:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Found {len(ready_to_start)} tournaments ready to start:"
                )
            )
            
            for tournament in ready_to_start:
                if verbose:
                    self.stdout.write(
                        f"  - {tournament.name} ({tournament.total_checked_in} checked in)"
                    )
                
                if not dry_run:
                    tournament.start_tournament()
                    
                    # Send notification
                    from tournaments.tasks import send_tournament_start_notifications
                    send_tournament_start_notifications.delay(tournament.id)
        
        if not_ready:
            self.stdout.write(
                self.style.WARNING(
                    f"Found {len(not_ready)} tournaments past start time but not enough participants:"
                )
            )
            
            for tournament in not_ready:
                if verbose:
                    self.stdout.write(
                        f"  - {tournament.name} ({tournament.total_checked_in}/{tournament.min_participants} checked in)"
                    )
        
        if not ready_to_start and not not_ready:
            self.stdout.write("No tournaments ready to start")
        
        # Check for tournaments that should be completed
        expired_tournaments = Tournament.objects.filter(
            status='in_progress',
            estimated_end__lte=now - timezone.timedelta(hours=24)  # 24 hours past estimated end
        )
        
        if expired_tournaments.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Found {expired_tournaments.count()} tournaments that may need completion:"
                )
            )
            
            for tournament in expired_tournaments:
                if verbose:
                    self.stdout.write(f"  - {tournament.name} (estimated end: {tournament.estimated_end})")
                
                if not dry_run:
                    tournament.status = 'completed'
                    tournament.actual_end = now
                    tournament.save()
        else:
            self.stdout.write("No tournaments need automatic completion")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN: No changes were made. Remove --dry-run to apply changes.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Tournament status updates completed!")
            )