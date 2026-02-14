#!/usr/bin/env python
"""
Test the registration status fix for team-based tournaments
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

def test_registration_status_fix():
    print("🧪 TESTING REGISTRATION STATUS FIX")
    print("=" * 50)
    
    # Get test user
    try:
        user = User.objects.get(username='eyt')
        print(f"✅ Using test user: {user.username}")
    except User.DoesNotExist:
        print("❌ Test user 'eyt' not found")
        return
    
    # Get team-based tournament
    team_tournament = Tournament.objects.filter(
        is_team_based=True,
        status='registration',
        is_public=True
    ).first()
    
    if not team_tournament:
        print("❌ No team-based tournaments available")
        return
    
    print(f"🏆 Testing tournament: {team_tournament.name} (slug: {team_tournament.slug})")
    
    # Get user's eligible team
    user_teams = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=team_tournament.game
    ).distinct()
    
    if not user_teams.exists():
        print("❌ No eligible teams found")
        return
    
    test_team = user_teams.first()
    print(f"👥 Using team: {test_team.name}")
    
    # Test 1: Before registration
    print(f"\n📝 TEST 1: BEFORE TEAM REGISTRATION")
    
    # Check if team is registered
    team_participant = Participant.objects.filter(
        tournament=team_tournament,
        team=test_team
    ).first()
    
    print(f"   Team participant exists: {team_participant is not None}")
    
    # Test the view context logic
    from tournaments.views import TournamentContextMixin
    
    class TestRequest:
        def __init__(self, user):
            self.user = user
            self.META = {}
    
    class TestMixin(TournamentContextMixin):
        def __init__(self, user):
            self.request = TestRequest(user)
    
    mixin = TestMixin(user)
    context = mixin.get_user_registration_status(team_tournament)
    
    print(f"   Context is_registered: {context['is_registered']}")
    print(f"   Context can_register: {context['can_register']}")
    print(f"   Context participant: {context['participant']}")
    
    # Test 2: After registration
    print(f"\n📝 TEST 2: AFTER TEAM REGISTRATION")
    
    # Create a team registration
    if not team_participant:
        team_participant = Participant.objects.create(
            tournament=team_tournament,
            team=test_team,
            status='confirmed'
        )
        print(f"   ✅ Created team registration")
    else:
        print(f"   ✅ Team registration already exists")
    
    # Test the view context logic again
    context = mixin.get_user_registration_status(team_tournament)
    
    print(f"   Context is_registered: {context['is_registered']}")
    print(f"   Context can_register: {context['can_register']}")
    print(f"   Context participant: {context['participant']}")
    print(f"   Context team: {context['team']}")
    
    # Test 3: Legacy context logic (from TournamentDetailView)
    print(f"\n📝 TEST 3: LEGACY CONTEXT LOGIC")
    
    # Simulate the legacy context logic
    if team_tournament.is_team_based:
        user_teams_for_legacy = Team.objects.filter(
            members__user=user,
            members__status='active',
            members__role__in=['captain', 'co_captain'],
            status='active',
            game=team_tournament.game
        ).distinct()
        
        is_registered_legacy = Participant.objects.filter(
            tournament=team_tournament,
            team__in=user_teams_for_legacy
        ).exists()
        
        user_participant_legacy = Participant.objects.filter(
            tournament=team_tournament,
            team__in=user_teams_for_legacy
        ).select_related('team').first()
    else:
        is_registered_legacy = Participant.objects.filter(
            tournament=team_tournament,
            user=user
        ).exists()
        
        user_participant_legacy = Participant.objects.filter(
            tournament=team_tournament,
            user=user
        ).select_related('team').first()
    
    print(f"   Legacy is_registered: {is_registered_legacy}")
    print(f"   Legacy user_participant: {user_participant_legacy}")
    
    # Expected results
    print(f"\n✅ EXPECTED RESULTS:")
    print(f"   Before registration: is_registered=False, can_register=True")
    print(f"   After registration: is_registered=True, can_register=False")
    
    # Clean up - remove test registration
    if team_participant:
        team_participant.delete()
        print(f"\n🧹 Cleaned up test registration")

if __name__ == '__main__':
    test_registration_status_fix()