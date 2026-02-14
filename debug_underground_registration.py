#!/usr/bin/env python
"""Debug script for Underground First tournament registration"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament
from django.utils import timezone

# Find the tournament
tournaments = Tournament.objects.filter(name__icontains='underground')
print(f"\nFound {tournaments.count()} tournament(s) matching 'underground':\n")

for t in tournaments:
    print(f"Tournament: {t.name}")
    print(f"  Slug: {t.slug}")
    print(f"  Status: {t.status}")
    print(f"  Is Public: {t.is_public}")
    print(f"  Registration Start: {t.registration_start}")
    print(f"  Registration End: {t.registration_end}")
    print(f"  Current Time: {timezone.now()}")
    print(f"  Max Participants: {t.max_participants}")
    print(f"  Total Registered: {t.total_registered}")
    print(f"  Is Full: {t.is_full if hasattr(t, 'is_full') else 'N/A'}")
    
    # Try to get can_register status
    try:
        from accounts.models import User
        # Get a test user
        user = User.objects.filter(is_superuser=False).first()
        if user:
            can_register, message = t.can_user_register(user)
            print(f"\n  Can user '{user.username}' register? {can_register}")
            print(f"  Message: {message}")
    except Exception as e:
        print(f"  Error checking registration: {e}")
    
    print("\n" + "="*80 + "\n")
