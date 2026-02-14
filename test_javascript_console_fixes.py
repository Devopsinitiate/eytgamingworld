#!/usr/bin/env python3
"""
Test script to verify JavaScript console error fixes
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament, Game

def test_javascript_files_exist():
    """Test that all required JavaScript files exist"""
    print("🔍 Testing JavaScript file existence...")
    
    js_files = [
        'static/js/sw.js',
        'static/js/modules/performance-optimizer.js',
        'static/js/modules/console-error-handler.js',
        'static/js/tournament-detail.js',
        'static/js/mobile-optimization.js'
    ]
    
    missing_files = []
    for js_file in js_files:
        if not os.path.exists(js_file):
            missing_files.append(js_file)
        else:
            print(f"✅ {js_file} exists")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All JavaScript files exist")
    return True

def test_service_worker_content():
    """Test that service worker has proper content"""
    print("\n🔍 Testing service worker content...")
    
    try:
        with open('static/js/sw.js', 'r') as f:
            content = f.read()
            
        required_content = [
            'CACHE_NAME',
            'addEventListener',
            'install',
            'activate',
            'fetch'
        ]
        
        missing_content = []
        for item in required_content:
            if item not in content:
                missing_content.append(item)
            else:
                print(f"✅ Service worker contains: {item}")
        
        if missing_content:
            print(f"❌ Service worker missing: {missing_content}")
            return False
            
        print("✅ Service worker has proper structure")
        return True
        
    except Exception as e:
        print(f"❌ Error reading service worker: {e}")
        return False

def test_performance_optimizer_fixes():
    """Test that performance optimizer has the fixes"""
    print("\n🔍 Testing performance optimizer fixes...")
    
    try:
        with open('static/js/modules/performance-optimizer.js', 'r') as f:
            content = f.read()
        
        # Check for the FPS threshold fix
        if 'this.config.targetFPS * 0.5' in content:
            print("✅ Performance optimizer FPS threshold fixed (50% instead of 80%)")
        else:
            print("❌ Performance optimizer FPS threshold not fixed")
            return False
            
        # Check for service worker registration improvement
        if 'registration => {' in content and 'console.log(\'Service worker registered successfully' in content:
            print("✅ Service worker registration improved with success logging")
        else:
            print("❌ Service worker registration not improved")
            return False
            
        print("✅ Performance optimizer fixes applied")
        return True
        
    except Exception as e:
        print(f"❌ Error reading performance optimizer: {e}")
        return False

def test_tournament_detail_fixes():
    """Test that tournament detail JS has the fixes"""
    print("\n🔍 Testing tournament detail fixes...")
    
    try:
        with open('static/js/tournament-detail.js', 'r') as f:
            content = f.read()
        
        # Check for the updateValues -> updateStatistics fix
        if 'updateStatistics(data)' in content and 'updateValues(data)' not in content:
            print("✅ Tournament detail updateValues method fixed")
        else:
            print("❌ Tournament detail updateValues method not fixed")
            return False
            
        # Check for StatisticsDashboard class
        if 'class StatisticsDashboard' in content:
            print("✅ StatisticsDashboard class exists")
        else:
            print("❌ StatisticsDashboard class missing")
            return False
            
        print("✅ Tournament detail fixes applied")
        return True
        
    except Exception as e:
        print(f"❌ Error reading tournament detail: {e}")
        return False

def test_tournament_page_loads():
    """Test that tournament detail page loads without errors"""
    print("\n🔍 Testing tournament page loading...")
    
    try:
        # Create test data
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        
        game, created = Game.objects.get_or_create(
            name='Test Game',
            defaults={'slug': 'test-game'}
        )
        
        tournament, created = Tournament.objects.get_or_create(
            name='Test Tournament',
            defaults={
                'slug': 'test-tournament',
                'game': game,
                'organizer': user,
                'status': 'registration',
                'max_participants': 32
            }
        )
        
        # Test page load
        client = Client()
        url = reverse('tournaments:tournament_detail', kwargs={'slug': tournament.slug})
        response = client.get(url)
        
        if response.status_code == 200:
            print(f"✅ Tournament page loads successfully (status: {response.status_code})")
            
            # Check for JavaScript includes
            content = response.content.decode()
            js_includes = [
                'performance-optimizer.js',
                'console-error-handler.js',
                'tournament-detail.js',
                'mobile-optimization.js'
            ]
            
            for js_file in js_includes:
                if js_file in content:
                    print(f"✅ {js_file} included in page")
                else:
                    print(f"❌ {js_file} not included in page")
                    return False
            
            return True
        else:
            print(f"❌ Tournament page failed to load (status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Error testing tournament page: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 JavaScript Console Error Fixes Test Suite")
    print("=" * 50)
    
    tests = [
        test_javascript_files_exist,
        test_service_worker_content,
        test_performance_optimizer_fixes,
        test_tournament_detail_fixes,
        test_tournament_page_loads
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All JavaScript console error fixes verified!")
        return True
    else:
        print("⚠️  Some tests failed - please review the issues above")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)