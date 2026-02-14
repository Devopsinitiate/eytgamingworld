#!/usr/bin/env python3
"""
Test the check-in fix
"""

import os
import sys
import django
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament, Participant
from teams.models import TeamMember

def test_checkin_fix():
    """Test the check-in fix"""
    print("🧪 Testing Check-in Fix")
    print("=" * 25)
    
    # Get the tournament and user
    tournament = Tournament.objects.get(slug='Battle')
    User = get_user_model()
    user = User.objects.get(id='599c68de-d0d6-4c41-a04b-ca3d9ade46c4')
    
    print(f"Tournament: {tournament.name}")
    print(f"Status: {tournament.status}")
    print(f"User: {user.username}")
    print()
    
    # Check current participant status
    team_member = TeamMember.objects.filter(user=user, status='active').first()
    if team_member:
        participant = Participant.objects.filter(
            tournament=tournament,
            team=team_member.team
        ).first()
        
        if participant:
            print(f"Team: {participant.team.name}")
            print(f"Participant status: {participant.status}")
            print(f"Checked in: {participant.checked_in}")
            print()
            
            # Test the check-in logic manually
            print("🔧 Testing check-in logic...")
            
            # Check if can check in
            can_check_in = (
                tournament.status == 'check_in' or 
                (tournament.status == 'in_progress' and tournament.total_checked_in < tournament.min_participants)
            )
            
            print(f"Can check in: {can_check_in}")
            
            if can_check_in:
                # Try to check in
                if participant.check_in_participant(force=True):
                    print("✅ Check-in successful!")
                    
                    # Update tournament count
                    tournament.total_checked_in = tournament.participants.filter(checked_in=True).count()
                    tournament.save(update_fields=['total_checked_in'])
                    
                    print(f"Tournament checked-in count: {tournament.total_checked_in}")
                else:
                    print("❌ Check-in failed")
            else:
                print("❌ Check-in not allowed")
        else:
            print("❌ No participant record found for user's team")
    else:
        print("❌ User is not a member of any team")

if __name__ == '__main__':
    test_checkin_fix()