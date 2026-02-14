#!/usr/bin/env python3
"""
Fix tournament check-in automation issue
This script will:
1. Check current tournament statuses
2. Move tournaments to check-in if they should be there
3. Test the automated status system
4. Provide manual override options
"""

import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament
from tournaments.tasks import check_tournament_start_times, send_check_in_notifications

def check_current_tournaments():
    """Check current tournament statuses and identify issues"""
    print("🔍 Checking current tournament statuses...")
    
    now = timezone.now()
    
    # Find tournaments that should be in check-in but aren't
    should_be_checkin = Tournament.objects.filter(
        status='registration',
        registration_end__lte=now,
        check_in_start__lte=now,
        start_datetime__gt=now
    )
    
    print(f"\n📊 Tournament Status Analysis (Current time: {now})")
    print("=" * 60)
    
    if should_be_checkin.exists():
        print(f"⚠️  Found {should_be_checkin.count()} tournaments that should be in check-in:")
        for tournament in should_be_checkin:
            print(f"   - {tournament.name} (slug: {tournament.slug})")
            print(f"     Registration ended: {tournament.registration_end}")
            print(f"     Check-in started: {tournament.check_in_start}")
            print(f"     Tournament starts: {tournament.start_datetime}")
            print(f"     Current status: {tournament.status}")
            print()
    else:
        print("✅ No tournaments found that should be in check-in")
    
    # Find tournaments that should have started
    should_have_started = Tournament.objects.filter(
        status='check_in',
        start_datetime__lte=now
    )
    
    if should_have_started.exists():
        print(f"⚠️  Found {should_have_started.count()} tournaments that should have started:")
        for tournament in should_have_started:
            print(f"   - {tournament.name} (slug: {tournament.slug})")
            print(f"     Start time: {tournament.start_datetime}")
            print(f"     Checked in: {tournament.total_checked_in}/{tournament.min_participants}")
            print(f"     Current status: {tournament.status}")
            print()
    else:
        print("✅ No tournaments found that should have started")
    
    return should_be_checkin, should_have_started

def fix_tournament_statuses(should_be_checkin, should_have_started, auto_fix=False):
    """Fix tournament statuses"""
    
    if not should_be_checkin.exists() and not should_have_started.exists():
        print("✅ No tournaments need status fixes")
        return
    
    if not auto_fix:
        print("\n🔧 Manual Fix Options:")
        print("1. Move tournaments to check-in period")
        print("2. Force start tournaments (regardless of participant count)")
        print("3. Run automated status check")
        print("4. Exit without changes")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '4':
            print("Exiting without changes")
            return
        elif choice == '3':
            print("Running automated status check...")
            run_automation()
            return
        elif choice not in ['1', '2']:
            print("Invalid choice")
            return
    else:
        choice = '1'  # Auto-fix mode
    
    if choice == '1' and should_be_checkin.exists():
        print(f"\n🔄 Moving {should_be_checkin.count()} tournaments to check-in...")
        
        for tournament in should_be_checkin:
            print(f"   Moving {tournament.name} to check-in...")
            tournament.status = 'check_in'
            tournament.save()
            
            # Send check-in notifications
            try:
                send_check_in_notifications.delay(tournament.id)
                print(f"   ✅ Check-in notifications queued for {tournament.name}")
            except Exception as e:
                print(f"   ⚠️  Failed to queue notifications for {tournament.name}: {e}")
        
        print("✅ Tournaments moved to check-in period")
    
    elif choice == '2':
        tournaments_to_start = should_have_started if should_have_started.exists() else should_be_checkin
        
        print(f"\n🚀 Force starting {tournaments_to_start.count()} tournaments...")
        
        for tournament in tournaments_to_start:
            print(f"   Starting {tournament.name}...")
            tournament.status = 'in_progress'
            tournament.save()
            
            # Generate bracket
            try:
                from tournaments.services.bracket_generator import BracketGenerator
                generator = BracketGenerator(tournament)
                generator.generate_bracket()
                print(f"   ✅ Bracket generated for {tournament.name}")
                
                # Send start notifications
                from tournaments.tasks import send_tournament_start_notifications
                send_tournament_start_notifications.delay(tournament.id)
                print(f"   ✅ Start notifications queued for {tournament.name}")
                
            except Exception as e:
                print(f"   ⚠️  Error starting {tournament.name}: {e}")
        
        print("✅ Tournaments force started")

def run_automation():
    """Run the automated status check task"""
    print("\n🤖 Running automated tournament status check...")
    
    try:
        # Run the task synchronously for immediate feedback
        result = check_tournament_start_times()
        print("✅ Automated status check completed")
        
        # Check results
        check_current_tournaments()
        
    except Exception as e:
        print(f"❌ Error running automation: {e}")

def test_automation_schedule():
    """Test if the automation is properly scheduled"""
    print("\n🕐 Testing automation schedule...")
    
    try:
        from celery import current_app
        
        # Check if the beat schedule is configured
        beat_schedule = current_app.conf.beat_schedule
        
        if 'check-tournament-start-times' in beat_schedule:
            schedule_info = beat_schedule['check-tournament-start-times']
            print(f"✅ Automation task is scheduled:")
            print(f"   Task: {schedule_info['task']}")
            print(f"   Schedule: {schedule_info['schedule']}")
        else:
            print("❌ Automation task is not scheduled in Celery Beat")
            
        # Check if Celery is running
        inspect = current_app.control.inspect()
        active_tasks = inspect.active()
        
        if active_tasks:
            print("✅ Celery workers are active")
        else:
            print("⚠️  No active Celery workers found")
            
    except Exception as e:
        print(f"⚠️  Could not check automation schedule: {e}")

def main():
    """Main function"""
    print("🎮 Tournament Check-in Automation Fix")
    print("=" * 40)
    
    # Check current status
    should_be_checkin, should_have_started = check_current_tournaments()
    
    # Test automation
    test_automation_schedule()
    
    # Offer fixes
    if should_be_checkin.exists() or should_have_started.exists():
        print("\n🔧 Issues found that need fixing!")
        fix_tournament_statuses(should_be_checkin, should_have_started)
    else:
        print("\n✅ No issues found. Tournament automation appears to be working correctly.")
    
    print("\n📋 Next Steps:")
    print("1. Ensure Celery Beat is running: celery -A config beat")
    print("2. Ensure Celery workers are running: celery -A config worker")
    print("3. Check Django admin for manual tournament management")
    print("4. Monitor tournament statuses regularly")

if __name__ == '__main__':
    main()