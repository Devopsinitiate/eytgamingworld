import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament

try:
    t = Tournament.objects.get(slug='kings-battle')
    print(f"Current Status: {t.status}")
    t.status = 'registration'
    t.save()
    print(f"New Status: {t.status}")
    print("Tournament updated successfully!")
    
except Tournament.DoesNotExist:
    print("Tournament not found")
except Exception as e:
    print(f"Error: {e}")
