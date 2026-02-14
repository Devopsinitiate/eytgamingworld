#!/usr/bin/env python3
"""
Test script to verify team application UI workflow
Tests that team admins can see and manage applications through the web interface
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from teams.models import Team, TeamMember
from notifications.models import Notification

User = get_user_model()

def test_team_application_ui():
    print("=== Team Application UI Test ===\n")
    
    # Find a team with pending applications
    teams_with_applications = Team.objects.filter(
        members__status='pending'
    ).distinct().select_related('captain')
    
    print(f"Found {teams_with_applications.count()} teams with pending applications:")
    for team in teams_with_applications:
        pending_count = team.members.filter(status='pending').count()
        print(f"  - {team.name}: {pending_count} pending applications")
    
    if not teams_with_applications.exists():
        print("No teams with pending applications found!")
        return
    
    test_team = teams_with_applications.first()
    captain = test_team.captain
    
    print(f"\nUsing team: {test_team.name}")
    print(f"Captain: {captain.get_display_name()}")
    
    # Get pending applications
    pending_applications = test_team.members.filter(status='pending')
    print(f"Pending applications: {pending_applications.count()}")
    
    for app in pending_applications:
        print(f"  - {app.user.get_display_name()} (Applied: {app.joined_at})")
    
    # Test 1: Check if captain can access roster page
    print("\n=== Test 1: Captain Access to Roster Page ===")
    client = Client()
    
    # Login as captain
    client.force_login(captain)
    
    roster_url = reverse('teams:roster', kwargs={'slug': test_team.slug})
    print(f"Roster URL: {roster_url}")
    
    try:
        response = client.get(roster_url)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Captain can access roster page")
            
            # Check if pending applications are in the context
            if 'pending_applications' in response.context:
                context_applications = response.context['pending_applications']
                print(f"✓ Pending applications in context: {context_applications.count()}")
                
                for app in context_applications:
                    print(f"  - {app.user.get_display_name()}")
            else:
                print("✗ No pending_applications in context")
                
            # Check if the HTML contains application elements
            content = response.content.decode('utf-8')
            if 'Pending Applications' in content:
                print("✓ 'Pending Applications' section found in HTML")
            else:
                print("✗ 'Pending Applications' section not found in HTML")
                
            if 'application_approve' in content:
                print("✓ Approve buttons found in HTML")
            else:
                print("✗ Approve buttons not found in HTML")
                
        else:
            print(f"✗ Captain cannot access roster page (status: {response.status_code})")
            
    except Exception as e:
        print(f"✗ Error accessing roster page: {e}")
    
    # Test 2: Test application approval
    print("\n=== Test 2: Application Approval Test ===")
    if pending_applications.exists():
        test_application = pending_applications.first()
        approve_url = reverse('teams:application_approve', kwargs={
            'slug': test_team.slug,
            'member_id': test_application.id
        })
        print(f"Approve URL: {approve_url}")
        
        try:
            response = client.post(approve_url)
            print(f"Approval response status: {response.status_code}")
            
            if response.status_code == 302:  # Redirect after successful approval
                print("✓ Application approval successful (redirected)")
                
                # Check if application status changed
                test_application.refresh_from_db()
                print(f"Application status after approval: {test_application.status}")
                
                if test_application.status == 'active':
                    print("✓ Application status changed to active")
                else:
                    print(f"✗ Application status is still: {test_application.status}")
                    
            else:
                print(f"✗ Application approval failed (status: {response.status_code})")
                
        except Exception as e:
            print(f"✗ Error during approval: {e}")
    
    # Test 3: Check notifications
    print("\n=== Test 3: Notification Check ===")
    captain_notifications = Notification.objects.filter(
        user=captain,
        notification_type='team',
        title__icontains='Application'
    ).order_by('-created_at')
    
    print(f"Captain has {captain_notifications.count()} team application notifications")
    
    unread_count = captain_notifications.filter(read=False).count()
    print(f"Unread notifications: {unread_count}")
    
    if captain_notifications.exists():
        latest = captain_notifications.first()
        print(f"Latest notification: {latest.title}")
        print(f"Message: {latest.message}")
        print(f"Created: {latest.created_at}")
        print(f"Read: {latest.read}")
    
    # Test 4: Check team detail page application button
    print("\n=== Test 4: Team Detail Page Application Button ===")
    
    # Create a test user who can apply
    test_user = User.objects.exclude(
        id__in=test_team.members.values_list('user_id', flat=True)
    ).exclude(
        id=captain.id
    ).first()
    
    if test_user:
        print(f"Test user: {test_user.get_display_name()}")
        
        # Login as test user
        client.force_login(test_user)
        
        detail_url = reverse('teams:detail', kwargs={'slug': test_team.slug})
        response = client.get(detail_url)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            if test_team.is_recruiting and not test_team.is_full:
                if 'Apply to Join' in content:
                    print("✓ 'Apply to Join' button found on team detail page")
                else:
                    print("✗ 'Apply to Join' button not found")
                    
                # Test application submission
                apply_url = reverse('teams:apply', kwargs={'slug': test_team.slug})
                response = client.post(apply_url)
                
                if response.status_code == 302:
                    print("✓ Application submission successful")
                    
                    # Check if application was created
                    new_application = TeamMember.objects.filter(
                        team=test_team,
                        user=test_user,
                        status='pending'
                    ).first()
                    
                    if new_application:
                        print("✓ Application record created in database")
                        
                        # Clean up test application
                        new_application.delete()
                        print("✓ Test application cleaned up")
                    else:
                        print("✗ Application record not found in database")
                else:
                    print(f"✗ Application submission failed (status: {response.status_code})")
            else:
                print("Team is not recruiting or is full - application button should not be visible")
        else:
            print(f"✗ Cannot access team detail page (status: {response.status_code})")
    else:
        print("No test user available for application test")
    
    print("\n=== UI Test Complete ===")

if __name__ == '__main__':
    test_team_application_ui()