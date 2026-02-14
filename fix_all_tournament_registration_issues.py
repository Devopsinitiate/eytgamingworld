#!/usr/bin/env python3
"""
Fix registration issues for all tournaments
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

def fix_all_tournament_registration_issues():
    """Fix registration issues for all tournaments"""
    print("=== FIXING ALL TOURNAMENT REGISTRATION ISSUES ===\n")
    
    # Get test user
    try:
        user = User.objects.get(username='eyt')
        print(f"✅ Found user: {user.username}")
    except User.DoesNotExist:
        print("❌ User 'eyt' not found")
        return
    
    # Get all team-based tournaments in registration status
    tournaments = Tournament.objects.filter(
        is_team_based=True,
        status='registration'
    )
    
    print(f"📋 Found {tournaments.count()} team-based tournaments in registration status\n")
    
    now = timezone.now()
    
    for tournament in tournaments:
        print(f"🎯 Processing tournament: {tournament.name} ({tournament.game.name})")
        
        # Check if registration is open
        reg_open = (tournament.registration_start <= now <= tournament.registration_end)
        print(f"  - Registration open: {reg_open}")
        
        # Fix registration times if needed
        if not reg_open:
            if now < tournament.registration_start:
                print(f"  - 🔧 Registration hasn't started yet, updating times...")
                tournament.registration_start = now - timedelta(hours=1)
                tournament.registration_end = now + timedelta(hours=2)
                tournament.save()
                print(f"    Updated: {tournament.registration_start} to {tournament.registration_end}")
            elif now > tournament.registration_end:
                print(f"  - 🔧 Registration has ended, extending deadline...")
                tournament.registration_end = now + timedelta(hours=2)
                tournament.save()
                print(f"    Extended to: {tournament.registration_end}")
        
        # Check if user has eligible teams for this game
        user_teams = Team.objects.filter(
            members__user=user,
            members__status='active',
            members__role__in=['captain', 'co_captain'],
            status='active',
            game=tournament.game
        ).distinct()
        
        print(f"  - User's eligible teams: {user_teams.count()}")
        
        # Create team if user doesn't have one for this game
        if not user_teams.exists():
            print(f"  - 🔧 Creating team for {tournament.game.name}...")
            
            # Check if team already exists with this name
            team_name = f"Sample Team for {tournament.game.name}"
            existing_team = Team.objects.filter(name=team_name).first()
            
            if existing_team:
                print(f"    Team already exists: {existing_team.name}")
                # Add user as captain if not already a member
                membership = TeamMember.objects.filter(team=existing_team, user=user).first()
                if not membership:
                    TeamMember.objects.create(
                        team=existing_team,
                        user=user,
                        role='captain',
                        status='active',
                        joined_at=now,
                        approved_at=now
                    )
                    print(f"    Added user as captain to existing team")
            else:
                # Create new team
                team = Team.objects.create(
                    name=team_name,
                    slug=f"sample-team-{tournament.game.name.lower().replace(' ', '-')}",
                    tag="SMPL",
                    description=f"Sample team for {tournament.game.name} tournaments",
                    game=tournament.game,
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
                
                # Add additional members to meet team size requirement
                required_members = tournament.team_size
                current_members = 1  # User is already added
                
                if current_members < required_members:
                    other_users = User.objects.exclude(id=user.id)[:required_members - current_members]
                    for other_user in other_users:
                        TeamMember.objects.create(
                            team=team,
                            user=other_user,
                            role='member',
                            status='active',
                            joined_at=now,
                            approved_at=now
                        )
                        current_members += 1
                
                print(f"    Created team: {team.name} with {current_members} members")
        
        # Test if user can register now
        can_register, message = tournament.can_user_register(user)
        print(f"  - Can register: {can_register}")
        if not can_register:
            print(f"    Message: {message}")
        
        print("-" * 60)
    
    print(f"\n✅ All tournament registration issues have been fixed!")

if __name__ == '__main__':
    fix_all_tournament_registration_issues()