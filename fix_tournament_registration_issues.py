#!/usr/bin/env python
"""
Fix tournament registration issues
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from tournaments.models import Tournament

def fix_tournament_registration_issues():
    print("🔧 FIXING TOURNAMENT REGISTRATION ISSUES")
    print("=" * 50)
    
    # Fix 1: Change draft tournaments to registration status
    draft_tournaments = Tournament.objects.filter(status='draft')
    print(f"📝 Found {draft_tournaments.count()} tournaments in 'draft' status")
    
    for tournament in draft_tournaments:
        print(f"   Fixing: {tournament.name} (slug: {tournament.slug})")
        tournament.status = 'registration'
        
        # Set registration dates if missing
        now = timezone.now()
        if not tournament.registration_start:
            tournament.registration_start = now
            print(f"      Set registration_start to now")
        
        if not tournament.registration_end:
            # Set registration to end in 7 days
            tournament.registration_end = now + timedelta(days=7)
            print(f"      Set registration_end to 7 days from now")
        
        tournament.save()
        print(f"      ✅ Status changed to 'registration'")
    
    # Fix 2: Extend registration for tournaments with past end dates (optional)
    past_reg_tournaments = Tournament.objects.filter(
        status='registration',
        registration_end__lt=timezone.now()
    )
    
    print(f"\n⏰ Found {past_reg_tournaments.count()} tournaments with past registration end dates")
    
    # Only extend registration for recent tournaments (within last 7 days)
    recent_past = timezone.now() - timedelta(days=7)
    recent_tournaments = past_reg_tournaments.filter(registration_end__gte=recent_past)
    
    print(f"   {recent_tournaments.count()} tournaments ended recently (within 7 days)")
    
    for tournament in recent_tournaments:
        print(f"   Extending registration: {tournament.name} (slug: {tournament.slug})")
        # Extend registration by 24 hours
        tournament.registration_end = timezone.now() + timedelta(hours=24)
        tournament.save()
        print(f"      ✅ Registration extended by 24 hours")
    
    # Fix 3: Update tournaments with future start dates that are too far out
    future_start_tournaments = Tournament.objects.filter(
        status='registration',
        registration_start__gt=timezone.now() + timedelta(hours=1)
    )
    
    print(f"\n🔮 Found {future_start_tournaments.count()} tournaments with future registration start dates")
    
    for tournament in future_start_tournaments:
        # If registration starts more than 1 hour from now, move it to now
        if tournament.registration_start > timezone.now() + timedelta(hours=1):
            print(f"   Moving registration start: {tournament.name} (slug: {tournament.slug})")
            tournament.registration_start = timezone.now()
            tournament.save()
            print(f"      ✅ Registration start moved to now")
    
    print(f"\n✅ Tournament registration fixes completed!")
    
    # Show current status
    print(f"\n📊 CURRENT STATUS")
    print("=" * 20)
    
    registerable_tournaments = Tournament.objects.filter(
        status='registration',
        registration_start__lte=timezone.now(),
        registration_end__gte=timezone.now(),
        is_public=True
    )
    
    print(f"🎮 Tournaments available for registration: {registerable_tournaments.count()}")
    
    for tournament in registerable_tournaments[:5]:
        print(f"   - {tournament.name} (slug: {tournament.slug})")
        print(f"     Registration ends: {tournament.registration_end}")
        print(f"     Spots: {tournament.total_registered}/{tournament.max_participants}")

if __name__ == '__main__':
    fix_tournament_registration_issues()