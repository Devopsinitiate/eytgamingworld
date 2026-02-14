#!/usr/bin/env python3
"""
Debug tournament times for Battle tournament
"""

import os
import sys
import django
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament

def debug_tournament_times():
    """Debug tournament times"""
    print("🕐 Debugging Tournament Times")
    print("=" * 30)
    
    try:
        tournament = Tournament.objects.get(slug='Battle')
        now = timezone.now()
        
        print(f"Tournament: {tournament.name}")
        print(f"Current time: {now}")
        print(f"Status: {tournament.status}")
        print()
        
        print("📅 Tournament Schedule:")
        print(f"Registration start: {tournament.registration_start}")
        print(f"Registration end:   {tournament.registration_end}")
        print(f"Check-in start:     {tournament.check_in_start}")
        print(f"Tournament start:   {tournament.start_datetime}")
        if tournament.estimated_end:
            print(f"Estimated end:      {tournament.estimated_end}")
        print()
        
        print("🔍 Time Checks:")
        print(f"Now >= registration_start: {now >= tournament.registration_start}")
        print(f"Now >= registration_end:   {now >= tournament.registration_end}")
        print(f"Now >= check_in_start:     {now >= tournament.check_in_start}")
        print(f"Now >= start_datetime:     {now >= tournament.start_datetime}")
        print()
        
        print("🎯 Status Logic:")
        print(f"Should be registration: {tournament.registration_start <= now < tournament.registration_end}")
        print(f"Should be check-in:     {tournament.registration_end <= now < tournament.start_datetime}")
        print(f"Should be in_progress:  {now >= tournament.start_datetime}")
        print()
        
        print("✅ Current Properties:")
        print(f"is_registration_open: {tournament.is_registration_open}")
        print(f"is_check_in_open:     {tournament.is_check_in_open}")
        print()
        
        # Check what the correct status should be
        if now >= tournament.start_datetime:
            print("🚨 Tournament should have started already!")
        elif now >= tournament.check_in_start and now >= tournament.registration_end:
            print("✅ Tournament should be in check-in period")
        elif tournament.registration_start <= now < tournament.registration_end:
            print("📝 Tournament should be in registration period")
        else:
            print("📋 Tournament should be in draft")
            
    except Tournament.DoesNotExist:
        print("❌ Tournament 'Battle' not found")

if __name__ == '__main__':
    debug_tournament_times()