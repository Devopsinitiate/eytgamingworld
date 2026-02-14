#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.urls import reverse
import traceback

def test_tournament_page():
    client = Client()
    try:
        # Test the tournaments page
        response = client.get('/tournaments/', HTTP_HOST='127.0.0.1:8000')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 500:
            print("500 Error occurred")
            # Try to get more details
            print("Response content:", response.content.decode('utf-8')[:1000])
        elif response.status_code == 200:
            print("Success! Page loaded correctly")
        else:
            print(f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_tournament_page()