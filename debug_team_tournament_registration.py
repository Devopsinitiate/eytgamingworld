#!/usr/bin/env python
"""
Debug team-based tournament registration issues
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
from tournaments.models import Tournament, Participant

User = get_user_model()

def debug_team_tournament_registration():
    print("🔍 DEBUGGING TEAM-BASED TOURNAMENT REGISTRATION")
    print("=" * 60)
    
    # Get team-based tournaments
    team_tournaments = Tournament.objects.filter(
        is_team_based=True,
        is_public=True
    ).order_by('-created_at')
    
    print(f"🏆 Found {team_tournaments.count()} team-based tournaments")
    
    if not team_tournaments.exists():
        print("❌ No team-based tournaments found")
        return
    
    # Get a test user
    users = User.objects.filter(is_active=True)
    if not users.exists():
        print("❌ No active users found")
        return
    
    user = users.first()
    print(f"👤 Testing with user: {user.username}")
    print()
    
    # Check each team tournament
    for tournament in team_tournaments[:3]:
        print(f"🎮 Tournament: {tournament.name}")
        print(f"   Slug: {tournament.slug}")
        print(f"   Status: {tournament.status}")
        print(f"   Is Team Based: {tournament.is_team_based}")
        print(f"   Team Size: {tournament.team_size}")
        print(f"   Game: {tournament.game.name if tournament.game else 'No game'}")
        print(f"   Registration Start: {tournament.registration_start}")
        print(f"   Registration End: {tournament.registration_end}")
        
        # Test basic registration check
        can_register, message = tournament.can_user_register(user)
        print(f"   Can Register (basic): {can_register}")
        print(f"   Message: {message}")
        
        if not can_register:
            print("   ❌ Basic registration check failed")
            continue
        
        # Check if teams app exists and user has teams
        try:
            from teams.models import Team, TeamMember
            print("   ✅ Teams app is available")
            
            # Check user's teams
            user_teams = Team.objects.filter(
                members__user=user,
                members__status='active',
                status='active'
            ).distinct()
            
            print(f"   User's total teams: {user_teams.count()}")
            
            # Check teams for this specific game
            game_teams = user_teams.filter(game=tournament.game) if tournament.game else user_teams
            print(f"   Teams for game '{tournament.game.name if tournament.game else 'Any'}': {game_teams.count()}")
            
            # Check teams where user is captain/co-captain
            captain_teams = game_teams.filter(
                members__user=user,
                members__role__in=['captain', 'co_captain']
            ).distinct()
            print(f"   Teams where user is captain/co-captain: {captain_teams.count()}")
            
            if captain_teams.exists():
                print("   ✅ User has eligible teams")
                for team in captain_teams:
                    print(f"      - {team.name} (members: {team.members.filter(status='active').count()})")
                    
                    # Check team size requirement
                    active_members = team.members.filter(status='active').count()
                    meets_size = active_members >= (tournament.team_size or 1)
                    print(f"        Active members: {active_members}, Required: {tournament.team_size}, Meets requirement: {meets_size}")
            else:
                print("   ❌ User has no eligible teams (not captain/co-captain)")
                
                # Show all user teams for debugging
                if user_teams.exists():
                    print("   User's teams (all roles):")
                    for team in user_teams:
                        membership = TeamMember.objects.filter(team=team, user=user).first()
                        print(f"      - {team.name} (role: {membership.role if membership else 'unknown'})")
            
        except ImportError:
            print("   ❌ Teams app not available")
        except Exception as e:
            print(f"   ❌ Error checking teams: {str(e)}")
        
        print()
    
    # Check for common team-based tournament issues
    print("🔧 TEAM TOURNAMENT ISSUES CHECK")
    print("=" * 35)
    
    # Issue 1: Tournaments without game assigned
    no_game_tournaments = team_tournaments.filter(game__isnull=True)
    print(f"🎯 Team tournaments without game: {no_game_tournaments.count()}")
    if no_game_tournaments.exists():
        print("   ⚠️  These tournaments need a game assigned")
        for t in no_game_tournaments:
            print(f"      - {t.name} (slug: {t.slug})")
    
    # Issue 2: Tournaments with no team size specified
    no_team_size = team_tournaments.filter(team_size__isnull=True)
    print(f"👥 Team tournaments without team size: {no_team_size.count()}")
    if no_team_size.exists():
        print("   ⚠️  These tournaments need team_size specified")
        for t in no_team_size:
            print(f"      - {t.name} (slug: {t.slug})")
    
    # Issue 3: Check if teams exist in the system
    try:
        from teams.models import Team
        total_teams = Team.objects.filter(status='active').count()
        print(f"🏅 Total active teams in system: {total_teams}")
        
        if total_teams == 0:
            print("   ❌ No active teams found - users cannot register for team tournaments")
        
        # Check teams by game
        if team_tournaments.exists():
            for tournament in team_tournaments[:3]:
                if tournament.game:
                    game_teams = Team.objects.filter(game=tournament.game, status='active').count()
                    print(f"   Teams for {tournament.game.name}: {game_teams}")
    except ImportError:
        print("❌ Teams app not available")
    
    print()
    print("🛠️  RECOMMENDED FIXES FOR TEAM TOURNAMENTS")
    print("=" * 45)
    
    print("1. Ensure team tournaments have:")
    print("   - game field assigned")
    print("   - team_size specified (e.g., 5 for 5v5)")
    print("   - status = 'registration'")
    print()
    
    print("2. Ensure users have teams:")
    print("   - Create teams for the tournament game")
    print("   - Assign users as captain or co-captain")
    print("   - Ensure teams have enough active members")
    print()
    
    print("3. Check teams app configuration:")
    print("   - Verify teams app is in INSTALLED_APPS")
    print("   - Run migrations for teams app")
    print("   - Check team model relationships")

if __name__ == '__main__':
    debug_team_tournament_registration()