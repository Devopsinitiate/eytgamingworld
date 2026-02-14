#!/usr/bin/env python3
"""
Real-world test of team application workflow
Tests the actual user experience step by step
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from teams.models import Team, TeamMember
from notifications.models import Notification

User = get_user_model()

def test_real_workflow():
    print("=== Real Team Application Workflow Test ===\n")
    
    # Step 1: Find a recruiting team
    recruiting_teams = Team.objects.filter(
        status='active',
        is_recruiting=True,
        is_public=True
    ).select_related('captain')
    
    if not recruiting_teams.exists():
        print("❌ No recruiting teams found!")
        print("SOLUTION: Team admins need to enable recruiting on their teams")
        print("Go to Team Settings > Enable 'Currently Recruiting' toggle")
        return
    
    test_team = recruiting_teams.first()
    print(f"✅ Found recruiting team: {test_team.name}")
    print(f"   Captain: {test_team.captain.get_display_name()}")
    print(f"   Email: {test_team.captain.email}")
    print(f"   Members: {test_team.member_count}/{test_team.max_members}")
    print()
    
    # Step 2: Check if team admin knows how to access applications
    print("=== Step 2: How Team Admins Access Applications ===")
    print(f"Team admins should:")
    print(f"1. Go to their team page: /teams/{test_team.slug}/")
    print(f"2. Click 'Manage Team' button (only visible to captains)")
    print(f"3. Navigate to 'Roster Management' or go directly to: /teams/{test_team.slug}/roster/")
    print(f"4. Look for 'Pending Applications' section")
    print()
    
    # Step 3: Check current pending applications
    pending_apps = test_team.members.filter(status='pending')
    print(f"=== Step 3: Current Pending Applications ===")
    print(f"Team {test_team.name} has {pending_apps.count()} pending applications:")
    
    if pending_apps.exists():
        for app in pending_apps:
            print(f"  - {app.user.get_display_name()} (Applied: {app.joined_at.strftime('%Y-%m-%d %H:%M')})")
        print()
        print("✅ Applications exist! Team admin should see these in the roster page.")
    else:
        print("  No pending applications found.")
        print()
        print("Let's create a test application...")
        
        # Find a user who can apply
        test_user = User.objects.exclude(
            id__in=test_team.members.values_list('user_id', flat=True)
        ).exclude(
            id=test_team.captain.id
        ).first()
        
        if test_user:
            # Create test application
            app = TeamMember.objects.create(
                team=test_team,
                user=test_user,
                role='member',
                status='pending'
            )
            print(f"✅ Created test application from {test_user.get_display_name()}")
            
            # Send notification
            from teams.notification_service import TeamNotificationService
            TeamNotificationService.notify_new_application(app, test_team)
            print(f"✅ Notification sent to captain")
        else:
            print("❌ No available users to create test application")
    
    # Step 4: Check captain notifications
    print("=== Step 4: Captain Notification Status ===")
    captain_notifications = Notification.objects.filter(
        user=test_team.captain,
        notification_type='team',
        title__icontains='Application'
    ).order_by('-created_at')
    
    print(f"Captain has {captain_notifications.count()} application notifications:")
    unread_count = captain_notifications.filter(read=False).count()
    print(f"  - Unread: {unread_count}")
    print(f"  - Total: {captain_notifications.count()}")
    
    if captain_notifications.exists():
        latest = captain_notifications.first()
        print(f"  - Latest: '{latest.title}' ({latest.created_at.strftime('%Y-%m-%d %H:%M')})")
        print(f"  - Message: {latest.message}")
        
        if not latest.read:
            print("✅ Captain has unread application notifications")
        else:
            print("⚠️  Latest notification has been read")
    else:
        print("❌ No application notifications found for captain")
    
    # Step 5: Check team settings
    print("\n=== Step 5: Team Configuration Check ===")
    print(f"Team settings for {test_team.name}:")
    print(f"  - Is recruiting: {test_team.is_recruiting}")
    print(f"  - Requires approval: {test_team.requires_approval}")
    print(f"  - Is public: {test_team.is_public}")
    print(f"  - Is full: {test_team.is_full}")
    
    if not test_team.is_recruiting:
        print("❌ Team is not recruiting - users cannot apply")
    if not test_team.requires_approval:
        print("⚠️  Team doesn't require approval - applications auto-approved")
    if not test_team.is_public:
        print("⚠️  Team is private - only members can see it")
    if test_team.is_full:
        print("❌ Team is full - no new applications accepted")
    
    # Step 6: User experience check
    print("\n=== Step 6: User Application Experience ===")
    print("For users to apply to teams:")
    print("1. Go to /teams/ (team list)")
    print("2. Find recruiting teams (green 'Recruiting' badge)")
    print("3. Click on team name to view details")
    print("4. Click 'Apply to Join' button")
    print("5. Application is submitted and captain is notified")
    
    # Step 7: Troubleshooting guide
    print("\n=== Step 7: Troubleshooting Guide ===")
    print("If team admins are not receiving applications:")
    print()
    print("A. Check team is properly configured:")
    print("   - Team status is 'active'")
    print("   - 'Currently Recruiting' is enabled")
    print("   - Team is not full")
    print("   - Team is public (if you want public applications)")
    print()
    print("B. Check notification settings:")
    print("   - Captain's email is correct")
    print("   - Email notifications are enabled")
    print("   - Check spam folder")
    print()
    print("C. Check roster management page:")
    print(f"   - Go to /teams/{test_team.slug}/roster/")
    print("   - Look for 'Pending Applications' section")
    print("   - Only captains and co-captains can see this page")
    print()
    print("D. Check user permissions:")
    print("   - User must be team captain or co-captain")
    print("   - User must be logged in")
    print()
    
    # Final summary
    print("=== SUMMARY ===")
    if pending_apps.exists() and captain_notifications.exists():
        print("✅ Team application system is working correctly!")
        print("✅ Applications exist and notifications were sent")
        print(f"✅ Captain should check: /teams/{test_team.slug}/roster/")
    elif not test_team.is_recruiting:
        print("❌ Team is not recruiting - enable recruiting in team settings")
    elif test_team.is_full:
        print("❌ Team is full - remove members or increase max_members")
    else:
        print("⚠️  System appears to be working, but no applications found")
        print("    Users may not be aware they can apply to teams")
    
    print(f"\nDirect link for team admin: /teams/{test_team.slug}/roster/")

if __name__ == '__main__':
    test_real_workflow()