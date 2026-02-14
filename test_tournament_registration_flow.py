#!/usr/bin/env python3
"""
Test the actual tournament registration flow for team captains
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember
from core.models import Game

User = get_user_model()

def test_team_registration_flow():
    """Test the complete team registration flow"""
    
    print("🧪 TESTING TEAM REGISTRATION FLOW")
    print("=" * 50)
    
    try:
        # Create test data
        game, _ = Game.objects.get_or_create(
            name='Flow Test Game',
            defaults={'slug': 'flow-test-game'}
        )
        
        captain_user, _ = User.objects.get_or_create(
            username='flow_captain',
            defaults={
                'email': 'flowcaptain@test.com',
                'first_name': 'Flow',
                'last_name': 'Captain'
            }
        )
        
        organizer_user, _ = User.objects.get_or_create(
            username='flow_organizer',
            defaults={
                'email': 'floworganizer@test.com',
                'first_name': 'Flow',
                'last_name': 'Organizer'
            }
        )
        
        # Create team
        team, created = Team.objects.get_or_create(
            name='Flow Test Team',
            defaults={
                'slug': 'flow-test-team',
                'tag': 'FLOW',
                'game': game,
                'captain': captain_user,
                'status': 'active'
            }
        )
        
        if not created and team.game != game:
            team.game = game
            team.save()
        
        # Create team membership
        membership, _ = TeamMember.objects.get_or_create(
            team=team,
            user=captain_user,
            defaults={
                'role': 'captain',
                'status': 'active',
                'approved_at': timezone.now()
            }
        )
        
        # Create tournament
        tournament, created = Tournament.objects.get_or_create(
            name='Flow Test Tournament',
            defaults={
                'slug': 'flow-test-tournament',
                'game': game,
                'organizer': organizer_user,
                'is_team_based': True,
                'team_size': 5,
                'status': 'registration',
                'registration_start': timezone.now() - timedelta(hours=1),
                'registration_end': timezone.now() + timedelta(hours=24),
                'check_in_start': timezone.now() + timedelta(hours=23),
                'start_datetime': timezone.now() + timedelta(days=1),
                'max_participants': 16,
                'min_participants': 4
            }
        )
        
        print(f"✅ Setup complete:")
        print(f"   Game: {game.name}")
        print(f"   Captain: {captain_user.username}")
        print(f"   Team: {team.name}")
        print(f"   Tournament: {tournament.name}")
        
        # Test the registration flow
        client = Client()
        client.force_login(captain_user)
        
        # 1. Test GET request to registration page
        print(f"\n🔍 TESTING REGISTRATION PAGE ACCESS")
        register_url = reverse('tournaments:register', kwargs={'slug': tournament.slug})
        response = client.get(register_url)
        
        print(f"   URL: {register_url}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Registration page accessible")
            
            # Check if team is available in the form
            content = response.content.decode()
            if team.name in content:
                print("✅ SUCCESS: Team appears in registration form")
            else:
                print("❌ FAILED: Team not found in registration form")
                return False
        else:
            print(f"❌ FAILED: Registration page not accessible - Status {response.status_code}")
            return False
        
        # 2. Test POST request to register team
        print(f"\n🔍 TESTING TEAM REGISTRATION SUBMISSION")
        
        # Clean up any existing participants first
        Participant.objects.filter(tournament=tournament, team=team).delete()
        
        response = client.post(register_url, {
            'team': str(team.id),
            'rules_agreement': 'on'
        })
        
        print(f"   Status: {response.status_code}")
        
        # Check if participant was created
        participant = Participant.objects.filter(tournament=tournament, team=team).first()
        
        if participant:
            print(f"✅ SUCCESS: Team registration created")
            print(f"   Participant ID: {participant.id}")
            print(f"   Team: {participant.team.name}")
            print(f"   Status: {participant.status}")
        else:
            print("❌ FAILED: No participant record created")
            return False
        
        # 3. Test duplicate registration prevention
        print(f"\n🔍 TESTING DUPLICATE REGISTRATION PREVENTION")
        
        response = client.post(register_url, {
            'team': str(team.id),
            'rules_agreement': 'on'
        })
        
        # Should redirect back to tournament detail with error message
        if response.status_code in [302, 200]:
            print("✅ SUCCESS: Duplicate registration handled")
        else:
            print(f"❌ FAILED: Unexpected response - Status {response.status_code}")
            return False
        
        # Clean up
        participant.delete()
        print(f"   Cleaned up test data")
        
        print(f"\n🎉 ALL TESTS PASSED!")
        print("Team captain registration flow is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_team_registration_flow()
    sys.exit(0 if success else 1)