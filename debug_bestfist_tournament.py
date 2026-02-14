#!/usr/bin/env python3
"""
Debug script specifically for BestFist tournament registration issue
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
from django.test import Client, override_settings

User = get_user_model()

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def debug_bestfist_tournament():
    """Debug the BestFist tournament specifically"""
    print("=== BESTFIST TOURNAMENT DEBUG ===\n")
    
    # Get BestFist tournament
    try:
        tournament = Tournament.objects.get(name='BestFist')
        print(f"✅ Found tournament: {tournament.name} (slug: {tournament.slug})")
    except Tournament.DoesNotExist:
        print("❌ BestFist tournament not found")
        return
    
    # Print tournament details
    print(f"\n📋 Tournament Details:")
    print(f"  - Name: {tournament.name}")
    print(f"  - Slug: {tournament.slug}")
    print(f"  - Game: {tournament.game.name}")
    print(f"  - Status: {tournament.status}")
    print(f"  - Is team based: {tournament.is_team_based}")
    print(f"  - Team size: {tournament.team_size}")
    print(f"  - Max participants: {tournament.max_participants}")
    print(f"  - Current registered: {tournament.total_registered}")
    print(f"  - Registration start: {tournament.registration_start}")
    print(f"  - Registration end: {tournament.registration_end}")
    print(f"  - Current time: {timezone.now()}")
    
    # Check if registration is open
    now = timezone.now()
    reg_open = (tournament.status == 'registration' and 
                tournament.registration_start <= now <= tournament.registration_end)
    print(f"  - Registration open: {reg_open}")
    
    # Get test user
    try:
        user = User.objects.get(username='eyt')
        print(f"\n👤 Found user: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        print("❌ User 'eyt' not found")
        return
    
    # Check user's teams for this game
    user_teams = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=tournament.game
    ).distinct()
    
    print(f"\n👥 User's eligible teams for {tournament.game.name}: {user_teams.count()}")
    for team in user_teams:
        print(f"  - {team.name} ({team.members.filter(status='active').count()} members)")
        print(f"    Role: {team.members.filter(user=user, status='active').first().role}")
    
    # Check if user is already registered
    existing_participant = Participant.objects.filter(
        tournament=tournament,
        team__in=user_teams
    ).first()
    
    if existing_participant:
        print(f"\n❌ User is already registered with team: {existing_participant.team.name}")
        print(f"   Participant status: {existing_participant.status}")
        print(f"   Registered at: {existing_participant.registered_at}")
    else:
        print(f"\n✅ User is not registered - should be able to register")
    
    # Test can_user_register method
    can_register, message = tournament.can_user_register(user)
    print(f"\n🧪 can_user_register() test:")
    print(f"  - Result: {can_register}")
    print(f"  - Message: {message}")
    
    # Test with Django test client
    print(f"\n🌐 Testing with Django test client:")
    client = Client()
    client.force_login(user)
    
    # Test tournament detail page
    detail_response = client.get(f'/tournaments/{tournament.slug}/')
    print(f"  - Detail page status: {detail_response.status_code}")
    
    if detail_response.status_code == 200:
        context = detail_response.context
        is_registered = context.get('is_registered', None)
        user_registration_status = context.get('user_registration_status', {})
        
        print(f"  - Context is_registered: {is_registered}")
        print(f"  - Context can_register: {user_registration_status.get('can_register', 'N/A')}")
        print(f"  - Context message: {user_registration_status.get('registration_message', 'N/A')}")
        
        # Check HTML content
        content = detail_response.content.decode('utf-8')
        if 'Register Now' in content:
            print(f"  - ✅ 'Register Now' found in HTML")
        else:
            print(f"  - ❌ 'Register Now' NOT found in HTML")
        
        if "You're Registered" in content:
            print(f"  - ❌ 'You're Registered' found in HTML (PROBLEM!)")
        else:
            print(f"  - ✅ 'You're Registered' NOT found in HTML")
    
    # Test registration page directly
    register_response = client.get(f'/tournaments/{tournament.slug}/register/')
    print(f"  - Register page status: {register_response.status_code}")
    
    if register_response.status_code == 302:
        print(f"  - 🔄 Register page redirects to: {register_response.url}")
        print(f"  - ❌ PROBLEM: Registration page is redirecting!")
    elif register_response.status_code == 200:
        print(f"  - ✅ Register page loads successfully")
    else:
        print(f"  - ❌ Register page error: {register_response.status_code}")
    
    # Test POST to registration
    if user_teams.exists():
        team = user_teams.first()
        print(f"\n📝 Testing POST registration with team: {team.name}")
        
        post_data = {
            'team': str(team.id),
            'rules_agreed': 'on'
        }
        
        post_response = client.post(f'/tournaments/{tournament.slug}/register/', post_data)
        print(f"  - POST response status: {post_response.status_code}")
        
        if post_response.status_code == 302:
            print(f"  - POST redirects to: {post_response.url}")
            
            # Check if participant was created
            new_participant = Participant.objects.filter(
                tournament=tournament,
                team=team
            ).first()
            
            if new_participant:
                print(f"  - ✅ Participant created successfully!")
                print(f"    Status: {new_participant.status}")
                print(f"    Team: {new_participant.team.name}")
            else:
                print(f"  - ❌ No participant created")
        else:
            print(f"  - ❌ POST failed with status: {post_response.status_code}")

if __name__ == '__main__':
    debug_bestfist_tournament()