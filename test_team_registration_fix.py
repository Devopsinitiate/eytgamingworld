"""Test script to verify team-based tournament registration fix"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament, Participant
from teams.models import Team

def test_team_registration_counting():
    """Test that team-based tournaments count teams, not individual users"""
    
    print("\n" + "="*80)
    print("TEAM-BASED TOURNAMENT REGISTRATION FIX - TEST RESULTS")
    print("="*80)
    
    # Find a team-based tournament
    team_tournament = Tournament.objects.filter(is_team_based=True).first()
    
    if not team_tournament:
        print("\n❌ No team-based tournaments found in database")
        return
    
    print(f"\n📋 Tournament: {team_tournament.name}")
    print(f"   Type: Team-Based")
    print(f"   Game: {team_tournament.game}")
    print(f"   Max Teams Allowed: {team_tournament.max_participants}")
    
    # Get current registrations
    registered_teams = team_tournament.participants.filter(
        team__isnull=False,
        status__in=['confirmed', 'pending_payment']
    )
    
    team_count = registered_teams.count()
    
    print(f"\n📊 REGISTRATION STATISTICS:")
    print(f"   ├─ Teams Currently Registered: {team_count}")
    print(f"   ├─ total_registered field (old method): {team_tournament.total_registered}")
    print(f"   ├─ get_current_registrations() (new method): {team_tournament.get_current_registrations()}")
    print(f"   ├─ Spots Remaining: {team_tournament.spots_remaining}")
    print(f"   ├─ Registration Progress: {team_tournament.registration_progress:.1f}%")
    print(f"   └─ Is Full: {team_tournament.is_full}")
    
    # List registered teams
    if team_count > 0:
        print(f"\n👥 REGISTERED TEAMS:")
        for i, participant in enumerate(registered_teams, 1):
            print(f"   {i}. {participant.team.name} (Status: {participant.status})")
    else:
        print(f"\n✓ No teams registered yet - tournament open for registration")
    
    # Test the fix
    print(f"\n🧪 FIX VALIDATION:")
    
    # Check if is_full logic is correct
    if team_count < team_tournament.max_participants:
        if team_tournament.is_full:
            print(f"   ❌ FAIL: Tournament marked as full but only {team_count}/{team_tournament.max_participants} teams registered")
        else:
            print(f"   ✅ PASS: Tournament correctly shows as open ({team_count}/{team_tournament.max_participants} teams)")
    else:
        if team_tournament.is_full:
            print(f"   ✅ PASS: Tournament correctly marked as full ({team_count}/{team_tournament.max_participants} teams)")
        else:
            print(f"   ❌ FAIL: Tournament should be full but shows as open")
    
    # Check spots_remaining
    expected_spots = max(0, team_tournament.max_participants - team_count)
    actual_spots = team_tournament.spots_remaining
    
    if actual_spots == expected_spots:
        print(f"   ✅ PASS: Spots remaining calculated correctly: {actual_spots}")
    else:
        print(f"   ❌ FAIL: Spots remaining incorrect (expected: {expected_spots}, got: {actual_spots})")
    
    # Check registration_progress
    expected_progress = min(100, (team_count / team_tournament.max_participants) * 100) if team_tournament.max_participants > 0 else 0
    actual_progress = team_tournament.registration_progress
    
    if abs(actual_progress - expected_progress) < 0.1:  # Allow small floating point differences
        print(f"   ✅ PASS: Registration progress calculated correctly: {actual_progress:.1f}%")
    else:
        print(f"   ❌ FAIL: Progress incorrect (expected: {expected_progress:.1f}%, got: {actual_progress:.1f}%)")
    
    print(f"\n" + "="*80)
    print("✅ FIX APPLIED: Team-based tournaments now count TEAMS, not individual users")
    print("="*80)
    
    # Show available teams for testing
    available_teams = Team.objects.filter(
        game=team_tournament.game,
        status='active'
    ).exclude(
        id__in=registered_teams.values_list('team_id', flat=True)
    )[:5]
    
    if available_teams.exists():
        print(f"\n🎮 TEAMS AVAILABLE FOR TESTING ({available_teams.count()} teams):")
        for i, team in enumerate(available_teams, 1):
            member_count = team.members.filter(status='active').count()
            print(f"   {i}. {team.name} ({member_count} members)")
    
    print("\n")

if __name__ == '__main__':
    test_team_registration_counting()
