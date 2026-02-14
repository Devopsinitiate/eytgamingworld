#!/usr/bin/env python3
"""
Test the Register Now button with real Django test client
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember
from django.urls import reverse

User = get_user_model()

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_register_now_button():
    """Test the Register Now button with authenticated user"""
    print("=== REGISTER NOW BUTTON REAL TEST ===\n")
    
    # Create test client
    client = Client()
    
    # Get test user
    try:
        user = User.objects.get(username='eyt')
        print(f"✅ Found user: {user.username}")
    except User.DoesNotExist:
        print("❌ User 'eyt' not found")
        return
    
    # Login the user
    login_success = client.force_login(user)
    print(f"✅ User logged in successfully")
    
    # Get a team-based tournament
    tournament = Tournament.objects.filter(
        is_team_based=True, 
        status='registration'
    ).first()
    
    if not tournament:
        print("❌ No team-based tournaments in registration status")
        return
    
    print(f"🎯 Testing tournament: {tournament.name} (slug: {tournament.slug})")
    
    # Check user's teams
    user_teams = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=tournament.game
    ).distinct()
    
    print(f"👥 User has {user_teams.count()} eligible teams")
    
    # Test tournament detail page
    detail_url = reverse('tournaments:detail', kwargs={'slug': tournament.slug})
    print(f"🔗 Testing URL: {detail_url}")
    
    response = client.get(detail_url)
    print(f"📄 Response status: {response.status_code}")
    
    if response.status_code == 200:
        # Check context
        context = response.context
        is_registered = context.get('is_registered', None)
        user_registration_status = context.get('user_registration_status', {})
        
        print(f"📊 Context data:")
        print(f"  - is_registered: {is_registered}")
        print(f"  - user_registration_status: {user_registration_status}")
        
        # Check if Register Now button should be shown
        if is_registered:
            print(f"🔴 PROBLEM: is_registered=True, Register Now button will NOT show")
        else:
            print(f"🟢 GOOD: is_registered=False, Register Now button SHOULD show")
        
        # Check the actual HTML content
        content = response.content.decode('utf-8')
        
        if 'Register Now' in content:
            print(f"✅ 'Register Now' text found in HTML")
        else:
            print(f"❌ 'Register Now' text NOT found in HTML")
        
        if "You're Registered" in content:
            print(f"❌ PROBLEM: 'You're Registered' text found in HTML")
        else:
            print(f"✅ GOOD: 'You're Registered' text NOT found in HTML")
        
        # Test register URL
        register_url = reverse('tournaments:register', kwargs={'slug': tournament.slug})
        print(f"\n🔗 Testing register URL: {register_url}")
        
        register_response = client.get(register_url)
        print(f"📄 Register page status: {register_response.status_code}")
        
        if register_response.status_code == 200:
            print(f"✅ Register page loads successfully")
        elif register_response.status_code == 302:
            print(f"🔄 Register page redirects to: {register_response.url}")
        else:
            print(f"❌ Register page error: {register_response.status_code}")
    
    else:
        print(f"❌ Failed to load tournament detail page")

if __name__ == '__main__':
    test_register_now_button()