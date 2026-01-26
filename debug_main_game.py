#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Game, UserGameProfile
import uuid

def test_main_game_uniqueness_debug():
    """Debug the main game uniqueness issue"""
    unique_id = str(uuid.uuid4())[:8]
    
    # Create test user
    user = User.objects.create_user(
        email=f'test_{unique_id}@example.com',
        username=f'testuser_{unique_id}',
        password='testpass123'
    )
    
    # Create 2 games and profiles
    games = []
    profiles = []
    for i in range(2):
        game = Game.objects.create(
            name=f'Game {i} {unique_id}',
            slug=f'game-{i}-{unique_id}',
            description=f'Test game {i}',
            genre='other',
            is_active=True
        )
        games.append(game)
        
        profile = UserGameProfile.objects.create(
            user=user,
            game=game,
            in_game_name=f'Player{i}',
            skill_rating=1000 + i * 100,
            is_main_game=False
        )
        profiles.append(profile)
    
    print("Initial state:")
    for i, profile in enumerate(profiles):
        print(f"  Profile {i}: is_main_game={profile.is_main_game}")
    print(f"  Total main games: {UserGameProfile.objects.filter(user=user, is_main_game=True).count()}")
    
    # Operation 1: Set first profile as main
    print("\nOperation 1: Set profile 0 as main")
    profiles[0].is_main_game = True
    profiles[0].save(update_fields=['is_main_game'])
    
    for i, profile in enumerate(profiles):
        profile.refresh_from_db()
        print(f"  Profile {i}: is_main_game={profile.is_main_game}")
    print(f"  Total main games: {UserGameProfile.objects.filter(user=user, is_main_game=True).count()}")
    
    # Operation 2: Update skill rating
    print("\nOperation 2: Update profile 0 skill rating")
    profiles[0].skill_rating = 1500
    profiles[0].save(update_fields=['skill_rating'])
    
    for i, profile in enumerate(profiles):
        profile.refresh_from_db()
        print(f"  Profile {i}: is_main_game={profile.is_main_game}")
    print(f"  Total main games: {UserGameProfile.objects.filter(user=user, is_main_game=True).count()}")
    
    # Operation 3: Set second profile as main
    print("\nOperation 3: Set profile 1 as main")
    profiles[1].is_main_game = True
    profiles[1].save(update_fields=['is_main_game'])
    
    for i, profile in enumerate(profiles):
        profile.refresh_from_db()
        print(f"  Profile {i}: is_main_game={profile.is_main_game}")
    print(f"  Total main games: {UserGameProfile.objects.filter(user=user, is_main_game=True).count()}")
    
    # Operation 4: Update in-game name
    print("\nOperation 4: Update profile 0 in-game name")
    profiles[0].in_game_name = "UpdatedName"
    profiles[0].save(update_fields=['in_game_name'])
    
    for i, profile in enumerate(profiles):
        profile.refresh_from_db()
        print(f"  Profile {i}: is_main_game={profile.is_main_game}")
    print(f"  Total main games: {UserGameProfile.objects.filter(user=user, is_main_game=True).count()}")
    
    # Final check
    final_main_count = UserGameProfile.objects.filter(user=user, is_main_game=True).count()
    print(f"\nFinal result: {final_main_count} main games")
    
    # Cleanup
    try:
        for game in games:
            game.delete()
        user.delete()
        print("Cleanup successful")
    except Exception as e:
        print(f"Cleanup error: {e}")

if __name__ == "__main__":
    test_main_game_uniqueness_debug()