import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament, Participant
from django.utils import timezone

print("=" * 60)
print("TOURNAMENT FULL ISSUE DIAGNOSTIC")
print("=" * 60)

# Get all tournaments in registration status
tournaments = Tournament.objects.filter(status='registration').order_by('-created_at')

if not tournaments.exists():
    print("\n❌ No tournaments in 'registration' status found")
    print("\nAll tournaments:")
    for t in Tournament.objects.all().order_by('-created_at')[:5]:
        print(f"  - {t.name} (Status: {t.status})")
else:
    for tournament in tournaments[:3]:  # Check first 3
        print(f"\n{'=' * 60}")
        print(f"Tournament: {tournament.name}")
        print(f"{'=' * 60}")
        print(f"Status: {tournament.status}")
        print(f"Max Participants: {tournament.max_participants}")
        print(f"Is Team Based: {tournament.is_team_based}")
        print(f"Requires Approval: {tournament.requires_approval}")
        print(f"Registration Fee: ${tournament.registration_fee}")
        
        print(f"\n--- Cached Field ---")
        print(f"total_registered (cached): {tournament.total_registered}")
        
        print(f"\n--- Actual Participant Counts ---")
        all_participants = tournament.participants.all()
        print(f"Total participants (all statuses): {all_participants.count()}")
        
        # Count by status
        for status in ['confirmed', 'pending', 'pending_payment', 'checked_in', 'withdrawn']:
            count = all_participants.filter(status=status).count()
            if count > 0:
                print(f"  - {status}: {count}")
        
        if tournament.is_team_based:
            team_count = tournament.participants.filter(
                team__isnull=False,
                status__in=['confirmed', 'pending_payment', 'pending']
            ).count()
            print(f"\nTeam count (confirmed/pending_payment/pending): {team_count}")
        else:
            user_count = tournament.participants.filter(
                user__isnull=False,
                status__in=['confirmed', 'pending_payment', 'pending']
            ).count()
            print(f"\nUser count (confirmed/pending_payment/pending): {user_count}")
        
        print(f"\n--- Property Values ---")
        print(f"is_full: {tournament.is_full}")
        print(f"is_registration_open: {tournament.is_registration_open}")
        print(f"spots_remaining: {tournament.spots_remaining}")
        print(f"registration_progress: {tournament.registration_progress:.1f}%")
        print(f"get_current_registrations(): {tournament.get_current_registrations()}")
        
        print(f"\n--- Registration Dates ---")
        now = timezone.now()
        print(f"Current time: {now}")
        print(f"Registration start: {tournament.registration_start}")
        print(f"Registration end: {tournament.registration_end}")
        print(f"Registration start <= now: {tournament.registration_start <= now}")
        print(f"now <= Registration end: {now <= tournament.registration_end}")
        
        print(f"\n--- Diagnosis ---")
        if tournament.is_full:
            print("❌ Tournament is marked as FULL")
            if tournament.is_team_based:
                team_count = tournament.participants.filter(
                    team__isnull=False,
                    status__in=['confirmed', 'pending_payment', 'pending']
                ).count()
                print(f"   Reason: {team_count} teams >= {tournament.max_participants} max")
            else:
                user_count = tournament.participants.filter(
                    user__isnull=False,
                    status__in=['confirmed', 'pending_payment', 'pending']
                ).count()
                print(f"   Reason: {user_count} users >= {tournament.max_participants} max")
        else:
            print("✅ Tournament is NOT full")
        
        if not tournament.is_registration_open:
            print("❌ Registration is CLOSED")
            if tournament.status != 'registration':
                print(f"   Reason: Status is '{tournament.status}' (not 'registration')")
            elif not (tournament.registration_start <= now <= tournament.registration_end):
                print(f"   Reason: Current time is outside registration window")
            elif tournament.is_full:
                print(f"   Reason: Tournament is full")
        else:
            print("✅ Registration is OPEN")
        
        # Show actual participants
        if all_participants.exists():
            print(f"\n--- Registered Participants ---")
            for p in all_participants[:10]:
                if tournament.is_team_based:
                    print(f"  - Team: {p.team.name if p.team else 'None'} | Status: {p.status} | Registered: {p.registered_at}")
                else:
                    print(f"  - User: {p.user.username if p.user else 'None'} | Status: {p.status} | Registered: {p.registered_at}")

print(f"\n{'=' * 60}")
print("DIAGNOSTIC COMPLETE")
print(f"{'=' * 60}")
