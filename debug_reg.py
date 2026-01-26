import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament

try:
    t = Tournament.objects.get(slug='kings-battle')
    print(f'Name: {t.name}')
    print(f'Status: {t.status}')
    print(f'Reg Start: {t.registration_start}')
    print(f'Reg End: {t.registration_end}')
    print(f'Now: {timezone.now()}')
    print(f'Is Reg Open: {t.is_registration_open}')
    
    # Also check simplified condition
    print(f'Condition (Status=reg): {t.status == "registration"}')
    print(f'Condition (Time): {t.registration_start <= timezone.now() <= t.registration_end}')
    print(f'Condition (Not Full): {t.total_registered < t.max_participants}')
    
except Tournament.DoesNotExist:
    print("Tournament not found")
except Exception as e:
    print(f"Error: {e}")
