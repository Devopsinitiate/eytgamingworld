import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament
from tournaments.cache_utils import TournamentCache

print("=" * 60)
print("CLEARING TOURNAMENT CACHE")
print("=" * 60)

# Get all tournaments
tournaments = Tournament.objects.all()

print(f"\nFound {tournaments.count()} tournaments")

for tournament in tournaments:
    print(f"\nClearing cache for: {tournament.name}")
    
    # Clear tournament stats cache
    TournamentCache.invalidate_tournament_cache(tournament.id)
    
    print(f"  ✅ Cache cleared for tournament ID: {tournament.id}")

print("\n" + "=" * 60)
print("CACHE CLEARING COMPLETE")
print("=" * 60)
print("\n⚠️  Please restart your Django development server for changes to take effect!")
