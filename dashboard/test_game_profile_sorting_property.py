"""
Property-based tests for game profile sorting functionality.

This module tests the game profile sorting property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.utils import timezone
from core.models import User, Game, UserGameProfile
import uuid


@pytest.mark.django_db
class TestGameProfileSorting:
    """
    **Feature: user-profile-dashboard, Property 7: Game profile sorting**
    
    For any list of game profiles, the main game must appear first, followed by other games 
    sorted by skill rating in descending order.
    
    **Validates: Requirements 4.5**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_games=st.integers(min_value=1, max_value=10),
        skill_ratings=st.lists(
            st.integers(min_value=0, max_value=5000), 
            min_size=1, 
            max_size=10
        ),
        main_game_index=st.integers(min_value=0, max_value=9)
    )
    def test_game_profile_sorting_property(self, num_games, skill_ratings, main_game_index):
        """Property: Game profiles are sorted by main game first, then skill rating descending"""
        # Ensure we have the right number of skill ratings
        skill_ratings = skill_ratings[:num_games]
        while len(skill_ratings) < num_games:
            skill_ratings.append(1000)  # Default skill rating
        
        # Ensure main_game_index is valid
        main_game_index = main_game_index % num_games
        
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
            
            is_main = (i == main_game_index)
            profile = UserGameProfile.objects.create(
                user=user,
                game=game,
                in_game_name=f'Player{i}',
                skill_rating=skill_ratings[i],
                is_main_game=is_main
            )
            profiles.append(profile)
        
        # Get sorted profiles using the same ordering as the view
        sorted_profiles = list(UserGameProfile.objects.filter(
            user=user
        ).order_by('-is_main_game', '-skill_rating'))
        
        # Property 1: Main game appears first
        if num_games > 0:
            first_profile = sorted_profiles[0]
            assert first_profile.is_main_game, \
                f"First profile should be the main game, but is_main_game={first_profile.is_main_game}"
            
            # Verify it's the correct main game
            assert first_profile.id == profiles[main_game_index].id, \
                f"First profile should be the main game (index {main_game_index}), but got different profile"
        
        # Property 2: All main games come before non-main games
        main_games_section = True
        for profile in sorted_profiles:
            if profile.is_main_game and not main_games_section:
                assert False, "Found main game after non-main games in sorted list"
            elif not profile.is_main_game:
                main_games_section = False
        
        # Property 3: Within each section (main/non-main), profiles are sorted by skill rating descending
        # Check main games section (should be only one main game)
        main_games = [p for p in sorted_profiles if p.is_main_game]
        assert len(main_games) <= 1, f"Expected at most 1 main game, got {len(main_games)}"
        
        # Check non-main games section
        non_main_games = [p for p in sorted_profiles if not p.is_main_game]
        for i in range(len(non_main_games) - 1):
            current_rating = non_main_games[i].skill_rating
            next_rating = non_main_games[i + 1].skill_rating
            assert current_rating >= next_rating, \
                f"Non-main games should be sorted by skill rating descending, but found {current_rating} before {next_rating}"
        
        # Property 4: All profiles are present in the sorted list
        assert len(sorted_profiles) == num_games, \
            f"Expected {num_games} profiles in sorted list, got {len(sorted_profiles)}"
        
        # Property 5: No duplicate profiles in the sorted list
        profile_ids = [p.id for p in sorted_profiles]
        assert len(profile_ids) == len(set(profile_ids)), \
            "Found duplicate profiles in sorted list"
        
        # Cleanup
        for game in games:
            game.delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_games=st.integers(min_value=2, max_value=8),
        skill_ratings=st.lists(
            st.integers(min_value=0, max_value=5000), 
            min_size=2, 
            max_size=8
        )
    )
    def test_game_profile_sorting_no_main_game(self, num_games, skill_ratings):
        """Property: When no main game is set, profiles are sorted by skill rating descending"""
        # Ensure we have the right number of skill ratings
        skill_ratings = skill_ratings[:num_games]
        while len(skill_ratings) < num_games:
            skill_ratings.append(1000)  # Default skill rating
        
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create games and profiles (no main game)
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
                skill_rating=skill_ratings[i],
                is_main_game=False  # No main game
            )
            profiles.append(profile)
        
        # Get sorted profiles
        sorted_profiles = list(UserGameProfile.objects.filter(
            user=user
        ).order_by('-is_main_game', '-skill_rating'))
        
        # Property 1: No main games
        for profile in sorted_profiles:
            assert not profile.is_main_game, \
                f"Expected no main games, but found profile with is_main_game=True"
        
        # Property 2: Profiles are sorted by skill rating descending
        for i in range(len(sorted_profiles) - 1):
            current_rating = sorted_profiles[i].skill_rating
            next_rating = sorted_profiles[i + 1].skill_rating
            assert current_rating >= next_rating, \
                f"Profiles should be sorted by skill rating descending, but found {current_rating} before {next_rating}"
        
        # Property 3: All profiles are present
        assert len(sorted_profiles) == num_games, \
            f"Expected {num_games} profiles in sorted list, got {len(sorted_profiles)}"
        
        # Cleanup
        for game in games:
            game.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_games=st.integers(min_value=3, max_value=6),
        main_game_skill=st.integers(min_value=0, max_value=5000),
        other_skills=st.lists(
            st.integers(min_value=0, max_value=5000), 
            min_size=2, 
            max_size=5
        )
    )
    def test_main_game_first_regardless_of_skill(self, num_games, main_game_skill, other_skills):
        """Property: Main game appears first even if it has lower skill rating than others"""
        # Ensure we have enough skill ratings for other games
        other_skills = other_skills[:num_games-1]
        while len(other_skills) < num_games - 1:
            other_skills.append(1000)
        
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
        
        # Create main game (first one)
        main_game = Game.objects.create(
            name=f'Main Game {unique_id}',
            slug=f'main-game-{unique_id}',
            description='Main test game',
            genre='other',
            is_active=True
        )
        games.append(main_game)
        
        main_profile = UserGameProfile.objects.create(
            user=user,
            game=main_game,
            in_game_name='MainPlayer',
            skill_rating=main_game_skill,
            is_main_game=True
        )
        profiles.append(main_profile)
        
        # Create other games with potentially higher skill ratings
        for i, skill in enumerate(other_skills):
            game = Game.objects.create(
                name=f'Game {i+1} {unique_id}',
                slug=f'game-{i+1}-{unique_id}',
                description=f'Test game {i+1}',
                genre='other',
                is_active=True
            )
            games.append(game)
            
            profile = UserGameProfile.objects.create(
                user=user,
                game=game,
                in_game_name=f'Player{i+1}',
                skill_rating=skill,
                is_main_game=False
            )
            profiles.append(profile)
        
        # Get sorted profiles
        sorted_profiles = list(UserGameProfile.objects.filter(
            user=user
        ).order_by('-is_main_game', '-skill_rating'))
        
        # Property 1: Main game is first regardless of skill rating
        first_profile = sorted_profiles[0]
        assert first_profile.is_main_game, \
            "First profile should be the main game"
        assert first_profile.id == main_profile.id, \
            "First profile should be the main game we created"
        
        # Property 2: Main game comes first even if others have higher skill ratings
        max_other_skill = max(other_skills) if other_skills else 0
        if main_game_skill < max_other_skill:
            # Main game has lower skill but should still be first
            assert sorted_profiles[0].skill_rating == main_game_skill, \
                f"Main game with skill {main_game_skill} should be first even though others have higher skills"
        
        # Property 3: Non-main games are sorted by skill rating descending
        non_main_profiles = sorted_profiles[1:]  # Skip the main game
        for i in range(len(non_main_profiles) - 1):
            current_rating = non_main_profiles[i].skill_rating
            next_rating = non_main_profiles[i + 1].skill_rating
            assert current_rating >= next_rating, \
                f"Non-main games should be sorted by skill rating descending, but found {current_rating} before {next_rating}"
        
        # Cleanup
        for game in games:
            game.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_games=st.integers(min_value=2, max_value=5),
        duplicate_skills=st.integers(min_value=1000, max_value=3000)
    )
    def test_sorting_with_duplicate_skill_ratings(self, num_games, duplicate_skills):
        """Property: Sorting works correctly when multiple profiles have the same skill rating"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create games and profiles with same skill rating
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
            
            # First profile is main, others are not
            is_main = (i == 0)
            profile = UserGameProfile.objects.create(
                user=user,
                game=game,
                in_game_name=f'Player{i}',
                skill_rating=duplicate_skills,  # Same skill for all
                is_main_game=is_main
            )
            profiles.append(profile)
        
        # Get sorted profiles
        sorted_profiles = list(UserGameProfile.objects.filter(
            user=user
        ).order_by('-is_main_game', '-skill_rating'))
        
        # Property 1: Main game is still first
        first_profile = sorted_profiles[0]
        assert first_profile.is_main_game, \
            "First profile should be the main game even with duplicate skill ratings"
        
        # Property 2: All profiles have the expected skill rating
        for profile in sorted_profiles:
            assert profile.skill_rating == duplicate_skills, \
                f"Expected skill rating {duplicate_skills}, got {profile.skill_rating}"
        
        # Property 3: Exactly one main game
        main_count = sum(1 for p in sorted_profiles if p.is_main_game)
        assert main_count == 1, \
            f"Expected exactly 1 main game, got {main_count}"
        
        # Property 4: All profiles are present
        assert len(sorted_profiles) == num_games, \
            f"Expected {num_games} profiles, got {len(sorted_profiles)}"
        
        # Cleanup
        for game in games:
            game.delete()
        user.delete()
    
    def test_sorting_edge_case_single_profile(self):
        """Edge case: Single profile should work correctly"""
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
            skill_rating=1500,
            is_main_game=True
        )
        
        # Get sorted profiles
        sorted_profiles = list(UserGameProfile.objects.filter(
            user=user
        ).order_by('-is_main_game', '-skill_rating'))
        
        # Property 1: Single profile is returned
        assert len(sorted_profiles) == 1, \
            f"Expected 1 profile, got {len(sorted_profiles)}"
        
        # Property 2: It's the correct profile
        assert sorted_profiles[0].id == profile.id, \
            "Returned profile should be the one we created"
        
        # Property 3: It's marked as main
        assert sorted_profiles[0].is_main_game, \
            "Single profile should be marked as main"
        
        # Cleanup
        game.delete()
        user.delete()
    
    def test_sorting_edge_case_no_profiles(self):
        """Edge case: User with no profiles should return empty list"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with no profiles
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Get sorted profiles
        sorted_profiles = list(UserGameProfile.objects.filter(
            user=user
        ).order_by('-is_main_game', '-skill_rating'))
        
        # Property: Empty list is returned
        assert len(sorted_profiles) == 0, \
            f"Expected 0 profiles for user with no game profiles, got {len(sorted_profiles)}"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_users=st.integers(min_value=2, max_value=4),
        games_per_user=st.integers(min_value=2, max_value=4)
    )
    def test_sorting_isolation_between_users(self, num_users, games_per_user):
        """Property: Sorting is isolated per user - one user's profiles don't affect another's"""
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
            
            # Create profiles for this user with different skill ratings
            for i, game in enumerate(shared_games):
                is_main = (i == 0)  # First game is main for each user
                skill_rating = 1000 + (u * 500) + (i * 100)  # Different skills per user
                UserGameProfile.objects.create(
                    user=user,
                    game=game,
                    in_game_name=f'Player{u}_{i}',
                    skill_rating=skill_rating,
                    is_main_game=is_main
                )
        
        # Test sorting for each user independently
        for user in users:
            sorted_profiles = list(UserGameProfile.objects.filter(
                user=user
            ).order_by('-is_main_game', '-skill_rating'))
            
            # Property 1: Correct number of profiles for this user
            assert len(sorted_profiles) == games_per_user, \
                f"User {user.username} should have {games_per_user} profiles, got {len(sorted_profiles)}"
            
            # Property 2: Main game is first
            assert sorted_profiles[0].is_main_game, \
                f"First profile for user {user.username} should be main game"
            
            # Property 3: Non-main games are sorted by skill rating descending
            non_main_profiles = sorted_profiles[1:]
            for i in range(len(non_main_profiles) - 1):
                current_rating = non_main_profiles[i].skill_rating
                next_rating = non_main_profiles[i + 1].skill_rating
                assert current_rating >= next_rating, \
                    f"User {user.username}: Non-main games should be sorted by skill descending, but found {current_rating} before {next_rating}"
            
            # Property 4: All profiles belong to this user
            for profile in sorted_profiles:
                assert profile.user.id == user.id, \
                    f"Found profile belonging to different user in {user.username}'s results"
        
        # Cleanup
        for game in shared_games:
            game.delete()
        for user in users:
            user.delete()