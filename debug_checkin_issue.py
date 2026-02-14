#!/usr/bin/env python3
"""
Debug the check-in issue for Battle tournament
"""

import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember

def debug_checkin_issue():
    """Debug the check-in issue"""
    print("🔍 Debugging Check-in Issue for Battle Tournament")
    print("=" * 50)
    
    # Get the tournament
    try:
        tournament = Tournament.objects.get(slug='Battle')
        print(f"✅ Found tournament: {tournament.name}")
        print(f"   Status: {tournament.status}")
        print(f"   Is team-based: {tournament.is_team_based}")
        print(f"   Check-in open: {tournament.is_check_in_open}")
        print()
    except Tournament.DoesNotExist:
        print("❌ Tournament 'Battle' not found")
        return
    
    # Get the user from the error
    User = get_user_model()
    user_id = '599c68de-d0d6-4c41-a04b-ca3d9ade46c4'
    
    try:
        user = User.objects.get(id=user_id)
        print(f"✅ Found user: {user.username} ({user.email})")
        print()
    except User.DoesNotExist:
        print(f"❌ User with ID {user_id} not found")
        return
    
    # Check for participant records
    print("🔍 Checking participant records...")
    
    # Check for individual participant
    individual_participant = Participant.objects.filter(
        tournament=tournament,
        user=user
    ).first()
    
    if individual_participant:
        print(f"✅ Found individual participant: {individual_participant}")
        print(f"   Status: {individual_participant.status}")
        print(f"   Checked in: {individual_participant.checked_in}")
    else:
        print("❌ No individual participant record found")
    
    # Check for team-based participant
    team_participants = Participant.objects.filter(
        tournament=tournament,
        team__isnull=False
    )
    
    print(f"\n🔍 Found {team_participants.count()} team participants:")
    for participant in team_participants:
        print(f"   - Team: {participant.team.name}")
        print(f"     Status: {participant.status}")
        print(f"     Checked in: {participant.checked_in}")
        
        # Check if user is a member of this team
        is_member = TeamMember.objects.filter(
            team=participant.team,
            user=user,
            status='active'
        ).exists()
        
        if is_member:
            print(f"     ✅ User {user.username} is a member of this team")
        else:
            print(f"     ❌ User {user.username} is NOT a member of this team")
        print()
    
    # Check user's team memberships
    print("🔍 Checking user's team memberships...")
    memberships = TeamMember.objects.filter(user=user, status='active')
    
    if memberships.exists():
        print(f"✅ User is member of {memberships.count()} teams:")
        for membership in memberships:
            print(f"   - {membership.team.name} (role: {membership.role})")
            
            # Check if this team is registered for the tournament
            team_participant = Participant.objects.filter(
                tournament=tournament,
                team=membership.team
            ).first()
            
            if team_participant:
                print(f"     ✅ Team is registered for tournament")
                print(f"     Status: {team_participant.status}")
                print(f"     Checked in: {team_participant.checked_in}")
            else:
                print(f"     ❌ Team is NOT registered for tournament")
    else:
        print("❌ User is not a member of any teams")
    
    print("\n" + "=" * 50)
    print("🔧 DIAGNOSIS:")
    
    if tournament.is_team_based:
        if not memberships.exists():
            print("❌ Issue: Tournament is team-based but user is not in any team")
        else:
            team_registered = any(
                Participant.objects.filter(tournament=tournament, team=m.team).exists()
                for m in memberships
            )
            if not team_registered:
                print("❌ Issue: User's teams are not registered for this tournament")
            else:
                print("✅ User's team is registered - check-in view needs to be fixed")
    else:
        if not individual_participant:
            print("❌ Issue: User is not registered for this individual tournament")
        else:
            print("✅ User is registered - check-in should work")

if __name__ == '__main__':
    debug_checkin_issue()