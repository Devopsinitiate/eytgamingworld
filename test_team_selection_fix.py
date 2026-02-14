#!/usr/bin/env python
"""
Test the team selection fix for tournament registration
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember

User = get_user_model()

def test_team_selection_data():
    print("🧪 TESTING TEAM SELECTION DATA AVAILABILITY")
    print("=" * 60)
    
    # Get a test user
    try:
        user = User.objects.get(username='eyt')
        print(f"✅ Using test user: {user.username}")
    except User.DoesNotExist:
        print("❌ Test user 'eyt' not found")
        return
    
    # Get a team-based tournament
    team_tournament = Tournament.objects.filter(
        is_team_based=True,
        status='registration',
        is_public=True
    ).first()
    
    if not team_tournament:
        print("❌ No team-based tournaments available for testing")
        return
    
    print(f"🏆 Testing with tournament: {team_tournament.name} (slug: {team_tournament.slug})")
    print(f"   Game: {team_tournament.game.name}")
    print(f"   Team size required: {team_tournament.team_size}")
    
    # Check user's eligible teams (same logic as in the view)
    eligible_teams = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=team_tournament.game
    ).distinct()
    
    print(f"\n👥 ELIGIBLE TEAMS FOR USER")
    print(f"   Found {eligible_teams.count()} eligible teams")
    
    for team in eligible_teams:
        print(f"   - Team: {team.name} (ID: {team.id})")
        print(f"     Game: {team.game.name}")
        print(f"     Status: {team.status}")
        
        # Check user's role in team
        membership = TeamMember.objects.filter(
            team=team,
            user=user,
            status='active'
        ).first()
        
        if membership:
            print(f"     User role: {membership.role}")
            print(f"     Can register: {'Yes' if membership.role in ['captain', 'co_captain'] else 'No'}")
        else:
            print(f"     User role: Not found")
        
        # Check team size
        active_members = team.members.filter(status='active').count()
        print(f"     Active members: {active_members}")
        print(f"     Meets requirement: {'Yes' if active_members >= team_tournament.team_size else 'No'}")
        
        # Check if already registered
        existing_participant = Participant.objects.filter(
            tournament=team_tournament,
            team=team
        ).first()
        
        if existing_participant:
            print(f"     Already registered: Yes (Status: {existing_participant.status})")
        else:
            print(f"     Already registered: No")
    
    # Test the view context data
    print(f"\n📝 TESTING VIEW CONTEXT DATA")
    
    # Simulate the view logic for getting user teams
    from tournaments.views import TournamentContextMixin
    
    class TestMixin(TournamentContextMixin):
        def __init__(self):
            pass
    
    # This simulates what the registration view does
    user_teams = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=team_tournament.game
    ).distinct()
    
    print(f"   View would show {user_teams.count()} teams")
    
    if user_teams.exists():
        print(f"✅ Teams available for selection in form")
        for team in user_teams:
            print(f"   - {team.name} (members: {team.members.filter(status='active').count()})")
    else:
        print(f"❌ No teams would be shown in form")
    
    # Test tournament registration eligibility
    print(f"\n🔍 TESTING REGISTRATION ELIGIBILITY")
    can_register, message = team_tournament.can_user_register(user)
    print(f"   Can register: {can_register}")
    print(f"   Message: {message}")
    
    if can_register and user_teams.exists():
        print(f"✅ User should be able to see and use team selection")
    else:
        print(f"❌ User will not be able to complete registration")
        if not can_register:
            print(f"   Reason: {message}")
        if not user_teams.exists():
            print(f"   Reason: No eligible teams")

def test_javascript_data_format():
    print(f"\n🔧 TESTING JAVASCRIPT DATA FORMAT")
    print("=" * 40)
    
    # Get teams and check how they would appear in template
    user = User.objects.get(username='eyt')
    team_tournament = Tournament.objects.filter(
        is_team_based=True,
        status='registration',
        is_public=True
    ).first()
    
    user_teams = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=team_tournament.game
    ).distinct()
    
    print(f"Template data that would be generated:")
    for team in user_teams:
        print(f"   Team ID: {team.id} (UUID)")
        print(f"   Team Name: {team.name}")
        print(f"   HTML ID: team_{team.id}")
        print(f"   Data attribute: data-team-id=\"{team.id}\"")
        print(f"   Radio value: {team.id}")
        print()

if __name__ == '__main__':
    test_team_selection_data()
    test_javascript_data_format()