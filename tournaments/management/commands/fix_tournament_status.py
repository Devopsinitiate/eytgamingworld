"""
Management command to manually fix tournament status transitions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tournaments.models import Tournament


class Command(BaseCommand):
    help = 'Manually fix tournament status transitions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tournament-slug',
            type=str,
            help='Fix specific tournament by slug',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force status changes regardless of participant count',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        tournament_slug = options.get('tournament_slug')
        now = timezone.now()
        
        self.stdout.write(f"Fixing tournament statuses at {now}")
        
        if tournament_slug:
            # Fix specific tournament
            try:
                tournament = Tournament.objects.get(slug=tournament_slug)
                self.fix_single_tournament(tournament, dry_run, force)
            except Tournament.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Tournament with slug '{tournament_slug}' not found")
                )
                return
        else:
            # Fix all tournaments
            self.fix_all_tournaments(dry_run, force)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN: No changes were made. Remove --dry-run to apply changes.")
            )

    def fix_single_tournament(self, tournament, dry_run, force):
        """Fix a single tournament's status"""
        now = timezone.now()
        
        self.stdout.write(f"\nAnalyzing tournament: {tournament.name}")
        self.stdout.write(f"Current status: {tournament.status}")
        self.stdout.write(f"Registration: {tournament.registration_start} - {tournament.registration_end}")
        self.stdout.write(f"Check-in starts: {tournament.check_in_start}")
        self.stdout.write(f"Tournament starts: {tournament.start_datetime}")
        self.stdout.write(f"Participants: {tournament.total_registered}/{tournament.max_participants}")
        self.stdout.write(f"Checked in: {tournament.total_checked_in}")
        
        # Determine what status it should be
        new_status = self.determine_correct_status(tournament, now, force)
        
        if new_status != tournament.status:
            self.stdout.write(
                self.style.SUCCESS(f"Should be: {new_status}")
            )
            
            if not dry_run:
                old_status = tournament.status
                tournament.status = new_status
                tournament.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f"Updated {tournament.name}: {old_status} → {new_status}")
                )
                
                # Send notifications
                self.send_status_notifications(tournament, new_status)
        else:
            self.stdout.write(
                self.style.SUCCESS("Status is correct - no changes needed")
            )

    def fix_all_tournaments(self, dry_run, force):
        """Fix all tournaments that need status updates"""
        now = timezone.now()
        
        # Get all active tournaments
        tournaments = Tournament.objects.filter(
            status__in=['draft', 'registration', 'check_in']
        ).order_by('start_datetime')
        
        if not tournaments.exists():
            self.stdout.write("No tournaments need status updates")
            return
        
        self.stdout.write(f"Found {tournaments.count()} tournaments to check")
        
        updated_count = 0
        for tournament in tournaments:
            new_status = self.determine_correct_status(tournament, now, force)
            
            if new_status != tournament.status:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{tournament.name}: {tournament.status} → {new_status}"
                    )
                )
                
                if not dry_run:
                    tournament.status = new_status
                    tournament.save()
                    
                    # Send notifications
                    self.send_status_notifications(tournament, new_status)
                    updated_count += 1
        
        if not dry_run and updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"Updated {updated_count} tournaments")
            )

    def determine_correct_status(self, tournament, now, force):
        """Determine what status a tournament should have"""
        
        # If tournament is past estimated end, it should be completed
        if (tournament.estimated_end and 
            now > tournament.estimated_end + timezone.timedelta(hours=24)):
            return 'completed'
        
        # If tournament should have started
        if now >= tournament.start_datetime:
            if force or tournament.total_checked_in >= tournament.min_participants:
                return 'in_progress'
            else:
                # Not enough participants, keep in check_in
                return 'check_in'
        
        # If check-in period should have started
        if now >= tournament.check_in_start and now >= tournament.registration_end:
            return 'check_in'
        
        # If registration period should be open
        if (now >= tournament.registration_start and 
            now < tournament.registration_end):
            return 'registration'
        
        # Otherwise, keep as draft
        return 'draft'

    def send_status_notifications(self, tournament, new_status):
        """Send appropriate notifications for status changes"""
        try:
            if new_status == 'registration':
                from tournaments.tasks import send_registration_opened_notification
                send_registration_opened_notification.delay(tournament.id)
                self.stdout.write("  → Registration notifications queued")
                
            elif new_status == 'check_in':
                from tournaments.tasks import send_check_in_notifications
                send_check_in_notifications.delay(tournament.id)
                self.stdout.write("  → Check-in notifications queued")
                
            elif new_status == 'in_progress':
                # Generate bracket
                from tournaments.services.bracket_generator import BracketGenerator
                generator = BracketGenerator(tournament)
                generator.generate_bracket()
                
                from tournaments.tasks import send_tournament_start_notifications
                send_tournament_start_notifications.delay(tournament.id)
                self.stdout.write("  → Bracket generated and start notifications queued")
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"  → Error sending notifications: {e}")
            )