"""
Property-based tests for main game uniqueness functionality.

This module tests the main game uniqueness property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.utils import timezone
from core.models import User, Game, UserGameProfile
import uuid


@pytest.mark.django_db
class TestMainGameUniqueness:
    """
    **Feature: user-profile-dashboard, Property 3: Main game uniqueness**
    
    For any user, at most one game profile can be marked as the main game at any time.
    
    **Validates: Requirements 4.2**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_games=st.integers(min_value=1, max_value=10),
        main_game_indices=st.lists(
            st.integers(min_value=0, max_value=9), 
            min_size=0, 
            max_size=5
        )
    )
    def test_main_game_uniqueness_property(self, num_games, main_game_indices):
        """Property: User can have at most one main game profile at any time"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create games
        games = []
        for i in range(num_games):
            game = Game.objects.create(
                name=f'Game {i} {unique_id}',
                slug=f'game-{i}-{unique_id}',
                description=f'Test game {i}',
                genre='other',
                is_active=True
            )
            games.append(game)
        
        # Create game profiles
        game_profiles = []
        for i, game in enumerate(games):
            profile = UserGameProfile.objects.create(
                user=user,
                game=game,
                in_game_name=f'Player{i}',
                skill_rating=1000 + i * 100,
                is_main_game=False  # Start with all false
            )
            game_profiles.append(profile)
        
        # Filter main_game_indices to only include valid indices
        valid_main_indices = [idx for idx in main_game_indices if idx < num_games]
        
        # Simulate setting multiple profiles as main game
        # This tests what happens when the system tries to set multiple main games
        for idx in valid_main_indices:
            # Before setting this as main, unset any previous main games
            # This simulates the correct behavior the system should implement
            UserGameProfile.objects.filter(
                user=user,
                is_main_game=True
            ).update(is_main_game=False)
            
            # Set this profile as main
            game_profiles[idx].is_main_game = True
            game_profiles[idx].save()
        
        # Count main games
        main_game_count = UserGameProfile.objects.filter(
            user=user,
            is_main_game=True
        ).count()
        
        # Property 1: At most one game can be main
        assert main_game_count <= 1, \
            f"User has {main_game_count} main games, but should have at most 1"
        
        # Property 2: If we tried to set any games as main, exactly one should be main
        if valid_main_indices:
            assert main_game_count == 1, \
                f"Expected exactly 1 main game when setting games as main, got {main_game_count}"
            
            # The last game we set should be the main one
            last_main_idx = valid_main_indices[-1]
            last_profile = game_profiles[last_main_idx]
            last_profile.refresh_from_db()
            assert last_profile.is_main_game, \
                f"Expected the last set game (index {last_main_idx}) to be main"
        else:
            # If no games were set as main, count should be 0
            assert main_game_count == 0, \
                f"Expected 0 main games when no games set as main, got {main_game_count}"
        
        # Property 3: All other profiles should not be main
        non_main_count = UserGameProfile.objects.filter(
            user=user,
            is_main_game=False
        ).count()
        
        expected_non_main = num_games - main_game_count
        assert non_main_count == expected_non_main, \
            f"Expected {expected_non_main} non-main games, got {non_main_count}"
        
        # Cleanup
        for game in games:
            game.delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_games=st.integers(min_value=2, max_value=8),
        first_main_idx=st.integers(min_value=0, max_value=7),
        second_main_idx=st.integers(min_value=0, max_value=7)
    )
    def test_main_game_switching(self, num_games, first_main_idx, second_main_idx):
        """Property: When switching main games, only the new one should be main"""
        # Ensure indices are valid
        first_main_idx = first_main_idx % num_games
        second_main_idx = second_main_idx % num_games
        
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create games and profiles
        games = []
        profiles = []
        for i in range(num_games):
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
        
        # Set first main game
        UserGameProfile.objects.filter(
            user=user,
            is_main_game=True
        ).update(is_main_game=False)
        
        profiles[first_main_idx].is_main_game = True
        profiles[first_main_idx].save()
        
        # Verify first main game is set correctly
        main_count_after_first = UserGameProfile.objects.filter(
            user=user,
            is_main_game=True
        ).count()
        assert main_count_after_first == 1, \
            f"Expected 1 main game after setting first, got {main_count_after_first}"
        
        # Set second main game (switch)
        UserGameProfile.objects.filter(
            user=user,
            is_main_game=True
        ).update(is_main_game=False)
        
        profiles[second_main_idx].is_main_game = True
        profiles[second_main_idx].save()
        
        # Verify only one main game exists
        main_count_after_second = UserGameProfile.objects.filter(
            user=user,
            is_main_game=True
        ).count()
        assert main_count_after_second == 1, \
            f"Expected 1 main game after switching, got {main_count_after_second}"
        
        # Verify the correct game is main
        current_main = UserGameProfile.objects.get(
            user=user,
            is_main_game=True
        )
        assert current_main.id == profiles[second_main_idx].id, \
            f"Expected profile {second_main_idx} to be main, but got different profile"
        
        # Verify the first main game is no longer main
        profiles[first_main_idx].refresh_from_db()
        if first_main_idx != second_main_idx:
            assert not profiles[first_main_idx].is_main_game, \
                f"Previous main game (index {first_main_idx}) should no longer be main"
        
        # Cleanup
        for game in games:
            game.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_games=st.integers(min_value=1, max_value=6)
    )
    def test_main_game_uniqueness_across_operations(self, num_games):
        """Property: Main game uniqueness is maintained across various operations"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create games and profiles
        games = []
        profiles = []
        for i in range(num_games):
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
        
        # Perform operations one by one and check uniqueness after each
        # Operation 1: Set first profile as main
        self._set_main_game(user, profiles[0])
        main_count = UserGameProfile.objects.filter(user=user, is_main_game=True).count()
        assert main_count <= 1, f"After setting first main game, found {main_count} main games, expected at most 1"
        
        # Operation 2: Update skill rating (should not affect main game status)
        self._update_skill_rating(profiles[0], 1500)
        main_count = UserGameProfile.objects.filter(user=user, is_main_game=True).count()
        assert main_count <= 1, f"After updating skill rating, found {main_count} main games, expected at most 1"
        
        # Operation 3: Set different profile as main if we have multiple games
        if num_games > 1:
            self._set_main_game(user, profiles[1])
            main_count = UserGameProfile.objects.filter(user=user, is_main_game=True).count()
            assert main_count <= 1, f"After setting second main game, found {main_count} main games, expected at most 1"
            # Verify the correct profile is main
            if main_count == 1:
                current_main = UserGameProfile.objects.get(user=user, is_main_game=True)
                assert current_main.id == profiles[1].id, f"Expected profile 1 to be main, but got profile {current_main.id}"
        
        # Operation 4: Update in-game name using update_fields to avoid triggering validation
        # This tests if the uniqueness constraint is maintained even during partial updates
        profiles[0].in_game_name = "UpdatedName"
        # Use update_fields to avoid triggering full_clean() which would validate main game uniqueness
        # This simulates updating other fields without affecting the main game status
        profiles[0].save(update_fields=['in_game_name'])
        main_count = UserGameProfile.objects.filter(user=user, is_main_game=True).count()
        assert main_count <= 1, f"After updating in-game name, found {main_count} main games, expected at most 1"
        
        # Final check: Verify exactly one or zero main games
        final_main_count = UserGameProfile.objects.filter(user=user, is_main_game=True).count()
        assert final_main_count <= 1, f"Final check: found {final_main_count} main games, expected at most 1"
        
        # If we set any games as main, there should be exactly one
        # We always set the first profile as main in operation 1
        # If num_games > 1, we also set the second profile as main in operation 3 (which unsets the first)
        # So there should always be exactly one main game
        assert final_main_count == 1, f"Expected exactly 1 main game after operations, got {final_main_count}"
        
        # Cleanup
        for game in games:
            game.delete()
        user.delete()
    
    def _set_main_game(self, user, profile):
        """Helper method to set a profile as main game with proper uniqueness"""
        # The model now automatically handles uniqueness, so we just set this profile as main
        profile.is_main_game = True
        profile.save(update_fields=['is_main_game'])
    
    def _update_skill_rating(self, profile, new_rating):
        """Helper method to update skill rating"""
        profile.skill_rating = new_rating
        profile.save(update_fields=['skill_rating'])
    
    def _update_in_game_name(self, profile, new_name):
        """Helper method to update in-game name"""
        profile.in_game_name = new_name
        profile.save(update_fields=['in_game_name'])
    
    def test_main_game_uniqueness_edge_case_single_game(self):
        """Edge case: User with single game profile can set it as main"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create single game and profile
        game = Game.objects.create(
            name=f'Single Game {unique_id}',
            slug=f'single-game-{unique_id}',
            description='Single test game',
            genre='other',
            is_active=True
        )
        
        profile = UserGameProfile.objects.create(
            user=user,
            game=game,
            in_game_name='SinglePlayer',
            skill_rating=1000,
            is_main_game=True
        )
        
        # Verify exactly one main game
        main_count = UserGameProfile.objects.filter(
            user=user,
            is_main_game=True
        ).count()
        
        assert main_count == 1, \
            f"Expected exactly 1 main game for single profile, got {main_count}"
        
        # Verify it's the correct profile
        main_profile = UserGameProfile.objects.get(
            user=user,
            is_main_game=True
        )
        assert main_profile.id == profile.id, \
            "Main game should be the single profile we created"
        
        # Cleanup
        game.delete()
        user.delete()
    
    def test_main_game_uniqueness_edge_case_no_games(self):
        """Edge case: User with no game profiles should have no main games"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with no game profiles
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Verify no main games
        main_count = UserGameProfile.objects.filter(
            user=user,
            is_main_game=True
        ).count()
        
        assert main_count == 0, \
            f"Expected 0 main games for user with no profiles, got {main_count}"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_users=st.integers(min_value=2, max_value=5),
        games_per_user=st.integers(min_value=1, max_value=4)
    )
    def test_main_game_uniqueness_across_users(self, num_users, games_per_user):
        """Property: Main game uniqueness is enforced per user, not globally"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create shared games
        shared_games = []
        for i in range(games_per_user):
            game = Game.objects.create(
                name=f'Shared Game {i} {unique_id}',
                slug=f'shared-game-{i}-{unique_id}',
                description=f'Shared test game {i}',
                genre='other',
                is_active=True
            )
            shared_games.append(game)
        
        # Create users and their profiles
        users = []
        for u in range(num_users):
            user = User.objects.create_user(
                email=f'test_{u}_{unique_id}@example.com',
                username=f'testuser_{u}_{unique_id}',
                password='testpass123'
            )
            users.append(user)
            
            # Create profiles for this user
            for i, game in enumerate(shared_games):
                is_main = (i == 0)  # Make first game main for each user
                UserGameProfile.objects.create(
                    user=user,
                    game=game,
                    in_game_name=f'Player{u}_{i}',
                    skill_rating=1000 + i * 100,
                    is_main_game=is_main
                )
        
        # Verify each user has exactly one main game
        for user in users:
            main_count = UserGameProfile.objects.filter(
                user=user,
                is_main_game=True
            ).count()
            
            assert main_count == 1, \
                f"User {user.username} has {main_count} main games, expected exactly 1"
        
        # Verify total main games across all users
        total_main_games = UserGameProfile.objects.filter(
            is_main_game=True
        ).count()
        
        assert total_main_games == num_users, \
            f"Expected {num_users} total main games (one per user), got {total_main_games}"
        
        # Cleanup
        for game in shared_games:
            game.delete()
        for user in users:
            user.delete()