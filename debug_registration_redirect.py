#!/usr/bin/env python
"""
Debug the registration redirect issue for team-based tournaments
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
from django.test import Client
from django.urls import reverse
from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember

User = get_user_model()

def debug_registration_flow():
    print("🔍 DEBUGGING REGISTRATION REDIRECT ISSUE")
    print("=" * 60)
    
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
    
    # Test can_user_register method
    print(f"\n🔍 TESTING can_user_register METHOD")
    can_register, message = team_tournament.can_user_register(user)
    print(f"   Result: {can_register}")
    print(f"   Message: {message}")
    
    # Check if user is already registered (individual check)
    individual_participant = Participant.objects.filter(
        tournament=team_tournament,
        user=user
    ).first()
    
    print(f"   Individual participant exists: {individual_participant is not None}")
    
    # Check if user's teams are already registered
    user_teams = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=team_tournament.game
    ).distinct()
    
    print(f"   User has {user_teams.count()} eligible teams")
    
    for team in user_teams:
        team_participant = Participant.objects.filter(
            tournament=team_tournament,
            team=team
        ).first()
        print(f"   Team '{team.name}' registered: {team_participant is not None}")
        if team_participant:
            print(f"     Status: {team_participant.status}")
    
    # Test the registration URL directly
    print(f"\n🌐 TESTING REGISTRATION URL ACCESS")
    client = Client()
    client.force_login(user)
    
    register_url = reverse('tournaments:register', kwargs={'slug': team_tournament.slug})
    print(f"   Registration URL: {register_url}")
    
    try:
        response = client.get(register_url)
        print(f"   GET Response Status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"   Redirected to: {response.url}")
            print(f"   ❌ User is being redirected instead of seeing registration form")
        elif response.status_code == 200:
            print(f"   ✅ Registration form loaded successfully")
            
            # Check if teams are in the response
            content = response.content.decode()
            if 'Select Your Team' in content:
                print(f"   ✅ Team selection section found in form")
            else:
                print(f"   ❌ Team selection section not found in form")
                
            # Check for specific team
            if user_teams.exists():
                team_name = user_teams.first().name
                if team_name in content:
                    print(f"   ✅ Team '{team_name}' found in form")
                else:
                    print(f"   ❌ Team '{team_name}' not found in form")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error accessing registration URL: {str(e)}")
    
    # Test tournament detail page Register Now button logic
    print(f"\n🔘 TESTING REGISTER NOW BUTTON LOGIC")
    
    detail_url = reverse('tournaments:detail', kwargs={'slug': team_tournament.slug})
    print(f"   Tournament detail URL: {detail_url}")
    
    try:
        response = client.get(detail_url)
        print(f"   Detail page status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode()
            
            # Check for Register Now button
            if 'Register Now' in content:
                print(f"   ✅ Register Now button found on detail page")
                
                # Check the href attribute
                if f'/tournaments/{team_tournament.slug}/register/' in content:
                    print(f"   ✅ Register Now button has correct URL")
                else:
                    print(f"   ❌ Register Now button URL might be incorrect")
            else:
                print(f"   ❌ Register Now button not found on detail page")
                
                # Check why button is not showing
                if 'Tournament Full' in content:
                    print(f"   Reason: Tournament is full")
                elif 'Registration has ended' in content:
                    print(f"   Reason: Registration has ended")
                elif 'Coming Soon' in content:
                    print(f"   Reason: Tournament is in draft")
                else:
                    print(f"   Reason: Unknown")
                    
    except Exception as e:
        print(f"   ❌ Error accessing detail page: {str(e)}")
    
    # Check tournament statistics that might affect button display
    print(f"\n📊 CHECKING TOURNAMENT STATISTICS")
    print(f"   Total registered: {team_tournament.total_registered}")
    print(f"   Max participants: {team_tournament.max_participants}")
    print(f"   Spots remaining: {team_tournament.spots_remaining}")
    print(f"   Is full: {team_tournament.is_full}")
    print(f"   Registration open: {team_tournament.is_registration_open}")
    
    # Check template context variables
    print(f"\n📝 CHECKING TEMPLATE CONTEXT")
    
    # Simulate the context that would be passed to the template
    from tournaments.views import TournamentContextMixin
    
    class TestRequest:
        def __init__(self, user):
            self.user = user
    
    class TestMixin(TournamentContextMixin):
        def __init__(self, user):
            self.request = TestRequest(user)
    
    mixin = TestMixin(user)
    context = mixin.get_tournament_context(team_tournament)
    
    print(f"   Tournament stats participants registered: {context['tournament_stats']['participants']['registered']}")
    print(f"   Tournament stats spots remaining: {context['tournament_stats']['participants']['spots_remaining']}")
    print(f"   User registration status can_register: {context['user_registration_status']['can_register']}")
    print(f"   User registration status message: {context['user_registration_status']['registration_message']}")

if __name__ == '__main__':
    debug_registration_flow()