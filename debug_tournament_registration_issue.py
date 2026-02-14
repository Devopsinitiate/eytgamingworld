#!/usr/bin/env python
"""
Debug script to identify tournament registration issues
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from tournaments.models import Tournament, Participant

User = get_user_model()

def debug_tournament_registration():
    print("🔍 DEBUGGING TOURNAMENT REGISTRATION ISSUES")
    print("=" * 60)
    
    # Get all tournaments
    tournaments = Tournament.objects.all().order_by('-created_at')
    
    if not tournaments.exists():
        print("❌ No tournaments found in database")
        return
    
    print(f"📊 Found {tournaments.count()} tournaments")
    print()
    
    # Check each tournament
    for tournament in tournaments[:5]:  # Check first 5 tournaments
        print(f"🎮 Tournament: {tournament.name}")
        print(f"   Slug: {tournament.slug}")
        print(f"   Status: {tournament.status}")
        print(f"   Is Public: {tournament.is_public}")
        print(f"   Max Participants: {tournament.max_participants}")
        print(f"   Total Registered: {tournament.total_registered}")
        print(f"   Registration Fee: ${tournament.registration_fee}")
        
        # Check dates
        now = timezone.now()
        print(f"   Current Time: {now}")
        print(f"   Registration Start: {tournament.registration_start}")
        print(f"   Registration End: {tournament.registration_end}")
        print(f"   Tournament Start: {tournament.start_datetime}")
        
        # Check if registration is theoretically open
        reg_start_ok = tournament.registration_start is None or now >= tournament.registration_start
        reg_end_ok = tournament.registration_end is None or now <= tournament.registration_end
        
        print(f"   Registration Start OK: {reg_start_ok}")
        print(f"   Registration End OK: {reg_end_ok}")
        print(f"   Is Full: {tournament.is_full}")
        
        # Test with a sample user
        users = User.objects.filter(is_active=True)
        if users.exists():
            user = users.first()
            can_register, message = tournament.can_user_register(user)
            print(f"   Can User Register: {can_register}")
            print(f"   Registration Message: {message}")
            
            # Check if user is already registered
            is_registered = Participant.objects.filter(tournament=tournament, user=user).exists()
            print(f"   User Already Registered: {is_registered}")
        else:
            print("   No users found to test registration")
        
        print()
    
    # Check for common issues
    print("🔧 COMMON ISSUES CHECK")
    print("=" * 30)
    
    # Issue 1: Tournaments in draft status
    draft_tournaments = tournaments.filter(status='draft')
    print(f"📝 Tournaments in 'draft' status: {draft_tournaments.count()}")
    if draft_tournaments.exists():
        print("   ⚠️  These tournaments need status changed to 'registration' to allow registration")
        for t in draft_tournaments[:3]:
            print(f"      - {t.name} (slug: {t.slug})")
    
    # Issue 2: Tournaments with no registration dates
    no_reg_dates = tournaments.filter(registration_start__isnull=True, registration_end__isnull=True)
    print(f"📅 Tournaments with no registration dates: {no_reg_dates.count()}")
    if no_reg_dates.exists():
        print("   ⚠️  These tournaments need registration dates set")
        for t in no_reg_dates[:3]:
            print(f"      - {t.name} (slug: {t.slug})")
    
    # Issue 3: Tournaments with past registration end dates
    past_reg_end = tournaments.filter(registration_end__lt=now)
    print(f"⏰ Tournaments with past registration end dates: {past_reg_end.count()}")
    if past_reg_end.exists():
        print("   ⚠️  These tournaments have closed registration")
        for t in past_reg_end[:3]:
            print(f"      - {t.name} (slug: {t.slug}) - ended {t.registration_end}")
    
    # Issue 4: Full tournaments
    from django.db import models
    full_tournaments = tournaments.filter(total_registered__gte=models.F('max_participants')).exclude(max_participants__isnull=True)
    print(f"🎯 Full tournaments: {full_tournaments.count()}")
    
    print()
    print("🛠️  RECOMMENDED FIXES")
    print("=" * 25)
    
    if draft_tournaments.exists():
        print("1. Change tournament status from 'draft' to 'registration':")
        print("   - Via Django admin: /admin/tournaments/tournament/")
        print("   - Or via management command")
        print()
    
    if no_reg_dates.exists():
        print("2. Set registration dates for tournaments:")
        print("   - registration_start: When registration opens")
        print("   - registration_end: When registration closes")
        print()
    
    print("3. Ensure tournaments are public (is_public=True) if they should be visible")
    print()
    
    # Generate fix script
    print("🔧 QUICK FIX SCRIPT")
    print("=" * 20)
    
    if draft_tournaments.exists():
        print("# Fix draft tournaments - run in Django shell:")
        print("from tournaments.models import Tournament")
        print("from django.utils import timezone")
        print()
        for t in draft_tournaments[:3]:
            print(f"# Fix {t.name}")
            print(f"t = Tournament.objects.get(slug='{t.slug}')")
            print("t.status = 'registration'")
            if not t.registration_start:
                print("t.registration_start = timezone.now()")
            if not t.registration_end:
                print("t.registration_end = timezone.now() + timezone.timedelta(days=7)")
            print("t.save()")
            print()

if __name__ == '__main__':
    debug_tournament_registration()