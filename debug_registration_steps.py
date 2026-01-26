#!/usr/bin/env python
"""
Debug script to test tournament registration step navigation
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client, override_settings
from django.contrib.auth import get_user_model
from tournaments.models import Tournament
from bs4 import BeautifulSoup

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_registration_steps():
    """Test the tournament registration step navigation"""
    client = Client()
    
    # Get a tournament
    tournament = Tournament.objects.first()
    if not tournament:
        print("No tournaments found in database")
        return
    
    print(f"Testing tournament: {tournament.name}")
    print(f"Tournament details:")
    print(f"  - Is team based: {tournament.is_team_based}")
    print(f"  - Registration fee: ${tournament.registration_fee}")
    print(f"  - Max participants: {tournament.max_participants}")
    print(f"  - Total registered: {tournament.total_registered}")
    print(f"  - Spots remaining: {tournament.spots_remaining}")
    
    # Create a test user
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Login the user
    client.force_login(user)
    
    # Test GET request to registration page
    url = f'/tournaments/{tournament.slug}/register/'
    print(f"\nTesting URL: {url}")
    
    try:
        response = client.get(url)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check step indicator
            steps = soup.find_all(class_='step')
            print(f"\nFound {len(steps)} steps:")
            for i, step in enumerate(steps, 1):
                step_number = step.find(class_='step-number')
                step_label = step.find(class_='step-label')
                print(f"  Step {i}: {step_label.text.strip() if step_label else 'No label'}")
            
            # Check step content sections
            step_contents = soup.find_all(class_='step-content')
            print(f"\nFound {len(step_contents)} step content sections:")
            for i, content_section in enumerate(step_contents, 1):
                data_step = content_section.get('data-step')
                is_active = 'active' in content_section.get('class', [])
                print(f"  Step {data_step}: {'Active' if is_active else 'Inactive'}")
                
                # Check if this is step 2 (Review)
                if data_step == '2':
                    print(f"    Checking Review step content...")
                    
                    # Check for registration summary
                    summary = content_section.find(class_='registration-summary')
                    if summary:
                        print(f"    ✅ Registration summary found")
                        
                        # Check summary fields
                        summary_fields = summary.find_all('p', class_='font-semibold')
                        print(f"    Found {len(summary_fields)} summary fields:")
                        for field in summary_fields:
                            print(f"      - {field.text.strip()}")
                    else:
                        print(f"    ❌ Registration summary not found")
                    
                    # Check for important information section
                    info_section = content_section.find(class_='bg-blue-900/20')
                    if info_section:
                        print(f"    ✅ Important information section found")
                    else:
                        print(f"    ❌ Important information section not found")
            
            # Check JavaScript variables
            if 'totalSteps' in content:
                print(f"\n✅ JavaScript totalSteps variable found")
            else:
                print(f"\n❌ JavaScript totalSteps variable not found")
            
            # Check for JavaScript functions
            js_functions = ['nextStep', 'prevStep', 'showStep', 'updateStepIndicator']
            for func in js_functions:
                if f'function {func}' in content:
                    print(f"✅ JavaScript function {func} found")
                else:
                    print(f"❌ JavaScript function {func} not found")
                    
        else:
            print(f"❌ Registration page failed to load: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error testing registration page: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_registration_steps()