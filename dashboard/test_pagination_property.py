"""
Property-Based Tests for Pagination Consistency

This module contains property-based tests for pagination functionality
in the dashboard application, specifically for activity feed and tournament history.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from django.utils import timezone
from datetime import timedelta
import uuid

from core.models import User, Game
from dashboard.models import Activity
from dashboard.services import ActivityService, StatisticsService
from tournaments.models import Tournament, Participant


@pytest.mark.django_db
class TestPaginationConsistency:
    """
    **Feature: user-profile-dashboard, Property 11: Pagination consistency**
    
    For any paginated list (tournament history with 20 per page, activity feed with 25 per page), 
    the total number of items across all pages must equal the total count, and no items must be 
    duplicated or missing.
    
    **Validates: Requirements 5.5, 8.5**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_activities=st.integers(min_value=0, max_value=200),
        page_size=st.integers(min_value=1, max_value=50)
    )
    def test_activity_feed_pagination_consistency(self, num_activities, page_size):
        """
        Property: All activities are present exactly once across all pages.
        
        This test verifies that:
        1. Total items across all pages equals total count
        2. No items are duplicated across pages
        3. No items are missing
        4. Page boundaries are correct
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create activities for this user
        created_activity_ids = []
        for i in range(num_activities):
            activity = Activity.objects.create(
                user=user,
                activity_type='profile_updated',
                data={'test_index': i}
            )
            created_activity_ids.append(activity.id)
        
        # Collect all activities across all pages
        collected_activity_ids = []
        page = 1
        total_count_from_service = None
        total_pages_from_service = None
        
        while True:
            # Get page of activities
            result = ActivityService.get_activity_feed(
                user_id=user.id,
                filters=None,
                page=page,
                page_size=page_size
            )
            
            # Store total count from first page
            if page == 1:
                total_count_from_service = result['total_count']
                total_pages_from_service = result['total_pages']
            
            # Collect activity IDs from this page
            page_activity_ids = [activity.id for activity in result['activities']]
            collected_activity_ids.extend(page_activity_ids)
            
            # Property: Page size should not exceed requested page_size
            assert len(page_activity_ids) <= page_size, \
                f"Page {page} has {len(page_activity_ids)} items, exceeds page_size {page_size}"
            
            # Property: Last page can be smaller, but other pages should be full (if there are more items)
            if result['has_next']:
                # Not the last page, should be full
                assert len(page_activity_ids) == page_size, \
                    f"Page {page} has {len(page_activity_ids)} items, expected {page_size} (not last page)"
            
            # Break if no more pages
            if not result['has_next']:
                break
            
            page += 1
            
            # Safety check to prevent infinite loops
            if page > 1000:
                pytest.fail("Pagination loop exceeded 1000 pages, likely infinite loop")
        
        # Property 1: Total count from service matches actual number of activities
        assert total_count_from_service == num_activities, \
            f"Service reported {total_count_from_service} activities, but {num_activities} were created"
        
        # Property 2: Number of collected activities equals total count
        assert len(collected_activity_ids) == num_activities, \
            f"Collected {len(collected_activity_ids)} activities across pages, expected {num_activities}"
        
        # Property 3: No duplicates - all IDs are unique
        assert len(collected_activity_ids) == len(set(collected_activity_ids)), \
            f"Found duplicate activities across pages. Collected {len(collected_activity_ids)}, unique {len(set(collected_activity_ids))}"
        
        # Property 4: All created activities are present in collected activities
        assert set(collected_activity_ids) == set(created_activity_ids), \
            f"Mismatch between created and collected activities. Missing: {set(created_activity_ids) - set(collected_activity_ids)}, Extra: {set(collected_activity_ids) - set(created_activity_ids)}"
        
        # Property 5: Total pages calculation is correct
        # Note: Django's Paginator returns 1 page for empty results
        if num_activities == 0:
            expected_pages = 1  # Django's Paginator returns 1 for empty results
        else:
            expected_pages = (num_activities + page_size - 1) // page_size  # Ceiling division
        
        assert total_pages_from_service == expected_pages, \
            f"Service reported {total_pages_from_service} pages, expected {expected_pages} for {num_activities} items with page_size {page_size}"
        
        # Property 6: Number of pages traversed matches total_pages
        assert page == max(total_pages_from_service, 1), \
            f"Traversed {page} pages, but service reported {total_pages_from_service} total pages"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_tournaments=st.integers(min_value=0, max_value=100),
        page_size=st.integers(min_value=1, max_value=30)
    )
    def test_tournament_history_pagination_consistency(self, num_tournaments, page_size):
        """
        Property: All tournament participations are present exactly once across all pages.
        
        This test verifies pagination consistency for tournament history.
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
        
        # Create tournaments and participations
        created_participant_ids = []
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
            
            participant = Participant.objects.create(
                user=user,
                tournament=tournament,
                status='confirmed',
                matches_won=3,
                matches_lost=2
            )
            created_participant_ids.append(participant.id)
        
        # Get tournament history using StatisticsService
        queryset = StatisticsService.get_tournament_history(
            user_id=user.id,
            filters=None
        )
        
        # Manually paginate the queryset
        from django.core.paginator import Paginator
        paginator = Paginator(queryset, page_size)
        
        # Collect all participants across all pages
        collected_participant_ids = []
        
        for page_num in range(1, paginator.num_pages + 1):
            page_obj = paginator.get_page(page_num)
            page_participant_ids = [p.id for p in page_obj.object_list]
            collected_participant_ids.extend(page_participant_ids)
            
            # Property: Page size should not exceed requested page_size
            assert len(page_participant_ids) <= page_size, \
                f"Page {page_num} has {len(page_participant_ids)} items, exceeds page_size {page_size}"
            
            # Property: Last page can be smaller, but other pages should be full
            if page_num < paginator.num_pages:
                # Not the last page, should be full
                assert len(page_participant_ids) == page_size, \
                    f"Page {page_num} has {len(page_participant_ids)} items, expected {page_size} (not last page)"
        
        # Property 1: Total count matches actual number of participations
        assert paginator.count == num_tournaments, \
            f"Paginator reported {paginator.count} participations, but {num_tournaments} were created"
        
        # Property 2: Number of collected participations equals total count
        assert len(collected_participant_ids) == num_tournaments, \
            f"Collected {len(collected_participant_ids)} participations across pages, expected {num_tournaments}"
        
        # Property 3: No duplicates - all IDs are unique
        assert len(collected_participant_ids) == len(set(collected_participant_ids)), \
            f"Found duplicate participations across pages. Collected {len(collected_participant_ids)}, unique {len(set(collected_participant_ids))}"
        
        # Property 4: All created participations are present in collected participations
        assert set(collected_participant_ids) == set(created_participant_ids), \
            f"Mismatch between created and collected participations"
        
        # Property 5: Total pages calculation is correct
        if num_tournaments == 0:
            expected_pages = 1  # Django Paginator returns 1 page even for empty queryset
        else:
            expected_pages = (num_tournaments + page_size - 1) // page_size  # Ceiling division
        
        assert paginator.num_pages == expected_pages, \
            f"Paginator reported {paginator.num_pages} pages, expected {expected_pages} for {num_tournaments} items with page_size {page_size}"
        
        # Cleanup - delete tournaments first (Game has PROTECT foreign key)
        Tournament.objects.filter(game=game).delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_activities=st.integers(min_value=10, max_value=100),
        page_size=st.integers(min_value=5, max_value=30),
        target_page=st.integers(min_value=1, max_value=10)
    )
    def test_pagination_page_boundaries(self, num_activities, page_size, target_page):
        """
        Property: Items on page boundaries are correctly assigned to pages.
        
        This test verifies that items at page boundaries don't leak between pages.
        """
        # Ensure target_page is valid for the given num_activities and page_size
        max_pages = (num_activities + page_size - 1) // page_size
        assume(target_page <= max_pages)
        
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create activities with sequential data
        for i in range(num_activities):
            Activity.objects.create(
                user=user,
                activity_type='profile_updated',
                data={'sequence': i}
            )
        
        # Get the target page
        result = ActivityService.get_activity_feed(
            user_id=user.id,
            filters=None,
            page=target_page,
            page_size=page_size
        )
        
        # Calculate expected items on this page
        start_index = (target_page - 1) * page_size
        end_index = min(start_index + page_size, num_activities)
        expected_count = end_index - start_index
        
        # Property: Page has correct number of items
        actual_count = len(result['activities'])
        assert actual_count == expected_count, \
            f"Page {target_page} has {actual_count} items, expected {expected_count}"
        
        # Property: has_next is correct
        expected_has_next = target_page < max_pages
        assert result['has_next'] == expected_has_next, \
            f"Page {target_page} has_next={result['has_next']}, expected {expected_has_next}"
        
        # Property: has_previous is correct
        expected_has_previous = target_page > 1
        assert result['has_previous'] == expected_has_previous, \
            f"Page {target_page} has_previous={result['has_previous']}, expected {expected_has_previous}"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_activities=st.integers(min_value=20, max_value=100),
        filter_type=st.sampled_from(['profile_updated', 'tournament_registered', 'team_joined'])
    )
    def test_pagination_with_filters(self, num_activities, filter_type):
        """
        Property: Pagination consistency is maintained when filters are applied.
        
        This test verifies that filtering doesn't break pagination consistency.
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create activities with different types
        activity_types = ['profile_updated', 'tournament_registered', 'team_joined']
        created_ids_by_type = {t: [] for t in activity_types}
        
        for i in range(num_activities):
            activity_type = activity_types[i % len(activity_types)]
            activity = Activity.objects.create(
                user=user,
                activity_type=activity_type,
                data={'index': i}
            )
            created_ids_by_type[activity_type].append(activity.id)
        
        # Get filtered activities with pagination
        page_size = 10
        filters = {'activity_type': filter_type}
        
        collected_ids = []
        page = 1
        
        while True:
            result = ActivityService.get_activity_feed(
                user_id=user.id,
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            page_ids = [a.id for a in result['activities']]
            collected_ids.extend(page_ids)
            
            if not result['has_next']:
                break
            
            page += 1
        
        # Property: All filtered activities are collected
        expected_ids = created_ids_by_type[filter_type]
        assert set(collected_ids) == set(expected_ids), \
            f"Filtered pagination didn't collect all {filter_type} activities"
        
        # Property: No duplicates
        assert len(collected_ids) == len(set(collected_ids)), \
            f"Found duplicates in filtered pagination"
        
        # Property: Total count matches filter
        result = ActivityService.get_activity_feed(
            user_id=user.id,
            filters=filters,
            page=1,
            page_size=page_size
        )
        assert result['total_count'] == len(expected_ids), \
            f"Total count {result['total_count']} doesn't match expected {len(expected_ids)}"
        
        # Cleanup
        user.delete()
    
    def test_pagination_empty_result(self):
        """
        Property: Pagination handles empty results correctly.
        
        Edge case test for when there are no items to paginate.
        """
        # Create a unique user with no activities
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Get activity feed for user with no activities
        result = ActivityService.get_activity_feed(
            user_id=user.id,
            filters=None,
            page=1,
            page_size=25
        )
        
        # Property: Empty result has correct structure
        assert result['total_count'] == 0, "Total count should be 0 for empty result"
        assert len(result['activities']) == 0, "Activities list should be empty"
        assert result['total_pages'] == 1, "Total pages should be 1 for empty result (Django Paginator behavior)"
        assert result['has_next'] == False, "has_next should be False for empty result"
        assert result['has_previous'] == False, "has_previous should be False for empty result"
        assert result['page'] == 1, "Page should be 1 even for empty result"
        
        # Cleanup
        user.delete()
    
    def test_pagination_single_item(self):
        """
        Property: Pagination handles single item correctly.
        
        Edge case test for when there is exactly one item.
        """
        # Create a unique user with one activity
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        activity = Activity.objects.create(
            user=user,
            activity_type='profile_updated',
            data={}
        )
        
        # Get activity feed
        result = ActivityService.get_activity_feed(
            user_id=user.id,
            filters=None,
            page=1,
            page_size=25
        )
        
        # Property: Single item result has correct structure
        assert result['total_count'] == 1, "Total count should be 1"
        assert len(result['activities']) == 1, "Activities list should have 1 item"
        assert result['activities'][0].id == activity.id, "Should return the correct activity"
        assert result['total_pages'] == 1, "Total pages should be 1"
        assert result['has_next'] == False, "has_next should be False"
        assert result['has_previous'] == False, "has_previous should be False"
        
        # Cleanup
        user.delete()
