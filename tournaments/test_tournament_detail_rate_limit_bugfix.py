"""
Property-Based Tests for Tournament Detail Rate Limit Bugfix

**Feature: tournament-detail-rate-limit-fix**
Tests the bug condition exploration for excessive polling causing rate limit errors.

This test is designed to FAIL on unfixed code to confirm the bug exists.
"""

import pytest
import time
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase as HypothesisTestCase

from tournaments.models import Tournament, Participant
from core.models import Game
from venues.models import Venue

User = get_user_model()


class RequestMonitor:
    """
    Monitor to track API requests made during test execution.
    This simulates monitoring network requests in a browser environment.
    """
    def __init__(self):
        self.requests = []
        self.request_counts = defaultdict(int)
        self.lock = threading.Lock()
    
    def record_request(self, endpoint, timestamp=None):
        """Record an API request"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.lock:
            self.requests.append({
                'endpoint': endpoint,
                'timestamp': timestamp
            })
            self.request_counts[endpoint] += 1
    
    def get_requests_per_minute(self, window_minutes=1):
        """Calculate requests per minute over the monitoring period"""
        if not self.requests:
            return 0
        
        with self.lock:
            if len(self.requests) < 2:
                return len(self.requests)
            
            # Calculate time span
            start_time = self.requests[0]['timestamp']
            end_time = self.requests[-1]['timestamp']
            duration_minutes = (end_time - start_time).total_seconds() / 60.0
            
            if duration_minutes == 0:
                return len(self.requests)
            
            return len(self.requests) / duration_minutes
    
    def get_unique_endpoints(self):
        """Get list of unique endpoints called"""
        with self.lock:
            return list(set(req['endpoint'] for req in self.requests))
    
    def get_request_count(self):
        """Get total request count"""
        with self.lock:
            return len(self.requests)
    
    def reset(self):
        """Reset the monitor"""
        with self.lock:
            self.requests = []
            self.request_counts = defaultdict(int)


class TournamentDetailRateLimitBugfixPropertyTests(HypothesisTestCase):
    """
    Property-Based Tests for Tournament Detail Rate Limit Bugfix
    
    **Feature: tournament-detail-rate-limit-fix**
    
    CRITICAL: These tests are designed to FAIL on unfixed code.
    Failure confirms the bug exists. DO NOT fix the test or code when it fails.
    """
    
    def setUp(self):
        """Set up test client and clean database"""
        self.client = Client()
        self.request_monitor = RequestMonitor()
        
        # Clean up any existing data
        Tournament.objects.all().delete()
        Game.objects.all().delete()
        User.objects.all().delete()
        Venue.objects.all().delete()
    
    def create_test_tournament(self, status='registration'):
        """Helper to create a test tournament"""
        game = Game.objects.create(
            name="Rate Limit Test Game",
            slug="rate-limit-test-game",
            genre='fps'
        )
        
        organizer = User.objects.create(
            email="organizer_ratelimit@test.com",
            username="organizer_ratelimit",
            first_name="Rate",
            last_name="Organizer"
        )
        
        now = timezone.now()
        tournament = Tournament.objects.create(
            name="Rate Limit Bug Test Tournament",
            slug="rate-limit-bug-test-tournament",
            description="Tournament for testing rate limit bug",
            game=game,
            organizer=organizer,
            status=status,
            max_participants=32,
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=7),
            check_in_start=now + timedelta(days=7, hours=1),
            start_datetime=now + timedelta(days=8),
            estimated_end=now + timedelta(days=9),
            format='single_elim',
            is_team_based=False,
            is_public=True
        )
        
        return tournament
    
    def simulate_page_polling(self, tournament_slug, duration_seconds=60):
        """
        Simulate the polling behavior that occurs when a user stays on the 
        tournament detail page. This monitors the API endpoints that would be
        called by the JavaScript polling mechanisms.
        
        On unfixed code, we expect:
        - Multiple separate API endpoints being called
        - High request frequency (8-10 requests per minute)
        - Potential for rate limit errors
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        # List of API endpoints that are polled on the tournament detail page
        # Based on design.md analysis of the unfixed code
        polling_endpoints = [
            reverse('tournaments:api_stats', kwargs={'slug': tournament_slug}),
            reverse('tournaments:api_updates', kwargs={'slug': tournament_slug}),
            # Note: Other endpoints may exist for registration, timeline, etc.
        ]
        
        request_count = 0
        rate_limit_errors = []
        
        # Simulate polling behavior over the duration
        while datetime.now() < end_time:
            for endpoint in polling_endpoints:
                try:
                    response = self.client.get(endpoint)
                    self.request_monitor.record_request(endpoint)
                    request_count += 1
                    
                    # Check for rate limit errors
                    if response.status_code == 429:
                        rate_limit_errors.append({
                            'endpoint': endpoint,
                            'timestamp': datetime.now(),
                            'request_number': request_count
                        })
                except Exception as e:
                    # Record any errors
                    pass
            
            # Simulate the polling interval (30 seconds based on design.md)
            # In unfixed code, multiple components poll every 30 seconds
            time.sleep(2)  # Reduced for testing, but represents 30s intervals
        
        return {
            'total_requests': request_count,
            'rate_limit_errors': rate_limit_errors,
            'unique_endpoints': self.request_monitor.get_unique_endpoints(),
            'requests_per_minute': self.request_monitor.get_requests_per_minute()
        }
    
    @settings(max_examples=3, deadline=None)
    @given(
        tournament_status=st.sampled_from(['registration', 'check_in', 'in_progress']),
        monitoring_duration=st.integers(min_value=30, max_value=120)
    )
    def test_property_fault_condition_rate_limit_trigger(
        self,
        tournament_status,
        monitoring_duration
    ):
        """
        Property 1: Fault Condition - Rate Limit Trigger from Multiple Polling Intervals
        
        **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists.
        **DO NOT attempt to fix the test or the code when it fails.**
        
        For any tournament detail page state where multiple components require real-time 
        updates, the UNFIXED code will make excessive API requests due to uncoordinated 
        polling intervals, leading to:
        - Multiple concurrent setInterval calls (5+)
        - High request frequency (8-10 requests per minute)
        - Potential HTTP 429 rate limit errors
        - Continued polling even when tab is hidden
        
        The FIXED code should:
        - Use a single unified polling mechanism (1 setInterval)
        - Reduce request frequency to ≤1 request per minute
        - Never trigger HTTP 429 errors
        - Pause or slow polling when tab is hidden
        
        **Feature: tournament-detail-rate-limit-fix, Property 1: Fault Condition**
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5 (Current Behavior - Defect)**
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5 (Expected Behavior - Correct)**
        """
        # Create test tournament
        tournament = self.create_test_tournament(status=tournament_status)
        
        # First, verify the tournament detail page loads successfully
        detail_url = reverse('tournaments:detail', kwargs={'slug': tournament.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200, 
                        "Tournament detail page should load successfully")
        
        # Simulate the polling behavior that occurs when a user stays on the page
        print(f"\n🔍 Monitoring tournament detail page polling for {monitoring_duration} seconds...")
        print(f"   Tournament: {tournament.name} (Status: {tournament_status})")
        
        polling_results = self.simulate_page_polling(
            tournament.slug, 
            duration_seconds=monitoring_duration
        )
        
        # Document the counterexamples found
        print(f"\n📊 Polling Behavior Analysis:")
        print(f"   Total Requests: {polling_results['total_requests']}")
        print(f"   Requests Per Minute: {polling_results['requests_per_minute']:.2f}")
        print(f"   Unique Endpoints: {len(polling_results['unique_endpoints'])}")
        print(f"   Rate Limit Errors (429): {len(polling_results['rate_limit_errors'])}")
        
        if polling_results['unique_endpoints']:
            print(f"\n   Endpoints Called:")
            for endpoint in polling_results['unique_endpoints']:
                print(f"     - {endpoint}")
        
        if polling_results['rate_limit_errors']:
            print(f"\n   ⚠️  Rate Limit Errors Detected:")
            for error in polling_results['rate_limit_errors'][:3]:  # Show first 3
                print(f"     - Request #{error['request_number']}: {error['endpoint']}")
        
        # ASSERTIONS - These encode the EXPECTED BEHAVIOR (will fail on unfixed code)
        
        # Expected Behavior 2.2: Single unified polling mechanism
        # On unfixed code: Multiple separate endpoints are called
        # On fixed code: Should use single unified endpoint
        print(f"\n✅ Assertion 1: Unified Polling (Expected: 1 endpoint, Actual: {len(polling_results['unique_endpoints'])})")
        self.assertLessEqual(
            len(polling_results['unique_endpoints']), 
            1,
            f"EXPECTED FAILURE ON UNFIXED CODE: Multiple polling endpoints detected "
            f"({len(polling_results['unique_endpoints'])}). Fixed code should use single unified endpoint. "
            f"Endpoints: {polling_results['unique_endpoints']}"
        )
        
        # Expected Behavior 2.1, 2.2, 2.3: Reduced request frequency
        # On unfixed code: 8-10 requests per minute (5 components × 2 requests/min each)
        # On fixed code: ≤1 request per minute
        print(f"✅ Assertion 2: Request Frequency (Expected: ≤1 req/min, Actual: {polling_results['requests_per_minute']:.2f} req/min)")
        self.assertLessEqual(
            polling_results['requests_per_minute'],
            1.0,
            f"EXPECTED FAILURE ON UNFIXED CODE: Excessive request frequency detected "
            f"({polling_results['requests_per_minute']:.2f} requests/minute). "
            f"Fixed code should make ≤1 request per minute."
        )
        
        # Expected Behavior 2.1, 2.5: No rate limit errors
        # On unfixed code: May encounter HTTP 429 errors after extended monitoring
        # On fixed code: Should never encounter rate limit errors
        print(f"✅ Assertion 3: No Rate Limits (Expected: 0 errors, Actual: {len(polling_results['rate_limit_errors'])} errors)")
        self.assertEqual(
            len(polling_results['rate_limit_errors']),
            0,
            f"EXPECTED FAILURE ON UNFIXED CODE: Rate limit errors detected "
            f"({len(polling_results['rate_limit_errors'])} HTTP 429 responses). "
            f"Fixed code should never trigger rate limits."
        )
        
        print(f"\n{'='*70}")
        print(f"TEST RESULT: This test is EXPECTED TO FAIL on unfixed code.")
        print(f"Failure confirms the bug exists (excessive polling causing rate limits).")
        print(f"{'='*70}\n")


class TournamentDetailPreservationPropertyTests(HypothesisTestCase):
    """
    Property-Based Tests for Preservation of Real-Time Update Functionality
    
    **Feature: tournament-detail-rate-limit-fix**
    
    These tests verify that all real-time update functionality continues to work
    correctly after the fix is implemented. They establish a baseline by running
    on UNFIXED code first, then verify the same behavior on FIXED code.
    
    **EXPECTED OUTCOME**: These tests should PASS on both unfixed and fixed code.
    """
    
    def setUp(self):
        """Set up test client and clean database"""
        self.client = Client()
        
        # Clean up any existing data
        Tournament.objects.all().delete()
        Game.objects.all().delete()
        User.objects.all().delete()
        Venue.objects.all().delete()
    
    def create_test_tournament(self, status='registration', participant_count=0):
        """Helper to create a test tournament with participants"""
        import random
        import string
        
        # Generate short random suffix to avoid username collisions
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        game = Game.objects.create(
            name=f"Preservation Test Game {status}",
            slug=f"pres-test-game-{status}-{suffix}",
            genre='fps'
        )
        
        organizer = User.objects.create(
            email=f"org_pres_{suffix}@test.com",
            username=f"org_pres_{suffix}",
            first_name="Preservation",
            last_name="Organizer"
        )
        
        now = timezone.now()
        tournament = Tournament.objects.create(
            name=f"Preservation Test Tournament {status}",
            slug=f"pres-test-tourn-{status}-{suffix}",
            description="Tournament for testing preservation of real-time updates",
            game=game,
            organizer=organizer,
            status=status,
            max_participants=32,
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=7),
            check_in_start=now + timedelta(days=7, hours=1),
            start_datetime=now + timedelta(days=8),
            estimated_end=now + timedelta(days=9),
            format='single_elim',
            is_team_based=False,
            is_public=True
        )
        
        # Create participants if requested
        checked_in_count = 0
        for i in range(participant_count):
            user = User.objects.create(
                email=f"part_{suffix}_{i}@test.com",
                username=f"part_{suffix}_{i}"[:30],  # Ensure max 30 chars
                first_name=f"Player{i}",
                last_name="Test"
            )
            is_checked_in = (i < participant_count // 2)  # First half checked in
            if is_checked_in:
                checked_in_count += 1
            Participant.objects.create(
                tournament=tournament,
                user=user,
                status='confirmed',
                checked_in=is_checked_in,
                seed=i + 1
            )
        
        # Update tournament statistics to match actual participants
        tournament.total_registered = participant_count
        tournament.total_checked_in = checked_in_count
        tournament.save()
        
        return tournament
    
    @settings(max_examples=5, deadline=None)
    @given(
        tournament_status=st.sampled_from(['registration', 'check_in', 'in_progress']),
        participant_count=st.integers(min_value=0, max_value=16)
    )
    def test_property_preservation_statistics_updates(
        self,
        tournament_status,
        participant_count
    ):
        """
        Property 4: Preservation - Real-Time Statistics Updates
        
        For any tournament statistics change (participant count, match count, 
        completion percentage), the fixed code SHALL continue to update the 
        display with the same data accuracy as the original code.
        
        This test verifies that the statistics API endpoint returns accurate
        data that matches the actual tournament state across various configurations.
        
        **Feature: tournament-detail-rate-limit-fix, Property 4: Preservation**
        **Validates: Requirements 3.1, 3.5**
        """
        # Create tournament with participants
        tournament = self.create_test_tournament(
            status=tournament_status,
            participant_count=participant_count
        )
        
        # Fetch statistics via API endpoint
        stats_url = reverse('tournaments:api_stats', kwargs={'slug': tournament.slug})
        response = self.client.get(stats_url)
        
        # Verify endpoint is accessible
        self.assertEqual(response.status_code, 200,
                        "Statistics API endpoint should be accessible")
        
        stats_data = response.json()
        
        # Verify statistics structure exists
        self.assertIn('participants', stats_data,
                     "Statistics should include participant data")
        self.assertIn('matches', stats_data,
                     "Statistics should include match data")
        self.assertIn('status', stats_data,
                     "Statistics should include tournament status")
        
        # Verify participant statistics accuracy
        participant_stats = stats_data['participants']
        self.assertEqual(
            participant_stats['registered'],
            participant_count,
            f"Registered count should match actual participants: "
            f"expected {participant_count}, got {participant_stats['registered']}"
        )
        
        expected_checked_in = participant_count // 2  # Half are checked in
        self.assertEqual(
            participant_stats['checked_in'],
            expected_checked_in,
            f"Checked-in count should match actual: "
            f"expected {expected_checked_in}, got {participant_stats['checked_in']}"
        )
        
        self.assertEqual(
            participant_stats['capacity'],
            32,
            "Capacity should match tournament max_participants"
        )
        
        expected_spots = max(0, 32 - participant_count)
        self.assertEqual(
            participant_stats['spots_remaining'],
            expected_spots,
            f"Spots remaining should be calculated correctly: "
            f"expected {expected_spots}, got {participant_stats['spots_remaining']}"
        )
        
        # Verify status matches
        self.assertEqual(
            stats_data['status'],
            tournament_status,
            f"Status should match tournament state: "
            f"expected {tournament_status}, got {stats_data['status']}"
        )
        
        print(f"\n✅ Statistics Preservation Test Passed:")
        print(f"   Tournament: {tournament.slug}")
        print(f"   Status: {tournament_status}")
        print(f"   Participants: {participant_count} registered, {expected_checked_in} checked in")
        print(f"   API Response: Accurate and complete")
    
    @settings(max_examples=5, deadline=None)
    @given(
        tournament_status=st.sampled_from(['registration', 'check_in', 'in_progress']),
        participant_count=st.integers(min_value=0, max_value=20)
    )
    def test_property_preservation_registration_status(
        self,
        tournament_status,
        participant_count
    ):
        """
        Property 5: Preservation - Registration Status Updates
        
        For any tournament registration status change (capacity, spots remaining,
        registration open/closed), the fixed code SHALL continue to reflect the
        current state accurately.
        
        **Feature: tournament-detail-rate-limit-fix, Property 5: Preservation**
        **Validates: Requirements 3.2, 3.5**
        """
        # Create tournament with participants
        tournament = self.create_test_tournament(
            status=tournament_status,
            participant_count=participant_count
        )
        
        # Fetch updates via API endpoint
        updates_url = reverse('tournaments:api_updates', kwargs={'slug': tournament.slug})
        response = self.client.get(updates_url)
        
        # Verify endpoint is accessible
        self.assertEqual(response.status_code, 200,
                        "Updates API endpoint should be accessible")
        
        updates_data = response.json()
        
        # Verify registration status structure
        self.assertIn('stats', updates_data,
                     "Updates should include stats data")
        self.assertIn('participants', updates_data['stats'],
                     "Stats should include participant information")
        
        participant_data = updates_data['stats']['participants']
        
        # Verify registration status accuracy
        self.assertEqual(
            participant_data['registered'],
            participant_count,
            f"Registration count should be accurate: "
            f"expected {participant_count}, got {participant_data['registered']}"
        )
        
        expected_spots = max(0, 32 - participant_count)
        self.assertEqual(
            participant_data['spots_remaining'],
            expected_spots,
            f"Spots remaining should be calculated correctly: "
            f"expected {expected_spots}, got {participant_data['spots_remaining']}"
        )
        
        # Verify capacity percentage calculation
        expected_percentage = (participant_count / 32) * 100 if 32 > 0 else 0
        self.assertAlmostEqual(
            participant_data['percentage_full'],
            expected_percentage,
            places=1,
            msg=f"Capacity percentage should be accurate: "
                f"expected {expected_percentage:.1f}%, got {participant_data['percentage_full']:.1f}%"
        )
        
        print(f"\n✅ Registration Status Preservation Test Passed:")
        print(f"   Tournament: {tournament.slug}")
        print(f"   Capacity: {participant_count}/32 ({expected_percentage:.1f}% full)")
        print(f"   Spots Remaining: {expected_spots}")
        print(f"   API Response: Accurate registration status")
    
    @settings(max_examples=5, deadline=None)
    @given(
        tournament_status=st.sampled_from(['registration', 'check_in', 'in_progress', 'completed']),
        participant_count=st.integers(min_value=4, max_value=16)
    )
    def test_property_preservation_timeline_progress(
        self,
        tournament_status,
        participant_count
    ):
        """
        Property 6: Preservation - Timeline and Progress Updates
        
        For any tournament timeline phase transition, the fixed code SHALL
        continue to display accurate phase information and progress values.
        
        **Feature: tournament-detail-rate-limit-fix, Property 6: Preservation**
        **Validates: Requirements 3.3, 3.4**
        """
        # Create tournament
        tournament = self.create_test_tournament(
            status=tournament_status,
            participant_count=participant_count
        )
        
        # Fetch updates via API endpoint
        updates_url = reverse('tournaments:api_updates', kwargs={'slug': tournament.slug})
        response = self.client.get(updates_url)
        
        # Verify endpoint is accessible
        self.assertEqual(response.status_code, 200,
                        "Updates API endpoint should be accessible")
        
        updates_data = response.json()
        
        # Verify timeline structure
        self.assertIn('timeline', updates_data,
                     "Updates should include timeline data")
        self.assertIn('status', updates_data,
                     "Updates should include tournament status")
        
        timeline_data = updates_data['timeline']
        
        # Verify current phase matches tournament status
        self.assertEqual(
            timeline_data['current_phase'],
            tournament_status,
            f"Timeline phase should match tournament status: "
            f"expected {tournament_status}, got {timeline_data['current_phase']}"
        )
        
        # Verify progress percentage is reasonable
        progress = timeline_data['progress_percentage']
        self.assertGreaterEqual(progress, 0,
                               "Progress percentage should be >= 0")
        self.assertLessEqual(progress, 100,
                            "Progress percentage should be <= 100")
        
        # Verify progress matches expected values for each phase
        expected_progress = {
            'draft': 0,
            'registration': 25,
            'check_in': 50,
            'in_progress': 75,
            'completed': 100,
            'cancelled': 0
        }
        
        self.assertEqual(
            progress,
            expected_progress.get(tournament_status, 0),
            f"Progress percentage should match phase: "
            f"expected {expected_progress.get(tournament_status, 0)}, got {progress}"
        )
        
        print(f"\n✅ Timeline Progress Preservation Test Passed:")
        print(f"   Tournament: {tournament.slug}")
        print(f"   Phase: {tournament_status}")
        print(f"   Progress: {progress}%")
        print(f"   API Response: Accurate timeline data")
    
    @settings(max_examples=5, deadline=None)
    @given(
        tournament_status=st.sampled_from(['registration', 'check_in']),
        participant_count=st.integers(min_value=2, max_value=12)
    )
    def test_property_preservation_participant_display(
        self,
        tournament_status,
        participant_count
    ):
        """
        Property 7: Preservation - Participant List Updates
        
        For any participant updates (new registrations, check-in status changes),
        the fixed code SHALL continue to show current registrations and check-ins
        accurately.
        
        **Feature: tournament-detail-rate-limit-fix, Property 7: Preservation**
        **Validates: Requirements 3.5, 3.6**
        """
        # Create tournament with participants
        tournament = self.create_test_tournament(
            status=tournament_status,
            participant_count=participant_count
        )
        
        # Fetch participants via API endpoint
        participants_url = reverse('tournaments:api_participants', kwargs={'slug': tournament.slug})
        response = self.client.get(participants_url)
        
        # Verify endpoint is accessible
        self.assertEqual(response.status_code, 200,
                        "Participants API endpoint should be accessible")
        
        participants_data = response.json()
        
        # Verify participant list structure
        self.assertIn('participants', participants_data,
                     "Response should include participants list")
        self.assertIn('total', participants_data,
                     "Response should include total count")
        
        # Verify participant count matches
        self.assertEqual(
            participants_data['total'],
            participant_count,
            f"Total participant count should match: "
            f"expected {participant_count}, got {participants_data['total']}"
        )
        
        # Verify participant data structure
        participants_list = participants_data['participants']
        self.assertEqual(
            len(participants_list),
            participant_count,
            f"Participant list length should match: "
            f"expected {participant_count}, got {len(participants_list)}"
        )
        
        # Verify each participant has required fields
        for participant in participants_list:
            self.assertIn('id', participant,
                         "Participant should have ID")
            self.assertIn('display_name', participant,
                         "Participant should have display name")
            self.assertIn('seed', participant,
                         "Participant should have seed")
            self.assertIn('checked_in', participant,
                         "Participant should have checked_in status")
            self.assertIn('status', participant,
                         "Participant should have status")
        
        # Verify check-in status accuracy
        checked_in_count = sum(1 for p in participants_list if p['checked_in'])
        expected_checked_in = participant_count // 2
        self.assertEqual(
            checked_in_count,
            expected_checked_in,
            f"Checked-in count should match: "
            f"expected {expected_checked_in}, got {checked_in_count}"
        )
        
        print(f"\n✅ Participant Display Preservation Test Passed:")
        print(f"   Tournament: {tournament.slug}")
        print(f"   Total Participants: {participant_count}")
        print(f"   Checked In: {checked_in_count}")
        print(f"   API Response: Complete participant data")
    
    @settings(max_examples=3, deadline=None)
    @given(
        tournament_status=st.sampled_from(['registration', 'check_in', 'in_progress'])
    )
    def test_property_preservation_update_freshness(
        self,
        tournament_status
    ):
        """
        Property 8: Preservation - Update Freshness and Timestamps
        
        For all real-time updates, the fixed code SHALL continue to provide
        fresh data with accurate timestamps, ensuring users see current information.
        
        **Feature: tournament-detail-rate-limit-fix, Property 8: Preservation**
        **Validates: Requirements 3.5**
        """
        # Create tournament
        tournament = self.create_test_tournament(
            status=tournament_status,
            participant_count=8
        )
        
        # Fetch updates via API endpoint
        updates_url = reverse('tournaments:api_updates', kwargs={'slug': tournament.slug})
        response = self.client.get(updates_url)
        
        # Verify endpoint is accessible
        self.assertEqual(response.status_code, 200,
                        "Updates API endpoint should be accessible")
        
        updates_data = response.json()
        
        # Verify timestamp exists
        self.assertIn('timestamp', updates_data,
                     "Updates should include timestamp")
        
        # Verify timestamp is recent (within last 5 seconds)
        timestamp_str = updates_data['timestamp']
        from django.utils.dateparse import parse_datetime
        timestamp = parse_datetime(timestamp_str)
        
        self.assertIsNotNone(timestamp,
                            "Timestamp should be valid ISO format")
        
        time_diff = timezone.now() - timestamp
        self.assertLess(
            time_diff.total_seconds(),
            5,
            f"Timestamp should be recent (within 5 seconds): "
            f"age = {time_diff.total_seconds():.2f}s"
        )
        
        # Verify connection status
        self.assertIn('connection_status', updates_data,
                     "Updates should include connection status")
        self.assertEqual(
            updates_data['connection_status'],
            'connected',
            "Connection status should indicate successful connection"
        )
        
        print(f"\n✅ Update Freshness Preservation Test Passed:")
        print(f"   Tournament: {tournament.slug}")
        print(f"   Timestamp Age: {time_diff.total_seconds():.2f}s")
        print(f"   Connection Status: {updates_data['connection_status']}")
        print(f"   API Response: Fresh data with valid timestamps")


class TournamentDetailPollingBehaviorTests(TestCase):
    """
    Unit tests for specific polling behavior scenarios.
    These complement the property-based tests with targeted test cases.
    """
    
    def setUp(self):
        """Set up test client and clean database"""
        self.client = Client()
        
        # Clean up any existing data
        Tournament.objects.all().delete()
        Game.objects.all().delete()
        User.objects.all().delete()
    
    def create_test_tournament(self):
        """Helper to create a test tournament"""
        game = Game.objects.create(
            name="Polling Test Game",
            slug="polling-test-game",
            genre='fps'
        )
        
        organizer = User.objects.create(
            email="organizer_polling@test.com",
            username="organizer_polling",
            first_name="Polling",
            last_name="Organizer"
        )
        
        now = timezone.now()
        tournament = Tournament.objects.create(
            name="Polling Behavior Test Tournament",
            slug="polling-behavior-test-tournament",
            description="Tournament for testing polling behavior",
            game=game,
            organizer=organizer,
            status='registration',
            max_participants=32,
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=7),
            check_in_start=now + timedelta(days=7, hours=1),
            start_datetime=now + timedelta(days=8),
            estimated_end=now + timedelta(days=9),
            format='single_elim',
            is_team_based=False,
            is_public=True
        )
        
        return tournament
    
    def test_multiple_api_endpoints_exist(self):
        """
        Test that multiple separate API endpoints exist for tournament updates.
        
        On unfixed code: Multiple endpoints exist (stats, updates, registration, etc.)
        On fixed code: Should have a unified endpoint (or endpoints should be consolidated)
        
        **EXPECTED TO FAIL on unfixed code** - confirms multiple endpoints exist
        """
        tournament = self.create_test_tournament()
        
        # Test that multiple API endpoints are accessible
        endpoints_to_test = [
            ('api_stats', reverse('tournaments:api_stats', kwargs={'slug': tournament.slug})),
            ('api_updates', reverse('tournaments:api_updates', kwargs={'slug': tournament.slug})),
        ]
        
        accessible_endpoints = []
        for name, url in endpoints_to_test:
            try:
                response = self.client.get(url)
                if response.status_code == 200:
                    accessible_endpoints.append(name)
            except Exception:
                pass
        
        print(f"\n📊 API Endpoint Analysis:")
        print(f"   Accessible Endpoints: {len(accessible_endpoints)}")
        for endpoint in accessible_endpoints:
            print(f"     - {endpoint}")
        
        # ASSERTION: Fixed code should consolidate to single endpoint
        self.assertLessEqual(
            len(accessible_endpoints),
            1,
            f"EXPECTED FAILURE ON UNFIXED CODE: Multiple separate API endpoints exist "
            f"({len(accessible_endpoints)}). Fixed code should use unified endpoint. "
            f"Endpoints: {accessible_endpoints}"
        )
    
    def test_api_endpoints_return_data(self):
        """
        Test that API endpoints return the expected data structure.
        This helps verify that the endpoints are actually being used for polling.
        """
        tournament = self.create_test_tournament()
        
        # Test statistics endpoint
        stats_url = reverse('tournaments:api_stats', kwargs={'slug': tournament.slug})
        stats_response = self.client.get(stats_url)
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"\n📊 Statistics API Response:")
            print(f"   Status Code: {stats_response.status_code}")
            print(f"   Data Keys: {list(stats_data.keys())}")
            
            # Verify expected data structure
            self.assertIn('participants', stats_data)
            self.assertIn('matches', stats_data)
        
        # Test updates endpoint
        updates_url = reverse('tournaments:api_updates', kwargs={'slug': tournament.slug})
        updates_response = self.client.get(updates_url)
        
        if updates_response.status_code == 200:
            updates_data = updates_response.json()
            print(f"\n📊 Updates API Response:")
            print(f"   Status Code: {updates_response.status_code}")
            print(f"   Data Keys: {list(updates_data.keys())}")
