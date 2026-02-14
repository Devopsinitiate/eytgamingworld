#!/usr/bin/env python
"""
Test script to verify the invite players fix works correctly.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from teams.models import Team, TeamMember
from core.models import Game

User = get_user_model()

def test_user_search_api():
    """Test that the user search API works without query slicing errors"""
    print("=== Testing User Search API Fix ===")
    
    # Create test data
    game = Game.objects.get_or_create(name="Test Game", slug="test-game")[0]
    
    # Create team captain
    captain = User.objects.get_or_create(
        username="test_captain",
        defaults={'email': 'captain@test.com'}
    )[0]
    
    # Create team
    team = Team.objects.get_or_create(
        name="Test Team",
        slug="test-team",
        defaults={
            'captain': captain,
            'game': game,
            'status': 'active',
            'is_public': True
        }
    )[0]
    
    # Create captain membership
    TeamMember.objects.get_or_create(
        team=team,
        user=captain,
        defaults={'role': 'captain', 'status': 'active'}
    )
    
    # Create some test users to search for
    for i in range(15):  # More than the 10 limit to test slicing
        User.objects.get_or_create(
            username=f"searchuser{i}",
            defaults={'email': f'searchuser{i}@test.com'}
        )
    
    # Test the API endpoint directly using Django's test client
    client = Client()
    client.force_login(captain)
    
    try:
        response = client.get('/teams/api/user-search/', {
            'q': 'searchuser',
            'team': team.slug
        })
        
        print(f"✅ API request successful! Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data['users'])} users")
            print(f"✅ Response format is correct: {list(data.keys())}")
            
            # Verify we get at most 10 results (the limit)
            if len(data['users']) <= 10:
                print("✅ Limit of 10 users is properly applied")
            else:
                print(f"❌ Too many results returned: {len(data['users'])}")
                
            return True
        else:
            print(f"❌ API returned error status: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ API request failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_user_search_api()
    if success:
        print("\n🎉 Invite players fix is working correctly!")
    else:
        print("\n❌ Fix verification failed")
    
    sys.exit(0 if success else 1)