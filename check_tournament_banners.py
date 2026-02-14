import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.models import Tournament

# Check if tournaments exist and have banners
tournaments = Tournament.objects.all()
print(f"Total tournaments: {tournaments.count()}")

if tournaments.exists():
    for tournament in tournaments:
        print(f"\nTournament: {tournament.name}")
        print(f"  Slug: {tournament.slug}")
        print(f"  Banner: {tournament.banner}")
        print(f"  Banner URL: {tournament.banner.url if tournament.banner else 'No banner'}")
        print(f"  Thumbnail: {tournament.thumbnail}")
        print(f"  Status: {tournament.status}")
else:
    print("No tournaments found!")