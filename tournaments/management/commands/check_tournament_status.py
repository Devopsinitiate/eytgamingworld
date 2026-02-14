"""Management command to check and fix tournament registration status"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tournaments.models import Tournament


class Command(BaseCommand):
    help = 'Check tournament registration status and identify issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            help='Tournament slug to check',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix common registration issues',
        )

    def handle(self, *args, **options):
        slug = options.get('slug')
        fix_issues = options.get('fix', False)
        
        if slug:
            tournaments = Tournament.objects.filter(slug=slug)
        else:
            # Find tournaments with 'underground' in the name
            tournaments = Tournament.objects.filter(name__icontains='underground')
        
        if not tournaments.exists():
            self.stdout.write(self.style.WARNING('No matching tournaments found'))
            return
        
        for tournament in tournaments:
            self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
            self.stdout.write(self.style.SUCCESS(f'Tournament: {tournament.name}'))
            self.stdout.write(f'  Slug: {tournament.slug}')
            self.stdout.write(f'  Status: {tournament.status}')
            self.stdout.write(f'  Public: {tournament.is_public}')
            self.stdout.write(f'  Registration Start: {tournament.registration_start}')
            self.stdout.write(f'  Registration End: {tournament.registration_end}')
            self.stdout.write(f'  Current Time: {timezone.now()}')
            self.stdout.write(f'  Max Participants: {tournament.max_participants}')
            self.stdout.write(f'  Registered: {tournament.total_registered}')
            
            # Check for issues
            issues = []
            fixes_applied = []
            
            # Issue 1: Wrong status
            if tournament.status != 'registration':
                issues.append(f"Status is '{tournament.status}', should be 'registration'")
                if fix_issues:
                    tournament.status = 'registration'
                    fixes_applied.append("Changed status to 'registration'")
            
            # Issue 2: Not public
            if not tournament.is_public:
                issues.append("Tournament is not public")
                if fix_issues:
                    tournament.is_public = True
                    fixes_applied.append("Made tournament public")
            
            # Issue 3: Registration dates not set or invalid
            now = timezone.now()
            if not tournament.registration_start:
                issues.append("Registration start time is not set")
                if fix_issues:
                    tournament.registration_start = now
                    fixes_applied.append("Set registration start to now")
            elif tournament.registration_start > now:
                issues.append(f"Registration hasn't started yet (starts {tournament.registration_start})")
                if fix_issues:
                    tournament.registration_start = now
                    fixes_applied.append("Changed registration start to now (was in the future)")
            
            if not tournament.registration_end:
                issues.append("Registration end time is not set")
                if fix_issues:
                    from datetime import timedelta
                    tournament.registration_end = now + timedelta(days=7)
                    fixes_applied.append("Set registration end to 7 days from now")
            elif tournament.registration_end < now:
                issues.append(f"Registration has ended (ended {tournament.registration_end})")
                if fix_issues:
                    from datetime import timedelta
                    tournament.registration_end = now + timedelta(days=7)
                    fixes_applied.append("Extended registration end to 7 days from now")
            
            # Issue 4: Tournament full
            if tournament.max_participants and tournament.total_registered >= tournament.max_participants:
                issues.append(f"Tournament is full ({tournament.total_registered}/{tournament.max_participants})")
            
            # Display issues
            if issues:
                self.stdout.write(self.style.WARNING(f'\n  Issues found:'))
                for issue in issues:
                    self.stdout.write(self.style.ERROR(f'    ❌ {issue}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'\n  ✓ No issues found - tournament is ready for registration'))
            
            # Apply fixes if requested
            if fix_issues and fixes_applied:
                tournament.save()
                self.stdout.write(self.style.SUCCESS(f'\n  Fixes applied:'))
                for fix in fixes_applied:
                    self.stdout.write(self.style.SUCCESS(f'    ✓ {fix}'))
                self.stdout.write(self.style.SUCCESS(f'\n  Tournament updated successfully!'))
            elif fix_issues and not fixes_applied:
                self.stdout.write(self.style.WARNING(f'\n  No fixable issues found'))
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}\n'))
