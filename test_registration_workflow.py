#!/usr/bin/env python
"""
Test tournament registration workflow
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
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from tournaments.models import Tournament, Participant
from tournaments.views import tournament_register

User = get_user_model()

def test_registration_workflow():
    print("🧪 TESTING TOURNAMENT REGISTRATION WORKFLOW")
    print("=" * 55)
    
    # Get a test user
    users = User.objects.filter(is_active=True)
    if not users.exists():
        print("❌ No active users found. Please create a user first.")
        return
    
    user = users.first()
    print(f"👤 Testing with user: {user.username}")
    
    # Get tournaments available for registration
    registerable_tournaments = Tournament.objects.filter(
        status='registration',
        registration_start__lte=timezone.now(),
        registration_end__gte=timezone.now(),
        is_public=True
    )
    
    print(f"🎮 Found {registerable_tournaments.count()} tournaments available for registration")
    
    if not registerable_tournaments.exists():
        print("❌ No tournaments available for registration")
        return
    
    # Test each tournament
    for tournament in registerable_tournaments:
        print(f"\n🎯 Testing tournament: {tournament.name} (slug: {tournament.slug})")
        
        # Test can_user_register method
        can_register, message = tournament.can_user_register(user)
        print(f"   Can register: {can_register}")
        print(f"   Message: {message}")
        
        if not can_register:
            print("   ⚠️  User cannot register for this tournament")
            continue
        
        # Test GET request to registration view
        factory = RequestFactory()
        request = factory.get(f'/tournaments/{tournament.slug}/register/')
        request.user = user
        
        # Add messages framework
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        try:
            response = tournament_register(request, tournament.slug)
            print(f"   GET request status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Registration form loads successfully")
            elif response.status_code == 302:
                print("   🔄 Redirected (likely due to validation issue)")
                # Check messages
                message_list = list(messages)
                if message_list:
                    print(f"   Message: {message_list[0].message}")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error testing GET request: {str(e)}")
        
        # Test POST request (simulate form submission)
        post_data = {
            'rules_agreed': 'on' if tournament.rules else None,
        }
        
        # Remove None values
        post_data = {k: v for k, v in post_data.items() if v is not None}
        
        request = factory.post(f'/tournaments/{tournament.slug}/register/', post_data)
        request.user = user
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        try:
            response = tournament_register(request, tournament.slug)
            print(f"   POST request status: {response.status_code}")
            
            if response.status_code == 302:
                print("   🔄 Redirected after POST (expected)")
                # Check if user was registered
                is_registered = Participant.objects.filter(tournament=tournament, user=user).exists()
                print(f"   User registered: {is_registered}")
                
                # Check messages
                message_list = list(messages)
                if message_list:
                    print(f"   Message: {message_list[0].message}")
                    
                if is_registered:
                    print("   ✅ Registration successful!")
                    # Clean up - remove the test registration
                    Participant.objects.filter(tournament=tournament, user=user).delete()
                    tournament.total_registered = max(0, tournament.total_registered - 1)
                    tournament.save()
                    print("   🧹 Test registration cleaned up")
                else:
                    print("   ⚠️  Registration may have failed or requires payment")
            else:
                print(f"   ❌ Unexpected POST status code: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error testing POST request: {str(e)}")
    
    print(f"\n✅ Registration workflow testing completed!")

if __name__ == '__main__':
    test_registration_workflow()