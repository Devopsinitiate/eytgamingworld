#!/usr/bin/env python3
"""
Simple test to verify invite players functionality works
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from teams.models import Team, TeamMember, TeamInvite
from teams.views import TeamUserSearchView
from django.http import HttpRequest
from django.utils import timezone

User = get_user_model()

def test_invite_functionality():
    print("=== Invite Players Functionality Test ===\n")
    
    # Find a team with a captain
    team = Team.objects.filter(status='active').select_related('captain').first()
    if not team:
        print("❌ No active teams found!")
        return
    
    captain = team.captain
    print(f"Testing with team: {team.name}")
    print(f"Captain: {captain.get_display_name()}")
    print()
    
    # Test 1: Check if there are users available to invite
    print("=== Test 1: Available Users ===")
    
    # Get existing team members
    existing_member_ids = list(team.members.filter(
        status__in=['active', 'pending']
    ).values_list('user_id', flat=True))
    
    # Get users with pending invites
    pending_invite_user_ids = list(team.invites.filter(
        status='pending',
        expires_at__gt=timezone.now()
    ).values_list('invited_user_id', flat=True))
    
    # Find available users
    available_users = User.objects.exclude(
        id=captain.id
    ).exclude(
        id__in=existing_member_ids
    ).exclude(
        id__in=pending_invite_user_ids
    )
    
    print(f"Total users: {User.objects.count()}")
    print(f"Team members: {len(existing_member_ids)}")
    print(f"Pending invites: {len(pending_invite_user_ids)}")
    print(f"Available to invite: {available_users.count()}")
    
    if available_users.count() == 0:
        print("❌ No users available to invite!")
        print("This is likely why the search returns no results.")
        return
    else:
        print("✅ Users are available to invite")
        for user in available_users[:3]:
            print(f"  - {user.get_display_name()} ({user.email})")
    
    # Test 2: Test the search view logic directly
    print("\n=== Test 2: Search View Logic ===")
    
    # Create a mock request
    request = HttpRequest()
    request.method = 'GET'
    request.GET = {
        'q': 'test',
        'team': team.slug
    }
    request.user = captain
    
    # Test the view
    view = TeamUserSearchView()
    try:
        response = view.get(request)
        if hasattr(response, 'content'):
            import json
            data = json.loads(response.content)
            print(f"✅ Search view returned {len(data.get('users', []))} users")
            
            for user in data.get('users', [])[:3]:
                print(f"  - {user.get('display_name')} ({user.get('email')})")
        else:
            print(f"❌ Search view returned unexpected response: {response}")
    except Exception as e:
        print(f"❌ Search view error: {e}")
    
    # Test 3: Test invite creation
    print("\n=== Test 3: Invite Creation ===")
    
    if available_users.exists():
        test_user = available_users.first()
        print(f"Creating test invite for: {test_user.get_display_name()}")
        
        try:
            # Create invite
            invite = TeamInvite.objects.create(
                team=team,
                invited_by=captain,
                invited_user=test_user,
                message='Test invitation',
                expires_at=timezone.now() + timezone.timedelta(days=7)
            )
            print("✅ Invite created successfully")
            print(f"  ID: {invite.id}")
            print(f"  Expires: {invite.expires_at}")
            
            # Clean up
            invite.delete()
            print("✅ Test invite cleaned up")
            
        except Exception as e:
            print(f"❌ Invite creation failed: {e}")
    
    # Test 4: Check JavaScript issues
    print("\n=== Test 4: Common JavaScript Issues ===")
    print("Common reasons why invite players might not work:")
    print()
    print("1. JavaScript errors in browser console")
    print("   - Check browser developer tools for errors")
    print("   - Look for fetch() API errors")
    print("   - Check for CSRF token issues")
    print()
    print("2. User search returns no results")
    print("   - All users are already team members")
    print("   - Search query too specific")
    print("   - Team is full")
    print()
    print("3. Network/API issues")
    print("   - API endpoint not accessible")
    print("   - CORS issues")
    print("   - Server errors")
    print()
    print("4. UI/UX issues")
    print("   - Search input not working")
    print("   - Results not displaying")
    print("   - Form not submitting")
    print()
    
    # Test 5: Check team status
    print("=== Test 5: Team Status ===")
    print(f"Team full: {team.is_full}")
    print(f"Current members: {team.member_count}/{team.max_members}")
    print(f"Team status: {team.status}")
    
    if team.is_full:
        print("❌ Team is full - cannot invite new players")
    elif team.status != 'active':
        print("❌ Team is not active")
    else:
        print("✅ Team can accept new invites")
    
    print("\n=== Recommendations ===")
    print("1. Check browser console for JavaScript errors")
    print("2. Verify user has captain/co-captain permissions")
    print("3. Ensure team is not full")
    print("4. Try searching for specific usernames")
    print("5. Check network tab in browser dev tools")

if __name__ == '__main__':
    test_invite_functionality()