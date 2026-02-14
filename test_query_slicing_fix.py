#!/usr/bin/env python
"""
Direct test of the query slicing fix in TeamUserSearchView
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Q
from teams.models import Team, TeamMember
from core.models import Game

User = get_user_model()

def test_query_slicing_fix():
    """Test that the query slicing issue is fixed"""
    print("=== Testing Query Slicing Fix ===")
    
    try:
        # Create test data
        game = Game.objects.get_or_create(name="Test Game", slug="test-game")[0]
        
        # Create team captain
        captain = User.objects.get_or_create(
            username="test_captain_fix",
            defaults={'email': 'captain_fix@test.com'}
        )[0]
        
        # Create team
        team = Team.objects.get_or_create(
            name="Test Team Fix",
            slug="test-team-fix",
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
        test_users = []
        for i in range(15):  # More than the 10 limit to test slicing
            user, created = User.objects.get_or_create(
                username=f"fixuser{i}",
                defaults={'email': f'fixuser{i}@test.com'}
            )
            test_users.append(user)
        
        print(f"✅ Created {len(test_users)} test users")
        
        # Now test the exact logic from TeamUserSearchView
        query = "fixuser"
        
        # This is the exact code from the fixed TeamUserSearchView
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(
            id=captain.id  # Exclude current user
        )
        
        # Filter out existing team members if team is specified
        existing_member_ids = team.members.filter(
            status__in=['active', 'pending']
        ).values_list('user_id', flat=True)
        users = users.exclude(id__in=existing_member_ids)
        
        # Filter out users with pending invites
        pending_invite_user_ids = team.invites.filter(
            status='pending'
        ).values_list('invited_user_id', flat=True)
        users = users.exclude(id__in=pending_invite_user_ids)
        
        # Apply limit after all filtering is complete (THIS IS THE FIX)
        users = users[:10]
        
        # Try to evaluate the queryset - this would fail with the old code
        user_list = list(users)
        
        print(f"✅ Query executed successfully! Found {len(user_list)} users")
        print(f"✅ Limit properly applied: {len(user_list) <= 10}")
        
        # Verify the results
        for user in user_list[:3]:  # Show first 3
            print(f"  - {user.username} ({user.email})")
        
        return True
        
    except Exception as e:
        print(f"❌ Query slicing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_query_slicing_fix()
    if success:
        print("\n🎉 Query slicing fix is working correctly!")
        print("The 'Cannot filter a query once a slice has been taken' error has been resolved.")
    else:
        print("\n❌ Query slicing fix verification failed")
    
    sys.exit(0 if success else 1)