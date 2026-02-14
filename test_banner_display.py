#!/usr/bin/env python
import os
import django
import requests
from django.test import Client
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament

# Get a tournament with a banner (not empty)
tournament = Tournament.objects.exclude(banner='').exclude(banner__isnull=True).first()

if tournament:
    print(f"Testing tournament: {tournament.name}")
    print(f"Slug: {tournament.slug}")
    print(f"Banner: {tournament.banner}")
    print(f"Banner URL: {tournament.banner.url}")
    
    # Test if the banner file exists
    import os
    from django.conf import settings
    banner_path = os.path.join(settings.MEDIA_ROOT, tournament.banner.name)
    print(f"Banner file exists: {os.path.exists(banner_path)}")
    print(f"Banner file path: {banner_path}")
    
    # Test the tournament detail page
    client = Client()
    response = client.get(f'/tournaments/{tournament.slug}/')
    print(f"Response status: {response.status_code}")
    
    # Check if banner URL is in the HTML
    html_content = response.content.decode('utf-8')
    banner_url = tournament.banner.url
    
    if banner_url in html_content:
        print(f"✓ Banner URL found in HTML: {banner_url}")
    else:
        print(f"✗ Banner URL NOT found in HTML: {banner_url}")
        
    # Check for the img tag
    if f'<img src="{banner_url}"' in html_content:
        print("✓ Banner img tag found in HTML")
    else:
        print("✗ Banner img tag NOT found in HTML")
        
    # Check for the tournament.banner condition
    if 'tournament.banner' in html_content:
        print("✓ Template condition 'tournament.banner' found")
    else:
        print("✗ Template condition 'tournament.banner' NOT found")
        
    # Look for the hero-background section
    if 'hero-background' in html_content:
        print("✓ Hero background section found")
        # Extract the hero-background section
        start_idx = html_content.find('<div class="hero-background absolute inset-0">')
        if start_idx != -1:
            end_idx = html_content.find('</div>', start_idx + 200)  # Look for closing div
            if end_idx != -1:
                hero_section = html_content[start_idx:end_idx + 6]
                print("Hero background section:")
                print(hero_section[:500] + "..." if len(hero_section) > 500 else hero_section)
    else:
        print("✗ Hero background section NOT found")
        
else:
    print("No tournaments with banners found!")