#!/usr/bin/env python3
"""
Debug script for team invite players functionality
Tests the user search API and invite workflow
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
from teams.models import Team, TeamMember, TeamInvite
from django.utils import timezone

User = get_user_model()

def debug_invite_players():
    print("=== Team Invite Players Debug ===\n")
    
    # Find a team with a captain
    teams = Team.objects.filter(
        status='active'
    ).select_related('captain').first()
    
    if not teams:
        print("❌ No active teams found!")
        return
    
    test_team = teams
    captain = test_team.captain
    
    print(f"Using team: {test_team.name}")
    print(f"Captain: {captain.get_display_name()}")
    print(f"Team slug: {test_team.slug}")
    print()
    
    # Test 1: Check user search API endpoint
    print("=== Test 1: User Search API ===")
    client = Client()
    client.force_login(captain)
    
    # Test the API endpoint directly
    search_url = reverse('teams:user_search')
    print(f"Search URL: {search_url}")
    
    # Test with a search query
    test_query = "test"
    response = client.get(search_url, {
        'q': test_query,
        'team': test_team.slug
    })
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"✅ API response successful")
            print(f"Users found: {len(data.get('users', []))}")
            
            for user in data.get('users', [])[:3]:
                print(f"  - {user.get('display_name')} ({user.get('email')})")
                
        except Exception as e:
            print(f"❌ Error parsing JSON response: {e}")
            print(f"Response content: {response.content}")
    else:
        print(f"❌ API request failed with status {response.status_code}")
        print(f"Response content: {response.content}")
    
    # Test 2: Check if there are users available to invite
    print("\n=== Test 2: Available Users Check ===")
    
    # Get existing team members
    existing_member_ids = test_team.members.filter(
        status__in=['active', 'pending']
    ).values_list('user_id', flat=True)
    
    # Get users with pending invites
    pending_invite_user_ids = test_team.invites.filter(
        status='pending',
        expires_at__gt=timezone.now()
    ).values_list('invited_user_id', flat=True)
    
    # Find available users
    available_users = User.objects.exclude(
        id=captain.id
    ).exclude(
        id__in=existing_member_ids
    ).exclude(
        id__in=pending_invite_user_ids
    )[:5]
    
    print(f"Total users in system: {User.objects.count()}")
    print(f"Team members (active/pending): {len(existing_member_ids)}")
    print(f"Users with pending invites: {len(pending_invite_user_ids)}")
    print(f"Available users to invite: {available_users.count()}")
    
    if available_users.exists():
        print("Available users:")
        for user in available_users:
            print(f"  - {user.get_display_name()} ({user.email})")
    else:
        print("❌ No users available to invite!")
        print("This could be why the search returns no results.")
    
    # Test 3: Test invite sending
    print("\n=== Test 3: Invite Sending Test ===")
    
    if available_users.exists():
        test_user = available_users.first()
        print(f"Testing invite to: {test_user.get_display_name()}")
        
        # Test the invite send endpoint
        invite_url = reverse('teams:invite_send', kwargs={'slug': test_team.slug})
        print(f"Invite URL: {invite_url}")
        
        response = client.post(invite_url, {
            'user_id': str(test_user.id),
            'message': 'Test invitation message'
        })
        
        print(f"Invite response status: {response.status_code}")
        
        if response.status_code == 302:  # Redirect after successful invite
            print("✅ Invite sent successfully")
            
            # Check if invite was created
            invite = TeamInvite.objects.filter(
                team=test_team,
                invited_user=test_user,
                status='pending'
            ).first()
            
            if invite:
                print(f"✅ Invite record created in database")
                print(f"  Expires: {invite.expires_at}")
                print(f"  Message: {invite.message}")
                
                # Clean up test invite
                invite.delete()
                print("✅ Test invite cleaned up")
            else:
                print("❌ Invite record not found in database")
        else:
            print(f"❌ Invite sending failed")
            print(f"Response content: {response.content}")
    else:
        print("⚠️  Skipping invite test - no available users")
    
    # Test 4: Check JavaScript issues
    print("\n=== Test 4: JavaScript/Frontend Issues ===")
    
    # Check if the roster page loads correctly
    roster_url = reverse('teams:roster', kwargs={'slug': test_team.slug})
    response = client.get(roster_url)
    
    print(f"Roster page status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Check for key elements
        checks = [
            ('userSearch input', 'id="userSearch"'),
            ('searchResults div', 'id="searchResults"'),
            ('inviteForm form', 'id="inviteForm"'),
            ('JavaScript fetch call', '/teams/api/user-search/'),
            ('selectUser function', 'function selectUser'),
        ]
        
        for check_name, check_pattern in checks:
            if check_pattern in content:
                print(f"✅ {check_name} found in HTML")
            else:
                print(f"❌ {check_name} missing from HTML")
    else:
        print(f"❌ Cannot load roster page (status: {response.status_code})")
    
    # Test 5: Check permissions
    print("\n=== Test 5: Permission Check ===")
    
    # Check if user has permission to access roster page
    user_membership = TeamMember.objects.filter(
        team=test_team,
        user=captain,
        status='active'
    ).first()
    
    if user_membership:
        print(f"✅ Captain membership found: {user_membership.role}")
        if user_membership.role in ['captain', 'co_captain']:
            print("✅ Captain has permission to invite players")
        else:
            print("❌ Captain doesn't have permission to invite players")
    else:
        print("❌ Captain membership not found")
    
    # Test 6: Check team status
    print("\n=== Test 6: Team Status Check ===")
    print(f"Team status: {test_team.status}")
    print(f"Team is full: {test_team.is_full}")
    print(f"Current members: {test_team.member_count}/{test_team.max_members}")
    
    if test_team.status != 'active':
        print("❌ Team is not active")
    if test_team.is_full:
        print("❌ Team is full - cannot invite new players")
    
    print("\n=== Debug Summary ===")
    print("Common issues with invite players functionality:")
    print("1. No users available to invite (all users are already members)")
    print("2. Team is full")
    print("3. User doesn't have captain/co-captain permissions")
    print("4. JavaScript errors in browser console")
    print("5. API endpoint not accessible")
    print()
    print("Check browser developer tools for JavaScript errors!")

if __name__ == '__main__':
    debug_invite_players()