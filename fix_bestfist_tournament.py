#!/usr/bin/env python3
"""
Fix BestFist tournament registration issues
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
from core.models import Game
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def fix_bestfist_tournament():
    """Fix BestFist tournament registration issues"""
    print("=== FIXING BESTFIST TOURNAMENT ===\n")
    
    # Get BestFist tournament
    try:
        tournament = Tournament.objects.get(name='BestFist')
        print(f"✅ Found tournament: {tournament.name}")
    except Tournament.DoesNotExist:
        print("❌ BestFist tournament not found")
        return
    
    # Get test user
    try:
        user = User.objects.get(username='eyt')
        print(f"✅ Found user: {user.username}")
    except User.DoesNotExist:
        print("❌ User 'eyt' not found")
        return
    
    # Fix 1: Update tournament registration times to be open now
    now = timezone.now()
    tournament.registration_start = now - timedelta(hours=1)  # Started 1 hour ago
    tournament.registration_end = now + timedelta(hours=2)    # Ends in 2 hours
    tournament.save()
    
    print(f"🔧 Updated tournament registration times:")
    print(f"  - Registration start: {tournament.registration_start}")
    print(f"  - Registration end: {tournament.registration_end}")
    print(f"  - Current time: {now}")
    
    # Fix 2: Create a team for the user for MK1 game
    mk1_game = tournament.game  # Should be MK1
    
    # Check if user already has a team for MK1
    existing_team = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=mk1_game
    ).first()
    
    if existing_team:
        print(f"✅ User already has team for {mk1_game.name}: {existing_team.name}")
    else:
        # Create a new team for MK1
        team = Team.objects.create(
            name=f"Sample Team for {mk1_game.name}",
            slug=f"sample-team-{mk1_game.name.lower()}",
            tag="SMPL",
            description=f"Sample team for {mk1_game.name} tournaments",
            game=mk1_game,
            captain=user,
            status='active',
            is_recruiting=False,
            requires_approval=False,
            max_members=10
        )
        
        # Add user as captain
        TeamMember.objects.create(
            team=team,
            user=user,
            role='captain',
            status='active',
            joined_at=now,
            approved_at=now
        )
        
        # Add one more member to meet team size requirement (2 players)
        try:
            # Try to find another user to add as member
            other_user = User.objects.exclude(id=user.id).first()
            if other_user:
                TeamMember.objects.create(
                    team=team,
                    user=other_user,
                    role='member',
                    status='active',
                    joined_at=now,
                    approved_at=now
                )
                print(f"✅ Added {other_user.username} as team member")
        except Exception as e:
            print(f"⚠️ Could not add second team member: {e}")
        
        print(f"✅ Created team for {mk1_game.name}: {team.name}")
        print(f"  - Team ID: {team.id}")
        print(f"  - Captain: {user.username}")
        print(f"  - Members: {team.members.filter(status='active').count()}")
    
    # Test the fixes
    print(f"\n🧪 Testing fixes:")
    
    # Test can_user_register
    can_register, message = tournament.can_user_register(user)
    print(f"  - can_user_register(): {can_register}")
    print(f"  - Message: {message}")
    
    # Check user's teams
    user_teams = Team.objects.filter(
        members__user=user,
        members__status='active',
        members__role__in=['captain', 'co_captain'],
        status='active',
        game=tournament.game
    ).distinct()
    
    print(f"  - User's eligible teams: {user_teams.count()}")
    for team in user_teams:
        print(f"    - {team.name} ({team.members.filter(status='active').count()} members)")
    
    # Check if registration should work now
    if can_register and user_teams.exists():
        print(f"✅ Registration should work now!")
    else:
        print(f"❌ Registration still has issues:")
        if not can_register:
            print(f"    - Cannot register: {message}")
        if not user_teams.exists():
            print(f"    - No eligible teams")

if __name__ == '__main__':
    fix_bestfist_tournament()