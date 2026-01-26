#!/usr/bin/env python3
"""
Test script to verify JavaScript module loading fixes
"""

import requests
import re
from urllib.parse import urljoin

def test_module_loading():
    base_url = "http://127.0.0.1:8000"
    
    print("Testing JavaScript module loading fixes...")
    print("=" * 50)
    
    # Test 1: Check if static files are accessible
    modules_to_test = [
        "/static/js/modules/module-manager.js",
        "/static/js/modules/bracket-preview.js", 
        "/static/js/modules/live-updates.js",
        "/static/js/modules/social-sharing.js",
        "/static/js/modules/timeline-animations.js"
    ]
    
    print("1. Testing static file accessibility:")
    for module_path in modules_to_test:
        try:
            response = requests.get(urljoin(base_url, module_path), timeout=5)
            if response.status_code == 200:
                print(f"   ✓ {module_path} - OK ({len(response.content)} bytes)")
            else:
                print(f"   ✗ {module_path} - HTTP {response.status_code}")
        except requests.RequestException as e:
            print(f"   ✗ {module_path} - Error: {e}")
    
    print("\n2. Testing tournament detail page:")
    try:
        # Test with a known tournament
        tournament_url = f"{base_url}/tournaments/test-enhanced-hero/"
        response = requests.get(tournament_url, timeout=10)
        
        if response.status_code == 200:
            print(f"   ✓ Tournament page accessible - HTTP {response.status_code}")
            
            # Check for JavaScript errors in the HTML
            content = response.text
            
            # Look for script tags that might cause issues
            script_tags = re.findall(r'<script[^>]*src="([^"]*)"[^>]*>', content)
            print(f"   Found {len(script_tags)} script tags")
            
            # Check for ES6 export statements that would cause syntax errors
            problematic_patterns = [
                r'export\s+default',
                r'export\s+\{',
                r'import\s+.*from'
            ]
            
            issues_found = []
            for pattern in problematic_patterns:
                if re.search(pattern, content):
                    issues_found.append(pattern)
            
            if issues_found:
                print(f"   ⚠ Found potential ES6 module syntax in HTML: {issues_found}")
            else:
                print("   ✓ No ES6 module syntax found in HTML")
                
        else:
            print(f"   ✗ Tournament page - HTTP {response.status_code}")
            
    except requests.RequestException as e:
        print(f"   ✗ Tournament page - Error: {e}")
    
    print("\n3. Testing individual module syntax:")
    for module_path in modules_to_test:
        try:
            response = requests.get(urljoin(base_url, module_path), timeout=5)
            if response.status_code == 200:
                content = response.text
                
                # Check for ES6 export statements
                if re.search(r'export\s+default', content):
                    print(f"   ✗ {module_path} - Contains 'export default'")
                elif re.search(r'export\s+\{', content):
                    print(f"   ✗ {module_path} - Contains 'export {{'")
                else:
                    print(f"   ✓ {module_path} - No problematic exports")
                    
        except requests.RequestException:
            pass  # Already reported in test 1
    
    print("\n" + "=" * 50)
    print("Module loading test completed!")

if __name__ == "__main__":
    test_module_loading()