#!/usr/bin/env python3
"""
Debug script to test the Register Now button functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember
from django.utils import timezone
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from tournaments.views import TournamentDetailView

User = get_user_model()

def debug_register_now_button():
    """Debug the Register Now button functionality"""
    print("=== REGISTER NOW BUTTON DEBUG ===\n")
    
    # Get test user
    try:
        user = User.objects.get(username='eyt')
        print(f"✅ Found user: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        print("❌ User 'eyt' not found")
        return
    
    # Get team-based tournaments
    team_tournaments = Tournament.objects.filter(is_team_based=True, status='registration')
    print(f"\n📋 Found {team_tournaments.count()} team-based tournaments in registration status:")
    
    for tournament in team_tournaments:
        print(f"  - {tournament.name} (slug: {tournament.slug})")
        print(f"    Game: {tournament.game.name}")
        print(f"    Status: {tournament.status}")
        print(f"    Registration: {tournament.registration_start} to {tournament.registration_end}")
        print(f"    Team size: {tournament.team_size}")
        print(f"    Max participants: {tournament.max_participants}")
        print(f"    Current registered: {tournament.total_registered}")
        
        # Check user's teams for this game
        user_teams = Team.objects.filter(
            members__user=user,
            members__status='active',
            members__role__in=['captain', 'co_captain'],
            status='active',
            game=tournament.game
        ).distinct()
        
        print(f"    User's eligible teams: {user_teams.count()}")
        for team in user_teams:
            print(f"      - {team.name} ({team.members.filter(status='active').count()} members)")
        
        # Check if user is already registered
        existing_participant = Participant.objects.filter(
            tournament=tournament,
            team__in=user_teams
        ).first()
        
        if existing_participant:
            print(f"    ❌ Already registered with team: {existing_participant.team.name}")
        else:
            print(f"    ✅ Not registered - should show Register Now button")
        
        # Test tournament detail view context
        print(f"\n🔍 Testing TournamentDetailView context for {tournament.slug}:")
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get(f'/tournaments/{tournament.slug}/')
        request.user = user
        
        # Add session middleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add auth middleware
        auth_middleware = AuthenticationMiddleware(lambda x: None)
        auth_middleware.process_request(request)
        
        # Create view instance
        view = TournamentDetailView()
        view.request = request
        view.object = tournament
        
        # Get context data
        try:
            context = view.get_context_data()
            
            # Check registration status in context
            is_registered = context.get('is_registered', False)
            user_registration_status = context.get('user_registration_status', {})
            can_register = user_registration_status.get('can_register', False)
            
            print(f"    is_registered: {is_registered}")
            print(f"    can_register: {can_register}")
            print(f"    registration_message: {user_registration_status.get('registration_message', 'N/A')}")
            
            # Check what should be shown
            if is_registered:
                print(f"    🔴 Template should show: 'You're Registered' (PROBLEM!)")
            elif can_register:
                print(f"    🟢 Template should show: 'Register Now' button")
            else:
                print(f"    🟡 Template should show: Registration not available")
                
        except Exception as e:
            print(f"    ❌ Error getting context: {e}")
        
        print("-" * 60)
    
    # Test can_user_register method directly
    print(f"\n🧪 Testing can_user_register method directly:")
    for tournament in team_tournaments[:1]:  # Test first tournament
        can_register, message = tournament.can_user_register(user)
        print(f"Tournament: {tournament.name}")
        print(f"can_user_register(): {can_register}")
        print(f"Message: {message}")
        
        # Check if already registered (individual check)
        individual_participant = Participant.objects.filter(tournament=tournament, user=user).exists()
        print(f"Individual participant exists: {individual_participant}")
        
        # Check if team registered
        user_teams = Team.objects.filter(
            members__user=user,
            members__status='active',
            members__role__in=['captain', 'co_captain'],
            status='active',
            game=tournament.game
        ).distinct()
        
        team_participant = Participant.objects.filter(
            tournament=tournament,
            team__in=user_teams
        ).exists()
        print(f"Team participant exists: {team_participant}")

if __name__ == '__main__':
    debug_register_now_button()