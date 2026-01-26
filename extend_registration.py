import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament
from django.utils import timezone

try:
    t = Tournament.objects.get(slug='kings-battle')
    now = timezone.now()
    
    # Extend registration end by 24 hours from now
    t.registration_end = now + timedelta(hours=24)
    t.save()
    
    print(f"Tournament: {t.name}")
    print(f"Registration End Updated To: {t.registration_end}")
    print(f"Registration is now open for 24 hours")
    
except Exception as e:
    print(f"Error: {e}")
