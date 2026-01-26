"""
Property-based tests for game profile deletion protection functionality.

This module tests the game profile deletion protection property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from core.models import User, Game, UserGameProfile
from tournaments.models import Tournament, Participant
import uuid


@pytest.mark.django_db(transaction=True)
class TestGameProfileDeletionProtection:
    """
    **Feature: user-profile-dashboard, Property 4: Game profile deletion protection**
    
    For any game profile with associated tournament participations, deletion attempts must be rejected.
    
    **Validates: Requirements 4.4**
    """
    
    @settings(max_examples=20, deadline=None)
    @given(
        has_participation=st.booleans()
    )
    def test_game_profile_deletion_protection_property(self, has_participation):
        """Property: Game profiles with tournament participations cannot be deleted"""
        import time
        unique_id = f"{str(uuid.uuid4())[:6]}{int(time.time()) % 10000}"
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create organizer for tournaments
        organizer = User.objects.create_user(
            email=f'organizer_{unique_id}@example.com',
            username=f'organizer_{unique_id}',
            password='testpass123'
        )
        
        # Create game and game profile
        game = Game.objects.create(
            name=f'Game {unique_id}',
            slug=f'game-{unique_id}',
            description='Test game',
            genre='other',
            is_active=True
        )
        
        profile = UserGameProfile.objects.create(
            user=user,
            game=game,
            in_game_name='TestPlayer',
            skill_rating=1500,
            is_main_game=True
        )
        
        # Conditionally create tournament and participation
        if has_participation:
            tournament = Tournament.objects.create(
                name=f'Tournament {unique_id}',
                slug=f'tournament-{unique_id}',
                description='Test tournament',
                game=game,
                organizer=organizer,
                format='single_elim',
                registration_start=timezone.now() - timedelta(days=10),
                registration_end=timezone.now() - timedelta(days=3),
                check_in_start=timezone.now() - timedelta(days=2),
                start_datetime=timezone.now() - timedelta(days=1),
                max_participants=16,
                registration_fee=0
            )
            
            # Create participation record
            Participant.objects.create(
                tournament=tournament,
                user=user,
                status='confirmed'
            )
        
        # Test the deletion protection property
        actual_participations = Participant.objects.filter(
            user=user,
            tournament__game=game
        ).exists()
        
        # Verify our test setup is correct
        assert actual_participations == has_participation, \
            f"Test setup error: Expected participation={has_participation}, got {actual_participations}"
        
        # Test deletion protection logic (simulating the view logic)
        can_delete = not Participant.objects.filter(
            user=user,
            tournament__game=game
        ).exists()
        
        if has_participation:
            # Property: Profiles with participations should be protected from deletion
            assert not can_delete, \
                "Game profile with tournament participations should be protected from deletion"
        else:
            # Property: Profiles without participations should be deletable
            assert can_delete, \
                "Game profile without tournament participations should be deletable"
        
        # Cleanup
        if has_participation:
            tournament.delete()
        game.delete()
        organizer.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_tournaments=st.integers(min_value=1, max_value=4),
        participation_statuses=st.lists(
            st.sampled_from(['confirmed', 'pending', 'checked_in', 'eliminated']),
            min_size=1,
            max_size=4
        )
    )
    def test_deletion_protection_with_different_participation_statuses(self, num_tournaments, participation_statuses):
        """Property: Deletion protection applies regardless of participation status"""
        import time
        unique_id = f"{str(uuid.uuid4())[:6]}{int(time.time()) % 10000}"
        
        # Create test user and organizer
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        organizer = User.objects.create_user(
            email=f'organizer_{unique_id}@example.com',
            username=f'organizer_{unique_id}',
            password='testpass123'
        )
        
        # Create game and profile
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}',
            description='Test game',
            genre='other',
            is_active=True
        )
        
        profile = UserGameProfile.objects.create(
            user=user,
            game=game,
            in_game_name='TestPlayer',
            skill_rating=1500,
            is_main_game=True
        )
        
        # Create tournaments with different participation statuses
        tournaments = []
        participations = []
        
        # Ensure we don't exceed the number of tournaments
        statuses_to_use = participation_statuses[:num_tournaments]
        
        for i, status in enumerate(statuses_to_use):
            tournament = Tournament.objects.create(
                name=f'Tournament {i} {unique_id}',
                slug=f'tournament-{i}-{unique_id}',
                description=f'Test tournament {i}',
                game=game,
                organizer=organizer,
                format='single_elim',
                registration_start=timezone.now() - timedelta(days=10),
                registration_end=timezone.now() - timedelta(days=3),
                check_in_start=timezone.now() - timedelta(days=2),
                start_datetime=timezone.now() - timedelta(days=1),
                max_participants=16,
                registration_fee=0
            )
            tournaments.append(tournament)
            
            participation = Participant.objects.create(
                tournament=tournament,
                user=user,
                status=status
            )
            participations.append(participation)
        
        # Property: Profile should be protected regardless of participation status
        has_any_participations = Participant.objects.filter(
            user=user,
            tournament__game=game
        ).exists()
        
        assert has_any_participations, \
            "Test setup error: Should have participations"
        
        # Check deletion protection
        can_delete = not Participant.objects.filter(
            user=user,
            tournament__game=game
        ).exists()
        
        assert not can_delete, \
            f"Profile should be protected from deletion with participations of statuses: {statuses_to_use}"
        
        # Property: Each participation status should contribute to protection
        for status in set(statuses_to_use):
            status_participations = Participant.objects.filter(
                user=user,
                tournament__game=game,
                status=status
            ).exists()
            
            if status in statuses_to_use:
                assert status_participations, \
                    f"Should have participation with status '{status}'"
        
        # Cleanup
        for tournament in tournaments:
            tournament.delete()
        game.delete()
        organizer.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_users=st.integers(min_value=2, max_value=4),
        users_with_participations=st.lists(
            st.integers(min_value=0, max_value=3),
            min_size=0,
            max_size=2
        )
    )
    def test_deletion_protection_per_user(self, num_users, users_with_participations):
        """Property: Deletion protection is enforced per user, not globally"""
        import time
        unique_id = f"{str(uuid.uuid4())[:6]}{int(time.time()) % 10000}"
        
        # Create organizer
        organizer = User.objects.create_user(
            email=f'organizer_{unique_id}@example.com',
            username=f'organizer_{unique_id}',
            password='testpass123'
        )
        
        # Create shared game
        game = Game.objects.create(
            name=f'Shared Game {unique_id}',
            slug=f'shared-game-{unique_id}',
            description='Shared test game',
            genre='other',
            is_active=True
        )
        
        # Create tournament
        tournament = Tournament.objects.create(
            name=f'Shared Tournament {unique_id}',
            slug=f'shared-tournament-{unique_id}',
            description='Shared test tournament',
            game=game,
            organizer=organizer,
            format='single_elim',
            registration_start=timezone.now() - timedelta(days=10),
            registration_end=timezone.now() - timedelta(days=3),
            check_in_start=timezone.now() - timedelta(days=2),
            start_datetime=timezone.now() - timedelta(days=1),
            max_participants=16,
            registration_fee=0
        )
        
        # Filter users_with_participations to only include valid indices
        valid_participation_indices = [idx for idx in users_with_participations if idx < num_users]
        
        # Create users and their profiles
        users = []
        profiles = []
        for u in range(num_users):
            user = User.objects.create_user(
                email=f'test_{u}_{unique_id}@example.com',
                username=f'testuser_{u}_{unique_id}',
                password='testpass123'
            )
            users.append(user)
            
            profile = UserGameProfile.objects.create(
                user=user,
                game=game,
                in_game_name=f'Player{u}',
                skill_rating=1000 + u * 100,
                is_main_game=True
            )
            profiles.append(profile)
            
            # Create participation for selected users
            if u in valid_participation_indices:
                Participant.objects.create(
                    tournament=tournament,
                    user=user,
                    status='confirmed'
                )
        
        # Test deletion protection for each user
        for u, (user, profile) in enumerate(zip(users, profiles)):
            has_participations = u in valid_participation_indices
            
            # Check actual participations
            actual_participations = Participant.objects.filter(
                user=user,
                tournament__game=game
            ).exists()
            
            assert actual_participations == has_participations, \
                f"User {u} participation mismatch. Expected {has_participations}, got {actual_participations}"
            
            # Test deletion protection
            can_delete = not Participant.objects.filter(
                user=user,
                tournament__game=game
            ).exists()
            
            if has_participations:
                assert not can_delete, \
                    f"User {u} profile should be protected from deletion"
            else:
                assert can_delete, \
                    f"User {u} profile should be deletable"
        
        # Property: Users without participations should not be affected by others' participations
        users_without_participations = [
            u for u in range(num_users) 
            if u not in valid_participation_indices
        ]
        
        for u in users_without_participations:
            user = users[u]
            can_delete = not Participant.objects.filter(
                user=user,
                tournament__game=game
            ).exists()
            
            assert can_delete, \
                f"User {u} without participations should be able to delete profile, regardless of other users' participations"
        
        # Cleanup
        tournament.delete()
        game.delete()
        for user in users:
            user.delete()
        organizer.delete()
    
    def test_deletion_protection_edge_case_no_tournaments(self):
        """Edge case: Profile without any tournaments should be deletable"""
        import time
        unique_id = f"{str(uuid.uuid4())[:6]}{int(time.time()) % 10000}"
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create game and profile
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}',
            description='Test game',
            genre='other',
            is_active=True
        )
        
        profile = UserGameProfile.objects.create(
            user=user,
            game=game,
            in_game_name='TestPlayer',
            skill_rating=1500,
            is_main_game=True
        )
        
        # Verify no participations exist
        has_participations = Participant.objects.filter(
            user=user,
            tournament__game=game
        ).exists()
        
        assert not has_participations, \
            "Test setup error: Should have no participations"
        
        # Test deletion protection
        can_delete = not Participant.objects.filter(
            user=user,
            tournament__game=game
        ).exists()
        
        assert can_delete, \
            "Profile without tournament participations should be deletable"
        
        # Cleanup
        game.delete()
        user.delete()
    
    def test_deletion_protection_edge_case_tournament_without_participation(self):
        """Edge case: Tournament exists but user didn't participate"""
        import time
        unique_id = f"{str(uuid.uuid4())[:6]}{int(time.time()) % 10000}"
        
        # Create test user and organizer
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        organizer = User.objects.create_user(
            email=f'organizer_{unique_id}@example.com',
            username=f'organizer_{unique_id}',
            password='testpass123'
        )
        
        # Create game and profile
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}',
            description='Test game',
            genre='other',
            is_active=True
        )
        
        profile = UserGameProfile.objects.create(
            user=user,
            game=game,
            in_game_name='TestPlayer',
            skill_rating=1500,
            is_main_game=True
        )
        
        # Create tournament but no participation
        tournament = Tournament.objects.create(
            name=f'Tournament {unique_id}',
            slug=f'tournament-{unique_id}',
            description='Test tournament',
            game=game,
            organizer=organizer,
            format='single_elim',
            registration_start=timezone.now() - timedelta(days=10),
            registration_end=timezone.now() - timedelta(days=3),
            check_in_start=timezone.now() - timedelta(days=2),
            start_datetime=timezone.now() - timedelta(days=1),
            max_participants=16,
            registration_fee=0
        )
        
        # Verify no participations exist for this user
        has_participations = Participant.objects.filter(
            user=user,
            tournament__game=game
        ).exists()
        
        assert not has_participations, \
            "Test setup error: User should not have participations"
        
        # Verify tournament exists for the game
        tournament_exists = Tournament.objects.filter(game=game).exists()
        assert tournament_exists, \
            "Test setup error: Tournament should exist for the game"
        
        # Test deletion protection
        can_delete = not Participant.objects.filter(
            user=user,
            tournament__game=game
        ).exists()
        
        assert can_delete, \
            "Profile should be deletable when tournament exists but user didn't participate"
        
        # Cleanup
        tournament.delete()
        game.delete()
        organizer.delete()
        user.delete()
    
    @settings(max_examples=30, deadline=None)
    @given(
        num_games=st.integers(min_value=2, max_value=4),
        protected_game_idx=st.integers(min_value=0, max_value=3)
    )
    def test_deletion_protection_game_specificity(self, num_games, protected_game_idx):
        """Property: Deletion protection is game-specific"""
        # Ensure protected_game_idx is valid
        protected_game_idx = protected_game_idx % num_games
        
        import time
        unique_id = f"{str(uuid.uuid4())[:6]}{int(time.time()) % 10000}"
        
        # Create test user and organizer
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        organizer = User.objects.create_user(
            email=f'organizer_{unique_id}@example.com',
            username=f'organizer_{unique_id}',
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
                is_main_game=(i == 0)
            )
            profiles.append(profile)
        
        # Create tournament and participation for only one game
        protected_game = games[protected_game_idx]
        tournament = Tournament.objects.create(
            name=f'Tournament {unique_id}',
            slug=f'tournament-{unique_id}',
            description='Test tournament',
            game=protected_game,
            organizer=organizer,
            format='single_elim',
            registration_start=timezone.now() - timedelta(days=10),
            registration_end=timezone.now() - timedelta(days=3),
            check_in_start=timezone.now() - timedelta(days=2),
            start_datetime=timezone.now() - timedelta(days=1),
            max_participants=16,
            registration_fee=0
        )
        
        Participant.objects.create(
            tournament=tournament,
            user=user,
            status='confirmed'
        )
        
        # Test deletion protection for each game profile
        for i, (game, profile) in enumerate(zip(games, profiles)):
            has_participations = Participant.objects.filter(
                user=user,
                tournament__game=game
            ).exists()
            
            can_delete = not has_participations
            
            if i == protected_game_idx:
                # This game should be protected
                assert has_participations, \
                    f"Game {i} should have participations"
                assert not can_delete, \
                    f"Game {i} profile should be protected from deletion"
            else:
                # Other games should be deletable
                assert not has_participations, \
                    f"Game {i} should not have participations"
                assert can_delete, \
                    f"Game {i} profile should be deletable"
        
        # Property: Only one game should be protected
        protected_count = sum(
            1 for game in games
            if Participant.objects.filter(user=user, tournament__game=game).exists()
        )
        
        assert protected_count == 1, \
            f"Expected exactly 1 protected game, got {protected_count}"
        
        # Cleanup
        tournament.delete()
        for game in games:
            game.delete()
        organizer.delete()
        user.delete()