#!/usr/bin/env python3
"""
Simple test to verify JavaScript fixes
"""

import os

def test_files_exist():
    """Test that all required files exist"""
    print("🔍 Testing file existence...")
    
    files = [
        'static/js/sw.js',
        'static/js/modules/performance-optimizer.js',
        'static/js/tournament-detail.js'
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def test_service_worker():
    """Test service worker content"""
    print("\n🔍 Testing service worker...")
    
    try:
        with open('static/js/sw.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'CACHE_NAME' in content and 'addEventListener' in content:
            print("✅ Service worker has proper structure")
            return True
        else:
            print("❌ Service worker missing required content")
            return False
    except Exception as e:
        print(f"❌ Error reading service worker: {e}")
        return False

def test_performance_optimizer():
    """Test performance optimizer fixes"""
    print("\n🔍 Testing performance optimizer...")
    
    try:
        with open('static/js/modules/performance-optimizer.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'this.config.targetFPS * 0.5' in content:
            print("✅ FPS threshold fixed (50% instead of 80%)")
            return True
        else:
            print("❌ FPS threshold not fixed")
            return False
    except Exception as e:
        print(f"❌ Error reading performance optimizer: {e}")
        return False

def test_tournament_detail():
    """Test tournament detail fixes"""
    print("\n🔍 Testing tournament detail...")
    
    try:
        with open('static/js/tournament-detail.js', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if 'updateStatistics(data)' in content:
            print("✅ updateValues method fixed to updateStatistics")
            return True
        else:
            print("❌ updateValues method not fixed")
            return False
    except Exception as e:
        print(f"❌ Error reading tournament detail: {e}")
        return False

def main():
    """Run tests"""
    print("🧪 JavaScript Console Error Fixes - Simple Test")
    print("=" * 50)
    
    tests = [
        test_files_exist,
        test_service_worker,
        test_performance_optimizer,
        test_tournament_detail
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All JavaScript fixes verified!")
    else:
        print("⚠️  Some issues remain")

if __name__ == '__main__':
    main()