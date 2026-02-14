#!/usr/bin/env python3
"""
Test script to verify the team captain registration fix
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember
from core.models import Game

User = get_user_model()

def test_team_captain_registration():
    """Test that team captains can register for team tournaments"""
    
    print("🧪 TESTING TEAM CAPTAIN REGISTRATION FIX")
    print("=" * 50)
    
    # Create test data
    try:
        # Get or create a game
        game, created = Game.objects.get_or_create(
            name='Test Game',
            defaults={'slug': 'test-game'}
        )
        print(f"✅ Game: {game.name}")
        
        # Get or create test users
        captain_user, created = User.objects.get_or_create(
            username='test_captain',
            defaults={
                'email': 'captain@test.com',
                'first_name': 'Test',
                'last_name': 'Captain'
            }
        )
        print(f"✅ Captain user: {captain_user.username}")
        
        organizer_user, created = User.objects.get_or_create(
            username='test_organizer',
            defaults={
                'email': 'organizer@test.com',
                'first_name': 'Test',
                'last_name': 'Organizer'
            }
        )
        print(f"✅ Organizer user: {organizer_user.username}")
        
        # Create a test team with the same game
        test_team, created = Team.objects.get_or_create(
            name='Test Team',
            defaults={
                'slug': 'test-team',
                'tag': 'TEST',
                'game': game,  # Use the same game as tournament
                'captain': captain_user,
                'status': 'active'
            }
        )
        
        # If team already exists but with wrong game, update it
        if not created and test_team.game != game:
            test_team.game = game
            test_team.save()
            
        print(f"✅ Team: {test_team.name} (Game: {test_team.game.name})")
        
        # Create team membership for captain
        membership, created = TeamMember.objects.get_or_create(
            team=test_team,
            user=captain_user,
            defaults={
                'role': 'captain',
                'status': 'active',
                'approved_at': timezone.now()
            }
        )
        print(f"✅ Team membership: {membership.role}")
        
        # Create a team-based tournament
        tournament, created = Tournament.objects.get_or_create(
            name='Test Team Tournament',
            defaults={
                'slug': 'test-team-tournament',
                'game': game,
                'organizer': organizer_user,
                'is_team_based': True,
                'team_size': 5,
                'status': 'registration',
                'registration_start': timezone.now() - timedelta(hours=1),
                'registration_end': timezone.now() + timedelta(hours=24),
                'check_in_start': timezone.now() + timedelta(hours=23),
                'start_datetime': timezone.now() + timedelta(days=1),
                'max_participants': 16,
                'min_participants': 4
            }
        )
        print(f"✅ Tournament: {tournament.name} (Team-based: {tournament.is_team_based})")
        
        # Test the can_user_register method
        print(f"\n🔍 TESTING can_user_register METHOD")
        
        # Debug: Check user's teams
        from teams.models import Team as TeamModel, TeamMember as TeamMemberModel
        
        print(f"   Debug: Checking team membership...")
        all_memberships = TeamMemberModel.objects.filter(user=captain_user)
        print(f"   Debug: User has {all_memberships.count()} total memberships")
        for mem in all_memberships:
            print(f"     - Team: {mem.team.name}, Role: {mem.role}, Status: {mem.status}, Game: {mem.team.game.name}")
        
        print(f"   Debug: Tournament game: {tournament.game.name}")
        print(f"   Debug: Team game: {test_team.game.name}")
        print(f"   Debug: Games match: {tournament.game == test_team.game}")
        
        user_teams = TeamModel.objects.filter(
            members__user=captain_user,
            members__status='active',
            members__role__in=['captain', 'co_captain'],
            status='active',
            game=game
        ).distinct()
        
        print(f"   Debug: User has {user_teams.count()} eligible teams")
        for team in user_teams:
            print(f"     - Team: {team.name} (Game: {team.game.name})")
        
        can_register, message = tournament.can_user_register(captain_user)
        print(f"   Result: {can_register}")
        print(f"   Message: {message}")
        
        if can_register:
            print("✅ SUCCESS: Team captain can register for team tournament")
        else:
            print(f"❌ FAILED: Team captain cannot register - {message}")
            return False
        
        # Test registration with team already registered
        print(f"\n🔍 TESTING DUPLICATE REGISTRATION PREVENTION")
        
        # Create a participant record (simulate team already registered)
        participant = Participant.objects.create(
            tournament=tournament,
            team=test_team,
            status='confirmed'
        )
        print(f"   Created participant for team: {participant.team.name}")
        
        # Test can_user_register again
        can_register_again, message_again = tournament.can_user_register(captain_user)
        print(f"   Result: {can_register_again}")
        print(f"   Message: {message_again}")
        
        if not can_register_again and "already registered" in message_again.lower():
            print("✅ SUCCESS: Duplicate registration properly prevented")
        else:
            print(f"❌ FAILED: Duplicate registration not prevented - {message_again}")
            return False
        
        # Clean up
        participant.delete()
        print(f"   Cleaned up test participant")
        
        # Test user without eligible teams
        print(f"\n🔍 TESTING USER WITHOUT ELIGIBLE TEAMS")
        
        regular_user, created = User.objects.get_or_create(
            username='regular_user',
            defaults={
                'email': 'regular@test.com',
                'first_name': 'Regular',
                'last_name': 'User'
            }
        )
        
        can_register_regular, message_regular = tournament.can_user_register(regular_user)
        print(f"   Result: {can_register_regular}")
        print(f"   Message: {message_regular}")
        
        if not can_register_regular and ("captain" in message_regular.lower() or "co-captain" in message_regular.lower()):
            print("✅ SUCCESS: Non-captain users properly blocked")
        else:
            print(f"❌ FAILED: Non-captain user not properly blocked - {message_regular}")
            return False
        
        print(f"\n🎉 ALL TESTS PASSED!")
        print("The team captain registration fix is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_team_captain_registration()
    sys.exit(0 if success else 1)