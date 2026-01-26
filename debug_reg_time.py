import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament
from django.utils import timezone

try:
    t = Tournament.objects.get(slug='kings-battle')
    now = timezone.now()
    print(f"Tournament: {t.name}")
    print(f"Status: {t.status}")
    print(f"Registration Start: {t.registration_start}")
    print(f"Registration End: {t.registration_end}")
    print(f"Current Time: {now}")
    print(f"Registration Open: {t.is_registration_open}")
    print(f"Reg End Passed: {now > t.registration_end}")
    print(f"Time Until End: {t.registration_end - now}")
    
except Exception as e:
    print(f"Error: {e}")
