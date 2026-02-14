#!/usr/bin/env python3
"""
Debug the teams admin error
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from teams.models import Team
from teams.admin import TeamAdmin
from django.utils.html import format_html

def debug_teams_admin():
    """Debug the teams admin error"""
    print("🔍 Debugging Teams Admin Error")
    print("=" * 30)
    
    # Get a team to test with
    teams = Team.objects.all()[:3]
    
    if not teams.exists():
        print("❌ No teams found to test with")
        return
    
    print(f"Found {teams.count()} teams to test")
    
    # Create admin instance
    admin = TeamAdmin(Team, None)
    
    for team in teams:
        print(f"\n🔍 Testing team: {team.name}")
        
        try:
            # Test member_count_display
            member_display = admin.member_count_display(team)
            print(f"✅ member_count_display: {member_display}")
        except Exception as e:
            print(f"❌ member_count_display error: {e}")
        
        try:
            # Test status_badge
            status_badge = admin.status_badge(team)
            print(f"✅ status_badge: {status_badge}")
        except Exception as e:
            print(f"❌ status_badge error: {e}")
        
        try:
            # Test win_rate_display
            print(f"   win_rate value: {team.win_rate} (type: {type(team.win_rate)})")
            win_rate_display = admin.win_rate_display(team)
            print(f"✅ win_rate_display: {win_rate_display}")
        except Exception as e:
            print(f"❌ win_rate_display error: {e}")
            
            # Try to debug the specific issue
            try:
                win_rate = team.win_rate
                print(f"   Raw win_rate: {win_rate}")
                print(f"   Type: {type(win_rate)}")
                
                # Test the format_html call manually
                color = 'green' if win_rate >= 50 else 'orange' if win_rate >= 30 else 'red'
                print(f"   Color: {color}")
                
                # Try the format_html call
                result = format_html(
                    '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                    color, float(win_rate)
                )
                print(f"   Manual format_html result: {result}")
                
            except Exception as inner_e:
                print(f"   Inner error: {inner_e}")

if __name__ == '__main__':
    debug_teams_admin()