#!/usr/bin/env python3
"""
Simple test to verify the team captain registration fix
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
from tournaments.models import Tournament
from teams.models import Team, TeamMember
from core.models import Game

User = get_user_model()

def test_fix():
    """Test the fix for team captain registration"""
    
    print("🧪 TESTING TEAM CAPTAIN REGISTRATION FIX")
    print("=" * 50)
    
    try:
        # Get existing data or create minimal test data
        game = Game.objects.first()
        if not game:
            game = Game.objects.create(name='Test Game', slug='test-game')
        
        # Find an existing team-based tournament or create one
        tournament = Tournament.objects.filter(is_team_based=True).first()
        if not tournament:
            organizer = User.objects.first()
            if not organizer:
                organizer = User.objects.create_user(
                    username='test_organizer',
                    email='organizer@test.com'
                )
            
            tournament = Tournament.objects.create(
                name='Test Team Tournament',
                slug='test-team-tournament-fix',
                game=game,
                organizer=organizer,
                is_team_based=True,
                team_size=5,
                status='registration',
                registration_start=timezone.now() - timedelta(hours=1),
                registration_end=timezone.now() + timedelta(hours=24),
                check_in_start=timezone.now() + timedelta(hours=23),
                start_datetime=timezone.now() + timedelta(days=1),
                max_participants=16,
                min_participants=4
            )
        
        # Find an existing team captain or create one
        captain = None
        team = None
        
        # Look for existing team captain
        captain_membership = TeamMember.objects.filter(
            role='captain',
            status='active',
            team__game=tournament.game,
            team__status='active'
        ).first()
        
        if captain_membership:
            captain = captain_membership.user
            team = captain_membership.team
        else:
            # Create test captain and team
            captain = User.objects.create_user(
                username='test_captain_fix',
                email='captain@test.com'
            )
            
            team = Team.objects.create(
                name='Test Team Fix',
                slug='test-team-fix',
                tag='FIX',
                game=tournament.game,
                captain=captain,
                status='active'
            )
            
            TeamMember.objects.create(
                team=team,
                user=captain,
                role='captain',
                status='active',
                approved_at=timezone.now()
            )
        
        print(f"✅ Using tournament: {tournament.name}")
        print(f"✅ Using team: {team.name}")
        print(f"✅ Using captain: {captain.username}")
        
        # Test the can_user_register method
        print(f"\n🔍 TESTING can_user_register METHOD")
        can_register, message = tournament.can_user_register(captain)
        
        print(f"   Result: {can_register}")
        print(f"   Message: {message}")
        
        if can_register:
            print("✅ SUCCESS: Team captain can register for team tournament")
            print("\n🎉 FIX IS WORKING!")
            print("Team captains can now register for team-based tournaments.")
            return True
        else:
            print(f"❌ FAILED: Team captain cannot register - {message}")
            return False
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_fix()
    sys.exit(0 if success else 1)