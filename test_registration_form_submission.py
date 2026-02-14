#!/usr/bin/env python
"""
Test tournament registration form submission
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember

User = get_user_model()

def test_registration_form_submission():
    print("🧪 TESTING TOURNAMENT REGISTRATION FORM SUBMISSION")
    print("=" * 60)
    
    # Create a test client
    client = Client()
    
    # Get a test user
    try:
        user = User.objects.get(username='eyt')
        print(f"✅ Using test user: {user.username}")
    except User.DoesNotExist:
        print("❌ Test user 'eyt' not found")
        return
    
    # Login the user
    client.force_login(user)
    print(f"✅ User logged in")
    
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
    
    # Get user's eligible team
    eligible_team = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=team_tournament.game
    ).distinct().first()
    
    if not eligible_team:
        print("❌ No eligible teams found for user")
        return
    
    print(f"👥 Using team: {eligible_team.name}")
    
    # Test GET request to registration form
    print(f"\n📝 Testing GET request to registration form...")
    register_url = reverse('tournaments:register', kwargs={'slug': team_tournament.slug})
    print(f"   URL: {register_url}")
    
    try:
        response = client.get(register_url)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Registration form loads successfully")
            
            # Check if team is in the form
            if eligible_team.name in response.content.decode():
                print(f"✅ Team '{eligible_team.name}' appears in form")
            else:
                print(f"⚠️  Team '{eligible_team.name}' not found in form")
                
        elif response.status_code == 302:
            print(f"⚠️  Redirected to: {response.url}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error loading registration form: {str(e)}")
        return
    
    # Test POST request to submit registration
    print(f"\n🚀 Testing POST request to submit registration...")
    
    post_data = {
        'team': str(eligible_team.id),
        'rules_agreed': 'on'  # Checkbox value
    }
    
    # Check if tournament has rules
    if team_tournament.rules:
        print(f"   Tournament has rules - including agreement")
    else:
        print(f"   Tournament has no rules - skipping agreement")
        del post_data['rules_agreed']
    
    print(f"   POST data: {post_data}")
    
    try:
        response = client.post(register_url, post_data)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 302:
            print(f"✅ Registration submitted - redirected to: {response.url}")
            
            # Check if participant was created
            participant = Participant.objects.filter(
                tournament=team_tournament,
                team=eligible_team
            ).first()
            
            if participant:
                print(f"✅ Participant created successfully")
                print(f"   Participant ID: {participant.id}")
                print(f"   Status: {participant.status}")
                
                # Clean up
                print(f"🧹 Cleaning up test registration...")
                if participant.status == 'confirmed':
                    team_tournament.total_registered -= 1
                    team_tournament.save()
                participant.delete()
                print(f"✅ Test registration cleaned up")
                
            else:
                print(f"❌ No participant created")
                
        elif response.status_code == 200:
            print(f"⚠️  Form returned with errors")
            # Check for form errors in response
            content = response.content.decode()
            if 'error' in content.lower():
                print(f"   Form contains errors")
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error submitting registration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_registration_form_submission()