#!/usr/bin/env python3
"""
Debug script for team application workflow
Tests the complete flow from user application to admin notification
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
from django.utils import timezone

User = get_user_model()

def debug_team_applications():
    print("=== Team Application Workflow Debug ===\n")
    
    # Find a team that is recruiting
    recruiting_teams = Team.objects.filter(
        status='active',
        is_recruiting=True,
        is_public=True
    ).select_related('captain', 'game')
    
    print(f"Found {recruiting_teams.count()} recruiting teams:")
    for team in recruiting_teams[:5]:
        print(f"  - {team.name} [{team.tag}] (Game: {team.game.name})")
        print(f"    Captain: {team.captain.get_display_name()}")
        print(f"    Members: {team.member_count}/{team.max_members}")
        print(f"    Requires approval: {team.requires_approval}")
        print()
    
    if not recruiting_teams.exists():
        print("No recruiting teams found!")
        return
    
    # Use the first recruiting team for testing
    test_team = recruiting_teams.first()
    print(f"Using team: {test_team.name} for testing\n")
    
    # Find a user who is not a member of this team
    team_member_user_ids = test_team.members.values_list('user_id', flat=True)
    test_user = User.objects.exclude(
        id__in=team_member_user_ids
    ).exclude(
        id=test_team.captain.id
    ).first()
    
    if not test_user:
        print("No available test user found!")
        return
    
    print(f"Test user: {test_user.get_display_name()} (ID: {test_user.id})")
    print()
    
    # Check existing applications from this user
    existing_application = TeamMember.objects.filter(
        team=test_team,
        user=test_user
    ).first()
    
    if existing_application:
        print(f"Existing application found: Status = {existing_application.status}")
        if existing_application.status == 'pending':
            print("Application is already pending - testing notification system")
        elif existing_application.status == 'active':
            print("User is already an active member")
            return
        else:
            print(f"Application status: {existing_application.status}")
            # Delete old application for fresh test
            existing_application.delete()
            print("Deleted old application for fresh test")
    
    # Test 1: Create a new application
    print("=== Test 1: Creating Team Application ===")
    try:
        application = TeamMember.objects.create(
            team=test_team,
            user=test_user,
            role='member',
            status='pending'
        )
        print(f"✓ Application created successfully (ID: {application.id})")
        print(f"  Team: {application.team.name}")
        print(f"  User: {application.user.get_display_name()}")
        print(f"  Status: {application.status}")
        print(f"  Created: {application.joined_at}")
    except Exception as e:
        print(f"✗ Failed to create application: {e}")
        return
    
    # Test 2: Check if notification was sent to captain
    print("\n=== Test 2: Checking Captain Notifications ===")
    captain_notifications = Notification.objects.filter(
        user=test_team.captain,
        notification_type='team',
        title__icontains='Application'
    ).order_by('-created_at')
    
    print(f"Found {captain_notifications.count()} team application notifications for captain:")
    for notif in captain_notifications[:3]:
        print(f"  - {notif.title}")
        print(f"    Message: {notif.message}")
        print(f"    Created: {notif.created_at}")
        print(f"    Read: {notif.read}")
        print(f"    Priority: {notif.priority}")
        print()
    
    # Test 3: Test notification service directly
    print("=== Test 3: Testing Notification Service ===")
    try:
        from teams.notification_service import TeamNotificationService
        
        # Send notification manually
        TeamNotificationService.notify_new_application(application, test_team)
        print("✓ Notification service called successfully")
        
        # Check if new notification was created
        latest_notification = Notification.objects.filter(
            user=test_team.captain,
            notification_type='team'
        ).order_by('-created_at').first()
        
        if latest_notification:
            print(f"✓ Latest notification found:")
            print(f"  Title: {latest_notification.title}")
            print(f"  Message: {latest_notification.message}")
            print(f"  Created: {latest_notification.created_at}")
        else:
            print("✗ No notifications found after manual call")
            
    except Exception as e:
        print(f"✗ Notification service error: {e}")
    
    # Test 4: Check team roster view data
    print("\n=== Test 4: Checking Team Roster View Data ===")
    pending_applications = test_team.members.filter(status='pending')
    print(f"Pending applications for {test_team.name}: {pending_applications.count()}")
    
    for app in pending_applications:
        print(f"  - {app.user.get_display_name()} (Applied: {app.joined_at})")
    
    # Test 5: Test approval workflow
    print("\n=== Test 5: Testing Application Approval ===")
    try:
        # Approve the application
        application.status = 'active'
        application.approved_at = timezone.now()
        application.save()
        print("✓ Application approved successfully")
        
        # Test approval notification
        TeamNotificationService.notify_application_approved(application, test_team)
        print("✓ Approval notification sent")
        
        # Check user's notifications
        user_notifications = Notification.objects.filter(
            user=test_user,
            notification_type='team',
            title__icontains='Approved'
        ).order_by('-created_at')
        
        print(f"User approval notifications: {user_notifications.count()}")
        for notif in user_notifications[:2]:
            print(f"  - {notif.title}: {notif.message}")
            
    except Exception as e:
        print(f"✗ Approval test error: {e}")
    
    # Test 6: Check URLs and views
    print("\n=== Test 6: Checking URL Configuration ===")
    try:
        from django.urls import reverse
        
        # Test URL patterns
        urls_to_test = [
            ('teams:apply', {'slug': test_team.slug}),
            ('teams:roster', {'slug': test_team.slug}),
            ('teams:application_approve', {'slug': test_team.slug, 'member_id': application.id}),
            ('teams:application_decline', {'slug': test_team.slug, 'member_id': application.id}),
        ]
        
        for url_name, kwargs in urls_to_test:
            try:
                url = reverse(url_name, kwargs=kwargs)
                print(f"✓ {url_name}: {url}")
            except Exception as e:
                print(f"✗ {url_name}: {e}")
                
    except Exception as e:
        print(f"✗ URL test error: {e}")
    
    # Cleanup
    print("\n=== Cleanup ===")
    try:
        # Remove test application
        application.delete()
        print("✓ Test application cleaned up")
    except Exception as e:
        print(f"✗ Cleanup error: {e}")
    
    print("\n=== Debug Complete ===")

if __name__ == '__main__':
    debug_team_applications()