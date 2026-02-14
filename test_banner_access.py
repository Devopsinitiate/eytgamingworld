#!/usr/bin/env python
import requests
import time

# Wait a moment for server to fully start
time.sleep(2)

# Test direct banner access
banner_url = "http://127.0.0.1:8000/media/tournaments/banners/mk_ban.jpg"
print(f"Testing banner URL: {banner_url}")

try:
    response = requests.get(banner_url, timeout=10)
    print(f"Banner response status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Banner image is accessible")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {response.headers.get('Content-Length')}")
    else:
        print(f"✗ Banner image not accessible: {response.status_code}")
        print(f"Response text: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error accessing banner: {e}")

# Test tournament page
tournament_url = "http://127.0.0.1:8000/tournaments/beast/"
print(f"\nTesting tournament page: {tournament_url}")

try:
    response = requests.get(tournament_url, timeout=10)
    print(f"Tournament page status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Tournament page is accessible")
        
        # Check if banner URL is in the HTML
        html_content = response.text
        banner_url_path = "/media/tournaments/banners/mk_ban.jpg"
        
        if banner_url_path in html_content:
            print(f"✓ Banner URL found in HTML: {banner_url_path}")
        else:
            print(f"✗ Banner URL NOT found in HTML: {banner_url_path}")
            
        # Check for the img tag
        if f'<img src="{banner_url_path}"' in html_content:
            print("✓ Banner img tag found in HTML")
        else:
            print("✗ Banner img tag NOT found in HTML")
            
        # Look for the hero-background section
        if 'hero-background' in html_content:
            print("✓ Hero background section found")
            # Extract the hero-background section
            start_idx = html_content.find('<div class="hero-background absolute inset-0">')
            if start_idx != -1:
                end_idx = html_content.find('</div>', start_idx + 500)  # Look for closing div
                if end_idx != -1:
                    hero_section = html_content[start_idx:end_idx + 6]
                    print("\nHero background section:")
                    print(hero_section)
        else:
            print("✗ Hero background section NOT found")
            
    else:
        print(f"✗ Tournament page not accessible: {response.status_code}")
        print(f"Response text: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error accessing tournament page: {e}")