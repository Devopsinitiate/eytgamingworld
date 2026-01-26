#!/usr/bin/env python
"""
Debug script to test tournament registration page rendering
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client, override_settings
from django.contrib.auth import get_user_model
from tournaments.models import Tournament

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_registration_page():
    """Test the tournament registration page"""
    client = Client()
    
    # Get a tournament
    tournament = Tournament.objects.first()
    if not tournament:
        print("No tournaments found in database")
        return
    
    print(f"Testing tournament: {tournament.name} (slug: {tournament.slug})")
    
    # Create a test user
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Login the user
    client.force_login(user)
    
    # Test GET request to registration page
    url = f'/tournaments/{tournament.slug}/register/'
    print(f"Testing URL: {url}")
    
    try:
        response = client.get(url)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Registration page loads successfully")
            
            # Check context variables
            context = response.context
            print(f"Tournament in context: {context.get('tournament')}")
            print(f"User teams in context: {context.get('user_teams')}")
            
            # Check if template renders properly
            content = response.content.decode('utf-8')
            if 'Tournament Registration' in content:
                print("✅ Page title found")
            else:
                print("❌ Page title not found")
                
            if 'step-indicator' in content:
                print("✅ Step indicator found")
            else:
                print("❌ Step indicator not found")
                
            if 'nextStep' in content:
                print("✅ JavaScript functions found")
            else:
                print("❌ JavaScript functions not found")
                
        else:
            print(f"❌ Registration page failed to load: {response.status_code}")
            if hasattr(response, 'content'):
                print(f"Response content: {response.content.decode('utf-8')[:500]}")
                
    except Exception as e:
        print(f"❌ Error testing registration page: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_registration_page()