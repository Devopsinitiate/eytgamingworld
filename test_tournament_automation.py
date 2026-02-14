#!/usr/bin/env python3
"""
Test tournament automation system
"""

import os
import sys
import django
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament
from tournaments.tasks import check_tournament_start_times

def test_automation():
    """Test the tournament automation system"""
    print("🧪 Testing Tournament Automation System")
    print("=" * 40)
    
    now = timezone.now()
    print(f"Current time: {now}")
    
    # Check tournaments by status
    statuses = ['draft', 'registration', 'check_in', 'in_progress', 'completed']
    
    print("\n📊 Tournament Status Overview:")
    for status in statuses:
        count = Tournament.objects.filter(status=status).count()
        print(f"   {status.replace('_', ' ').title()}: {count}")
    
    # Find tournaments that need status updates
    print("\n🔍 Checking for tournaments needing status updates...")
    
    # Draft -> Registration
    draft_ready = Tournament.objects.filter(
        status='draft',
        registration_start__lte=now,
        registration_end__gt=now
    )
    
    if draft_ready.exists():
        print(f"   📝 {draft_ready.count()} tournaments ready to open registration")
        for t in draft_ready:
            print(f"      - {t.name}")
    
    # Registration -> Check-in
    checkin_ready = Tournament.objects.filter(
        status='registration',
        registration_end__lte=now,
        check_in_start__lte=now
    )
    
    if checkin_ready.exists():
        print(f"   ✅ {checkin_ready.count()} tournaments ready for check-in")
        for t in checkin_ready:
            print(f"      - {t.name}")
    
    # Check-in -> In Progress
    start_ready = Tournament.objects.filter(
        status='check_in',
        start_datetime__lte=now
    )
    
    if start_ready.exists():
        print(f"   🚀 {start_ready.count()} tournaments ready to start")
        for t in start_ready:
            print(f"      - {t.name} ({t.total_checked_in}/{t.min_participants} checked in)")
    
    if not any([draft_ready.exists(), checkin_ready.exists(), start_ready.exists()]):
        print("   ✅ No tournaments need status updates")
    
    # Test the automation task
    print("\n🤖 Testing automation task...")
    try:
        check_tournament_start_times()
        print("   ✅ Automation task completed successfully")
    except Exception as e:
        print(f"   ❌ Automation task failed: {e}")
    
    # Check if anything changed
    print("\n📊 Status after automation:")
    for status in statuses:
        count = Tournament.objects.filter(status=status).count()
        print(f"   {status.replace('_', ' ').title()}: {count}")

if __name__ == '__main__':
    test_automation()