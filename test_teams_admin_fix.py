#!/usr/bin/env python3
"""
Test the teams admin fix by simulating admin list view
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from teams.models import Team
from teams.admin import TeamAdmin
from django.contrib.admin.sites import AdminSite

def test_teams_admin_fix():
    """Test the teams admin fix"""
    print("🧪 Testing Teams Admin Fix")
    print("=" * 25)
    
    # Create admin instance
    site = AdminSite()
    admin = TeamAdmin(Team, site)
    
    # Get teams
    teams = Team.objects.all()[:5]
    
    if not teams.exists():
        print("❌ No teams found to test with")
        return
    
    print(f"Testing with {teams.count()} teams")
    print()
    
    # Test all list_display methods
    list_display_methods = [
        'name',
        'tag', 
        'game',
        'captain',
        'member_count_display',
        'status_badge',
        'win_rate_display',
        'is_recruiting'
    ]
    
    success_count = 0
    total_tests = 0
    
    for team in teams:
        print(f"🔍 Testing team: {team.name}")
        
        for method_name in list_display_methods:
            total_tests += 1
            
            try:
                if hasattr(admin, method_name):
                    # It's a custom admin method
                    method = getattr(admin, method_name)
                    result = method(team)
                    print(f"  ✅ {method_name}: {result}")
                else:
                    # It's a model field/property
                    result = getattr(team, method_name)
                    print(f"  ✅ {method_name}: {result}")
                
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ {method_name}: ERROR - {e}")
        
        print()
    
    print("=" * 25)
    print(f"📊 Test Results: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 All admin display methods working correctly!")
        return True
    else:
        print("⚠️  Some methods still have issues")
        return False

if __name__ == '__main__':
    success = test_teams_admin_fix()
    sys.exit(0 if success else 1)