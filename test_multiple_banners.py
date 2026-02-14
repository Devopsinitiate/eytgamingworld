#!/usr/bin/env python
import requests
import time

# Test multiple tournaments with banners
tournaments_to_test = [
    ("beast", "Serfast", "/media/tournaments/banners/mk_ban.jpg"),
    ("Battle", "Battle Hub", "/media/tournaments/banners/Mk1.jpg"),
    ("underfist", "underground Fight", "/media/tournaments/banners/banner_EuHm4SM.jpg"),
    ("test-enhanced-hero", "Enhanced Hero Test Tournament", "/media/tournaments/banners/Sf_BO4YSaj.jpg"),
]

for slug, name, expected_banner in tournaments_to_test:
    print(f"\n{'='*60}")
    print(f"Testing: {name} (slug: {slug})")
    print(f"Expected banner: {expected_banner}")
    
    # Test tournament page
    tournament_url = f"http://127.0.0.1:8000/tournaments/{slug}/"
    
    try:
        response = requests.get(tournament_url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check if banner URL is in the HTML
            if expected_banner in html_content:
                print(f"✅ Banner URL found in HTML")
            else:
                print(f"❌ Banner URL NOT found in HTML")
                
            # Check for the img tag
            if f'<img src="{expected_banner}"' in html_content:
                print("✅ Banner img tag found in HTML")
            else:
                print("❌ Banner img tag NOT found in HTML")
                
            # Test direct banner access
            banner_url = f"http://127.0.0.1:8000{expected_banner}"
            banner_response = requests.get(banner_url, timeout=5)
            if banner_response.status_code == 200:
                print(f"✅ Banner image accessible (Content-Type: {banner_response.headers.get('Content-Type')})")
            else:
                print(f"❌ Banner image not accessible: {banner_response.status_code}")
                
        else:
            print(f"❌ Tournament page not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n{'='*60}")
print("Banner display test completed!")