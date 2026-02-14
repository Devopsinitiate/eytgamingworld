#!/usr/bin/env python
"""Check coaching system status"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from coaching.models import CoachProfile, CoachAvailability

# Check active coaches
coaches = CoachProfile.objects.filter(is_verified=True, status='active')
print(f"✓ Active verified coaches: {coaches.count()}")

if coaches.exists():
    for coach in coaches[:3]:
        avail_count = coach.availability.filter(is_active=True).count()
        print(f"  - {coach.user.get_display_name()}: {avail_count} availability slots")
        
        # Check if coach has session_increment set
        if hasattr(coach, 'session_increment') and coach.session_increment:
            print(f"    Session increment: {coach.session_increment} minutes")
        else:
            print(f"    ⚠️  No session_increment set (will use 30 min default)")
else:
    print("\n❌ No active coaches found!")
    print("\n📝 To create a coach, run:")
    print("python manage.py shell")
    print("Then follow the instructions in COACHING_QUICKSTART.md")
