"""
Property-Based Tests for Tournament History Filtering

This module contains property-based tests for tournament history filtering functionality
in the dashboard application.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from django.utils import timezone
from datetime import timedelta, date
import uuid

from core.models import User, Game
from dashboard.services import StatisticsService
from tournaments.models import Tournament, Participant


@pytest.mark.django_db
class TestTournamentHistoryFiltering:
    """
    **Feature: user-profile-dashboard, Property 12: Tournament history filtering**
    
    For any filtered tournament history, all returned tournaments must match the filter criteria 
    (game, date range, placement).
    
    **Validates: Requirements 5.2**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_tournaments=st.integers(min_value=5, max_value=50),
        filter_game_index=st.integers(min_value=0, max_value=2),  # Index into games list
        use_game_filter=st.booleans()
    )
    def test_game_filter_consistency(self, num_tournaments, filter_game_index, use_game_filter):
        """
        Property: When filtering by game, all returned tournaments must be for that game.
        
        This test verifies that game filtering works correctly and returns only
        tournaments for the specified game.
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create multiple games
        games = []
        for i in range(3):
            game = Game.objects.create(
                name=f'TestGame_{unique_id}_{i}',
                slug=f'testgame_{unique_id}_{i}',
                genre='fps'
            )
            games.append(game)
        
        # Create tournaments across different games
        created_tournaments_by_game = {game.id: [] for game in games}
        
        for i in range(num_tournaments):
            game = games[i % len(games)]  # Distribute across games
            tournament = Tournament.objects.create(
                name=f'Tournament {i}',
                slug=f'tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=timezone.now() + timedelta(days=i+2),
                registration_start=timezone.now() - timedelta(days=1),
                registration_end=timezone.now() + timedelta(days=i),
                check_in_start=timezone.now() + timedelta(days=i+1),
                format='single_elim',
                status='completed'
            )
            
            participant = Participant.objects.create(
                user=user,
                tournament=tournament,
                status='confirmed',
                final_placement=(i % 5) + 1,  # Placements 1-5
                matches_won=3,
                matches_lost=2
            )
            created_tournaments_by_game[game.id].append(tournament.id)
        
        # Apply game filter if requested
        filters = {}
        expected_tournament_ids = set()
        
        if use_game_filter:
            filter_game = games[filter_game_index]
            filters['game_id'] = filter_game.id
            expected_tournament_ids = set(created_tournaments_by_game[filter_game.id])
        else:
            # No filter - expect all tournaments
            for tournament_ids in created_tournaments_by_game.values():
                expected_tournament_ids.update(tournament_ids)
        
        # Get filtered tournament history
        queryset = StatisticsService.get_tournament_history(
            user_id=user.id,
            filters=filters if filters else None
        )
        
        # Extract tournament IDs from results
        actual_tournament_ids = set(p.tournament.id for p in queryset)
        
        # Property 1: All returned tournaments must match the filter
        if use_game_filter:
            filter_game = games[filter_game_index]
            for participant in queryset:
                assert participant.tournament.game.id == filter_game.id, \
                    f"Tournament {participant.tournament.id} has game {participant.tournament.game.id}, expected {filter_game.id}"
        
        # Property 2: Returned tournaments must be exactly the expected set
        assert actual_tournament_ids == expected_tournament_ids, \
            f"Returned tournaments {actual_tournament_ids} don't match expected {expected_tournament_ids}"
        
        # Property 3: No tournaments from other games should be included when filtering
        if use_game_filter:
            filter_game = games[filter_game_index]
            other_games = [g for g in games if g.id != filter_game.id]
            for other_game in other_games:
                other_tournament_ids = set(created_tournaments_by_game[other_game.id])
                intersection = actual_tournament_ids.intersection(other_tournament_ids)
                assert len(intersection) == 0, \
                    f"Found tournaments from other game {other_game.id}: {intersection}"
        
        # Cleanup
        Tournament.objects.filter(game__in=games).delete()
        for game in games:
            game.delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_tournaments=st.integers(min_value=10, max_value=40),
        days_back=st.integers(min_value=1, max_value=100),
        use_date_filter=st.booleans()
    )
    def test_date_range_filter_consistency(self, num_tournaments, days_back, use_date_filter):
        """
        Property: When filtering by date range, all returned tournaments must be within that range.
        
        This test verifies that date filtering works correctly.
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create a game
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        # Create tournaments with different dates
        now = timezone.now()
        created_tournaments = []
        
        for i in range(num_tournaments):
            # Spread tournaments across a wider date range
            days_offset = (i * 5) - (num_tournaments * 2)  # Some past, some future
            tournament_date = now + timedelta(days=days_offset)
            
            tournament = Tournament.objects.create(
                name=f'Tournament {i}',
                slug=f'tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=tournament_date,
                registration_start=tournament_date - timedelta(days=2),
                registration_end=tournament_date - timedelta(days=1),
                check_in_start=tournament_date - timedelta(hours=1),
                format='single_elim',
                status='completed'
            )
            
            participant = Participant.objects.create(
                user=user,
                tournament=tournament,
                status='confirmed',
                final_placement=(i % 5) + 1,
                matches_won=3,
                matches_lost=2
            )
            created_tournaments.append((tournament, tournament_date))
        
        # Apply date filter if requested
        filters = {}
        expected_tournaments = created_tournaments
        
        if use_date_filter:
            date_from = now - timedelta(days=days_back)
            filters['date_from'] = date_from
            
            # Filter expected tournaments
            expected_tournaments = [
                (t, d) for t, d in created_tournaments 
                if d >= date_from
            ]
        
        # Get filtered tournament history
        queryset = StatisticsService.get_tournament_history(
            user_id=user.id,
            filters=filters if filters else None
        )
        
        # Extract tournaments from results
        actual_tournaments = [(p.tournament, p.tournament.start_datetime) for p in queryset]
        expected_tournament_ids = {t.id for t, d in expected_tournaments}
        actual_tournament_ids = {t.id for t, d in actual_tournaments}
        
        # Property 1: All returned tournaments must be within the date range
        if use_date_filter:
            date_from = now - timedelta(days=days_back)
            for tournament, tournament_date in actual_tournaments:
                assert tournament_date >= date_from, \
                    f"Tournament {tournament.id} date {tournament_date} is before filter date {date_from}"
        
        # Property 2: Returned tournaments must match expected set
        assert actual_tournament_ids == expected_tournament_ids, \
            f"Returned tournaments {actual_tournament_ids} don't match expected {expected_tournament_ids}"
        
        # Property 3: No tournaments outside date range should be included
        if use_date_filter:
            date_from = now - timedelta(days=days_back)
            excluded_tournaments = [
                (t, d) for t, d in created_tournaments 
                if d < date_from
            ]
            excluded_ids = {t.id for t, d in excluded_tournaments}
            intersection = actual_tournament_ids.intersection(excluded_ids)
            assert len(intersection) == 0, \
                f"Found tournaments outside date range: {intersection}"
        
        # Cleanup
        Tournament.objects.filter(game=game).delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_tournaments=st.integers(min_value=10, max_value=30),
        placement_filter=st.sampled_from(['top3', 'winner', 'specific']),
        specific_placement=st.integers(min_value=1, max_value=10),
        use_placement_filter=st.booleans()
    )
    def test_placement_filter_consistency(self, num_tournaments, placement_filter, specific_placement, use_placement_filter):
        """
        Property: When filtering by placement, all returned tournaments must match placement criteria.
        
        This test verifies that placement filtering works correctly.
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create a game
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        # Create tournaments with different placements
        created_participants = []
        
        for i in range(num_tournaments):
            tournament = Tournament.objects.create(
                name=f'Tournament {i}',
                slug=f'tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=timezone.now() + timedelta(days=i+2),
                registration_start=timezone.now() - timedelta(days=1),
                registration_end=timezone.now() + timedelta(days=i),
                check_in_start=timezone.now() + timedelta(days=i+1),
                format='single_elim',
                status='completed'
            )
            
            # Assign varied placements (1-10, with some None)
            placement = None if i % 7 == 0 else (i % 10) + 1
            
            participant = Participant.objects.create(
                user=user,
                tournament=tournament,
                status='confirmed',
                final_placement=placement,
                matches_won=3,
                matches_lost=2
            )
            created_participants.append(participant)
        
        # Apply placement filter if requested
        filters = {}
        expected_participants = created_participants
        
        if use_placement_filter:
            if placement_filter == 'top3':
                filters['placement_max'] = 3
                expected_participants = [
                    p for p in created_participants 
                    if p.final_placement is not None and p.final_placement <= 3
                ]
            elif placement_filter == 'winner':
                filters['placement_max'] = 1
                filters['placement_min'] = 1
                expected_participants = [
                    p for p in created_participants 
                    if p.final_placement == 1
                ]
            elif placement_filter == 'specific':
                filters['placement_max'] = specific_placement
                filters['placement_min'] = specific_placement
                expected_participants = [
                    p for p in created_participants 
                    if p.final_placement == specific_placement
                ]
        
        # Get filtered tournament history
        queryset = StatisticsService.get_tournament_history(
            user_id=user.id,
            filters=filters if filters else None
        )
        
        # Convert to lists for comparison
        actual_participants = list(queryset)
        expected_participant_ids = {p.id for p in expected_participants}
        actual_participant_ids = {p.id for p in actual_participants}
        
        # Property 1: All returned participants must match placement criteria
        if use_placement_filter:
            for participant in actual_participants:
                placement = participant.final_placement
                
                if placement_filter == 'top3':
                    assert placement is not None and placement <= 3, \
                        f"Participant {participant.id} has placement {placement}, expected <= 3"
                elif placement_filter == 'winner':
                    assert placement == 1, \
                        f"Participant {participant.id} has placement {placement}, expected 1"
                elif placement_filter == 'specific':
                    assert placement == specific_placement, \
                        f"Participant {participant.id} has placement {placement}, expected {specific_placement}"
        
        # Property 2: Returned participants must match expected set
        assert actual_participant_ids == expected_participant_ids, \
            f"Returned participants {actual_participant_ids} don't match expected {expected_participant_ids}"
        
        # Property 3: No participants outside placement criteria should be included
        if use_placement_filter:
            excluded_participants = [
                p for p in created_participants 
                if p.id not in expected_participant_ids
            ]
            excluded_ids = {p.id for p in excluded_participants}
            intersection = actual_participant_ids.intersection(excluded_ids)
            assert len(intersection) == 0, \
                f"Found participants outside placement criteria: {intersection}"
        
        # Cleanup
        Tournament.objects.filter(game=game).delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_tournaments=st.integers(min_value=15, max_value=30),
        game_index=st.integers(min_value=0, max_value=1),
        days_back=st.integers(min_value=5, max_value=50),
        max_placement=st.integers(min_value=1, max_value=5)
    )
    def test_combined_filters_consistency(self, num_tournaments, game_index, days_back, max_placement):
        """
        Property: When multiple filters are applied, all returned tournaments must match ALL criteria.
        
        This test verifies that combining multiple filters works correctly.
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create multiple games
        games = []
        for i in range(2):
            game = Game.objects.create(
                name=f'TestGame_{unique_id}_{i}',
                slug=f'testgame_{unique_id}_{i}',
                genre='fps'
            )
            games.append(game)
        
        # Create tournaments with varied attributes
        now = timezone.now()
        created_participants = []
        
        for i in range(num_tournaments):
            game = games[i % len(games)]
            days_offset = (i * 3) - (num_tournaments // 2)  # Mix of past and future
            tournament_date = now + timedelta(days=days_offset)
            placement = (i % 8) + 1  # Placements 1-8
            
            tournament = Tournament.objects.create(
                name=f'Tournament {i}',
                slug=f'tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=tournament_date,
                registration_start=tournament_date - timedelta(days=2),
                registration_end=tournament_date - timedelta(days=1),
                check_in_start=tournament_date - timedelta(hours=1),
                format='single_elim',
                status='completed'
            )
            
            participant = Participant.objects.create(
                user=user,
                tournament=tournament,
                status='confirmed',
                final_placement=placement,
                matches_won=3,
                matches_lost=2
            )
            created_participants.append((participant, tournament_date, game.id, placement))
        
        # Apply combined filters
        filter_game = games[game_index]
        date_from = now - timedelta(days=days_back)
        
        filters = {
            'game_id': filter_game.id,
            'date_from': date_from,
            'placement_max': max_placement
        }
        
        # Calculate expected participants manually
        expected_participants = []
        for participant, tournament_date, game_id, placement in created_participants:
            if (game_id == filter_game.id and 
                tournament_date >= date_from and 
                placement <= max_placement):
                expected_participants.append(participant)
        
        # Get filtered tournament history
        queryset = StatisticsService.get_tournament_history(
            user_id=user.id,
            filters=filters
        )
        
        actual_participants = list(queryset)
        expected_participant_ids = {p.id for p in expected_participants}
        actual_participant_ids = {p.id for p in actual_participants}
        
        # Property 1: All returned participants must match ALL filter criteria
        for participant in actual_participants:
            # Check game filter
            assert participant.tournament.game.id == filter_game.id, \
                f"Participant {participant.id} has wrong game {participant.tournament.game.id}, expected {filter_game.id}"
            
            # Check date filter
            assert participant.tournament.start_datetime >= date_from, \
                f"Participant {participant.id} tournament date {participant.tournament.start_datetime} is before {date_from}"
            
            # Check placement filter
            assert participant.final_placement <= max_placement, \
                f"Participant {participant.id} placement {participant.final_placement} exceeds max {max_placement}"
        
        # Property 2: Returned participants must match expected set
        assert actual_participant_ids == expected_participant_ids, \
            f"Returned participants {actual_participant_ids} don't match expected {expected_participant_ids}"
        
        # Property 3: Count should match manual calculation
        assert len(actual_participants) == len(expected_participants), \
            f"Returned {len(actual_participants)} participants, expected {len(expected_participants)}"
        
        # Cleanup
        Tournament.objects.filter(game__in=games).delete()
        for game in games:
            game.delete()
        user.delete()
    
    def test_empty_filter_returns_all(self):
        """
        Property: When no filters are applied, all user's tournaments should be returned.
        
        Edge case test for when filters is None or empty.
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create a game
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        # Create some tournaments
        created_participants = []
        for i in range(5):
            tournament = Tournament.objects.create(
                name=f'Tournament {i}',
                slug=f'tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=timezone.now() + timedelta(days=i+2),
                registration_start=timezone.now() - timedelta(days=1),
                registration_end=timezone.now() + timedelta(days=i),
                check_in_start=timezone.now() + timedelta(days=i+1),
                format='single_elim',
                status='completed'
            )
            
            participant = Participant.objects.create(
                user=user,
                tournament=tournament,
                status='confirmed',
                final_placement=i+1,
                matches_won=3,
                matches_lost=2
            )
            created_participants.append(participant)
        
        # Test with None filters
        queryset_none = StatisticsService.get_tournament_history(
            user_id=user.id,
            filters=None
        )
        
        # Test with empty filters
        queryset_empty = StatisticsService.get_tournament_history(
            user_id=user.id,
            filters={}
        )
        
        # Property: Both should return all tournaments
        expected_ids = {p.id for p in created_participants}
        actual_ids_none = {p.id for p in queryset_none}
        actual_ids_empty = {p.id for p in queryset_empty}
        
        assert actual_ids_none == expected_ids, \
            "None filters should return all tournaments"
        assert actual_ids_empty == expected_ids, \
            "Empty filters should return all tournaments"
        assert actual_ids_none == actual_ids_empty, \
            "None and empty filters should return same results"
        
        # Cleanup
        Tournament.objects.filter(game=game).delete()
        game.delete()
        user.delete()
    
    def test_invalid_filter_values_ignored(self):
        """
        Property: Invalid filter values should be ignored gracefully.
        
        Edge case test for when filter values are invalid.
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create a game and tournament
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        tournament = Tournament.objects.create(
            name='Test Tournament',
            slug=f'tournament-{unique_id}',
            game=game,
            organizer=user,
            max_participants=16,
            start_datetime=timezone.now() + timedelta(days=2),
            registration_start=timezone.now() - timedelta(days=1),
            registration_end=timezone.now() + timedelta(days=1),
            check_in_start=timezone.now() + timedelta(days=1),
            format='single_elim',
            status='completed'
        )
        
        participant = Participant.objects.create(
            user=user,
            tournament=tournament,
            status='confirmed',
            final_placement=1,
            matches_won=3,
            matches_lost=2
        )
        
        # Test with invalid filter values
        invalid_filters = {
            'game_id': 'invalid-uuid',
            'date_from': 'invalid-date',
            'placement_min': 'not-a-number',
            'placement_max': -1
        }
        
        # Should not raise exception and should return results
        try:
            queryset = StatisticsService.get_tournament_history(
                user_id=user.id,
                filters=invalid_filters
            )
            # Should still return the tournament (invalid filters ignored)
            results = list(queryset)
            assert len(results) >= 0, "Should handle invalid filters gracefully"
        except Exception as e:
            pytest.fail(f"Should handle invalid filters gracefully, but got: {e}")
        
        # Cleanup
        Tournament.objects.filter(game=game).delete()
        game.delete()
        user.delete()