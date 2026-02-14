#!/usr/bin/env python
"""
Fix team-based tournament registration issues
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
from tournaments.models import Tournament

User = get_user_model()

def fix_team_tournament_registration():
    print("🔧 FIXING TEAM-BASED TOURNAMENT REGISTRATION")
    print("=" * 50)
    
    # Get team-based tournaments
    team_tournaments = Tournament.objects.filter(is_team_based=True)
    
    print(f"🏆 Found {team_tournaments.count()} team-based tournaments")
    
    now = timezone.now()
    
    for tournament in team_tournaments:
        print(f"\n🎮 Fixing: {tournament.name} (slug: {tournament.slug})")
        print(f"   Current status: {tournament.status}")
        print(f"   Registration start: {tournament.registration_start}")
        print(f"   Registration end: {tournament.registration_end}")
        
        needs_update = False
        
        # Fix status if needed
        if tournament.status != 'registration':
            print(f"   ✅ Changing status from '{tournament.status}' to 'registration'")
            tournament.status = 'registration'
            needs_update = True
        
        # Fix registration dates
        if not tournament.registration_start or tournament.registration_start > now:
            print(f"   ✅ Setting registration_start to now")
            tournament.registration_start = now
            needs_update = True
        
        if not tournament.registration_end or tournament.registration_end <= now:
            # Set registration to end in 24 hours
            new_end = now + timedelta(hours=24)
            print(f"   ✅ Setting registration_end to {new_end}")
            tournament.registration_end = new_end
            needs_update = True
        
        # Ensure tournament start is after registration end
        if tournament.start_datetime and tournament.registration_end >= tournament.start_datetime:
            new_start = tournament.registration_end + timedelta(hours=2)
            print(f"   ✅ Moving tournament start to {new_start}")
            tournament.start_datetime = new_start
            needs_update = True
        
        if needs_update:
            tournament.save()
            print(f"   💾 Tournament updated")
        else:
            print(f"   ✅ Tournament already properly configured")
    
    print(f"\n📊 CURRENT STATUS AFTER FIXES")
    print("=" * 35)
    
    # Show available team tournaments
    available_team_tournaments = Tournament.objects.filter(
        is_team_based=True,
        status='registration',
        registration_start__lte=now,
        registration_end__gte=now,
        is_public=True
    )
    
    print(f"🎮 Team tournaments available for registration: {available_team_tournaments.count()}")
    
    for tournament in available_team_tournaments:
        print(f"   - {tournament.name} (slug: {tournament.slug})")
        print(f"     Game: {tournament.game.name if tournament.game else 'No game'}")
        print(f"     Team size: {tournament.team_size}")
        print(f"     Registration ends: {tournament.registration_end}")
        
        # Check if user can register
        users = User.objects.filter(is_active=True)
        if users.exists():
            user = users.first()
            can_register, message = tournament.can_user_register(user)
            print(f"     Can register: {can_register} - {message}")
    
    # Check teams for available tournaments
    print(f"\n👥 TEAM AVAILABILITY CHECK")
    print("=" * 30)
    
    try:
        from teams.models import Team, TeamMember
        
        for tournament in available_team_tournaments:
            if tournament.game:
                teams_for_game = Team.objects.filter(
                    game=tournament.game,
                    status='active'
                ).count()
                print(f"🏅 Teams available for {tournament.name} ({tournament.game.name}): {teams_for_game}")
                
                if teams_for_game == 0:
                    print(f"   ⚠️  No teams available for this game - users cannot register")
                    
                    # Create a sample team for testing
                    print(f"   🔧 Creating sample team for {tournament.game.name}")
                    
                    # Get a user to be team captain
                    users = User.objects.filter(is_active=True)
                    if users.exists():
                        captain = users.first()
                        
                        # Create team with captain
                        team = Team.objects.create(
                            name=f"Sample Team for {tournament.game.name}",
                            game=tournament.game,
                            captain=captain,  # Set captain here
                            status='active',
                            description=f"Sample team created for testing {tournament.name}",
                            tag="SMPL"
                        )
                        
                        # Add captain as team member
                        TeamMember.objects.create(
                            team=team,
                            user=captain,
                            role='captain',
                            status='active'
                        )
                        
                        print(f"   ✅ Created team '{team.name}' with captain {captain.username}")
                        
                        # Add more members if needed for team size
                        if tournament.team_size and tournament.team_size > 1:
                            other_users = User.objects.filter(is_active=True).exclude(id=captain.id)[:tournament.team_size-1]
                            for i, user in enumerate(other_users):
                                TeamMember.objects.create(
                                    team=team,
                                    user=user,
                                    role='member',
                                    status='active'
                                )
                                print(f"   ✅ Added member {user.username} to team")
    
    except ImportError:
        print("❌ Teams app not available")
    except Exception as e:
        print(f"❌ Error managing teams: {str(e)}")

if __name__ == '__main__':
    fix_team_tournament_registration()