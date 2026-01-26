#!/usr/bin/env python
"""
Quick test script to verify ngrok configuration
Run this after starting ngrok to test the setup
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

def test_ngrok_config():
    """Test that ngrok configuration is properly set up"""
    
    print("=" * 60)
    print("NGROK CONFIGURATION TEST")
    print("=" * 60)
    
    # Check DEBUG mode
    print(f"\n✓ DEBUG Mode: {settings.DEBUG}")
    
    # Check ALLOWED_HOSTS
    print(f"\n✓ ALLOWED_HOSTS includes:")
    for host in settings.ALLOWED_HOSTS:
        print(f"  - {host}")
    
    # Check for ngrok domains
    ngrok_domains = ['.ngrok-free.app', '.ngrok.io', '.ngrok.app']
    ngrok_configured = any(domain in settings.ALLOWED_HOSTS for domain in ngrok_domains)
    
    if ngrok_configured:
        print("\n✅ ngrok domains are configured in ALLOWED_HOSTS")
    else:
        print("\n❌ ngrok domains NOT found in ALLOWED_HOSTS")
        return False
    
    # Check CSRF_TRUSTED_ORIGINS
    print(f"\n✓ CSRF_TRUSTED_ORIGINS includes:")
    for origin in settings.CSRF_TRUSTED_ORIGINS:
        print(f"  - {origin}")
    
    # Check for ngrok CSRF origins
    ngrok_csrf = any('ngrok' in origin for origin in settings.CSRF_TRUSTED_ORIGINS)
    
    if ngrok_csrf:
        print("\n✅ ngrok origins are configured in CSRF_TRUSTED_ORIGINS")
    else:
        print("\n❌ ngrok origins NOT found in CSRF_TRUSTED_ORIGINS")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL CHECKS PASSED - ngrok is properly configured!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Start ngrok: ngrok http 8000")
    print("3. Copy the ngrok HTTPS URL")
    print("4. Visit: https://your-ngrok-url.ngrok-free.app/tournaments/")
    print("\nSee NGROK_SETUP.md for detailed instructions.")
    
    return True

if __name__ == '__main__':
    try:
        success = test_ngrok_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
