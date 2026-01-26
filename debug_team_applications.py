#!/usr/bin/env python
"""
Debug script to check team applications and identify the issue
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from teams.models import Team, TeamMember
from core.models import User

def debug_team_applications():
    """Debug team applications to identify the issue"""
    print("🔍 Debugging Team Applications...")
    
    # Check the specific team mentioned in the error
    try:
        team = Team.objects.get(slug='redbull')
        print(f"✅ Found team: {team.name} (ID: {team.id})")
        
        # Check all team members
        all_members = TeamMember.objects.filter(team=team)
        print(f"\n📋 All team members for {team.name}:")
        for member in all_members:
            print(f"  - {member.user.get_display_name()} | Status: {member.status} | Role: {member.role} | ID: {member.id}")
        
        # Check pending applications specifically
        pending_applications = TeamMember.objects.filter(team=team, status='pending')
        print(f"\n⏳ Pending applications for {team.name}:")
        if pending_applications.exists():
            for app in pending_applications:
                print(f"  - {app.user.get_display_name()} | ID: {app.id} | Applied: {app.joined_at}")
        else:
            print("  No pending applications found")
        
        # Check the specific ID from the error
        problem_id = 'a0bcaccc-eefb-435c-a386-3739ae9a3f06'
        print(f"\n🔍 Checking specific ID: {problem_id}")
        
        try:
            specific_member = TeamMember.objects.get(id=problem_id)
            print(f"  ✅ Found member: {specific_member.user.get_display_name()}")
            print(f"     Team: {specific_member.team.name}")
            print(f"     Status: {specific_member.status}")
            print(f"     Role: {specific_member.role}")
            print(f"     Applied: {specific_member.joined_at}")
            print(f"     Approved: {specific_member.approved_at}")
        except TeamMember.DoesNotExist:
            print(f"  ❌ No TeamMember found with ID: {problem_id}")
            
            # Check if it exists in any team
            all_members_with_id = TeamMember.objects.filter(id=problem_id)
            if all_members_with_id.exists():
                member = all_members_with_id.first()
                print(f"     But found in team: {member.team.name} with status: {member.status}")
            else:
                print("     ID doesn't exist in any team")
        
        # Check recent activity
        print(f"\n📅 Recent team member activity (last 24 hours):")
        from django.utils import timezone
        from datetime import timedelta
        
        recent_activity = TeamMember.objects.filter(
            team=team,
            joined_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-joined_at')
        
        for member in recent_activity:
            print(f"  - {member.user.get_display_name()} | Status: {member.status} | Time: {member.joined_at}")
            
    except Team.DoesNotExist:
        print("❌ Team 'redbull' not found")
        
        # List all teams
        print("\n📋 Available teams:")
        teams = Team.objects.all()[:10]
        for team in teams:
            print(f"  - {team.name} (slug: {team.slug})")

if __name__ == '__main__':
    debug_team_applications()