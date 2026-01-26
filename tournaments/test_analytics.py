"""
Tests for tournament analytics functionality.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import timedelta
import json

from .models import Tournament, Game
from .analytics_models import (
    PageView, UserEngagement, ConversionEvent, ErrorLog, 
    PerformanceMetric, AnalyticsSummary
)
from .analytics_service import AnalyticsService

User = get_user_model()


class AnalyticsServiceTest(TestCase):
    """Test analytics service functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game'
        )
        
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.user,
            start_datetime=timezone.now() + timezone.timedelta(days=1),
            registration_start=timezone.now() - timezone.timedelta(hours=1),
            registration_end=timezone.now() + timezone.timedelta(hours=12),
            check_in_start=timezone.now() + timezone.timedelta(hours=12),
            max_participants=32,
            registration_fee=10.00
        )
        
        self.client = Client()
    
    def test_track_page_view(self):
        """Test page view tracking"""
        # Create a mock request
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Track page view
        page_view = AnalyticsService.track_page_view(
            request=request,
            url=f'/tournaments/{self.tournament.slug}/',
            performance_data={
                'loadTime': 1500,
                'firstPaint': 800,
                'screenWidth': 1920,
                'screenHeight': 1080
            }
        )
        
        # Verify page view was created
        self.assertIsNotNone(page_view)
        self.assertEqual(page_view.url, f'/tournaments/{self.tournament.slug}/')
        self.assertEqual(page_view.user, self.user)
        self.assertEqual(page_view.load_time, 1500)
        self.assertEqual(page_view.first_paint, 800)
        
        # Verify engagement record was created
        self.assertTrue(hasattr(page_view, 'engagement'))
        self.assertIsNotNone(page_view.engagement)
    
    def test_update_engagement(self):
        """Test engagement tracking"""
        # Create page view first
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        page_view = AnalyticsService.track_page_view(
            request=request,
            url=f'/tournaments/{self.tournament.slug}/'
        )
        
        # Update engagement
        engagement_data = {
            'timeOnPage': 120,
            'scrollDepth': 75,
            'clicksCount': 5,
            'registrationButtonClicks': 1,
            'shareButtonClicks': 2
        }
        
        engagement = AnalyticsService.update_engagement(
            session_key=request.session.session_key,
            engagement_data=engagement_data
        )
        
        # Verify engagement was updated
        self.assertIsNotNone(engagement)
        self.assertEqual(engagement.time_on_page, 120)
        self.assertEqual(engagement.scroll_depth, 75)
        self.assertEqual(engagement.clicks_count, 5)
        self.assertEqual(engagement.registration_button_clicks, 1)
        self.assertEqual(engagement.share_button_clicks, 2)
    
    def test_track_conversion(self):
        """Test conversion tracking"""
        conversion = AnalyticsService.track_conversion(
            event_type='registration_completed',
            content_object=self.tournament,
            user=self.user,
            session_key='test_session',
            metadata={'test': 'data'}
        )
        
        # Verify conversion was tracked
        self.assertIsNotNone(conversion)
        self.assertEqual(conversion.event_type, 'registration_completed')
        self.assertEqual(conversion.content_object, self.tournament)
        self.assertEqual(conversion.user, self.user)
        self.assertEqual(conversion.metadata['test'], 'data')
    
    def test_track_error(self):
        """Test error tracking"""
        error_log = AnalyticsService.track_error(
            error_type='javascript',
            message='Test error message',
            url=f'/tournaments/{self.tournament.slug}/',
            user=self.user,
            session_key='test_session',
            severity='high',
            file_name='test.js',
            line_number=42
        )
        
        # Verify error was tracked
        self.assertIsNotNone(error_log)
        self.assertEqual(error_log.error_type, 'javascript')
        self.assertEqual(error_log.message, 'Test error message')
        self.assertEqual(error_log.severity, 'high')
        self.assertEqual(error_log.file_name, 'test.js')
        self.assertEqual(error_log.line_number, 42)
    
    def test_get_dashboard_data(self):
        """Test dashboard data generation"""
        # Create some test data
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create page views
        for i in range(5):
            AnalyticsService.track_page_view(
                request=request,
                url=f'/tournaments/{self.tournament.slug}/'
            )
        
        # Create conversions
        for i in range(2):
            AnalyticsService.track_conversion(
                event_type='registration_completed',
                content_object=self.tournament,
                user=self.user,
                session_key=request.session.session_key
            )
        
        # Get dashboard data
        dashboard_data = AnalyticsService.get_dashboard_data(
            tournament_slug=self.tournament.slug,
            days=7
        )
        
        # Verify dashboard data
        self.assertIn('overview', dashboard_data)
        self.assertIn('performance', dashboard_data)
        self.assertIn('engagement', dashboard_data)
        self.assertIn('daily_data', dashboard_data)
        
        # Check overview metrics
        self.assertEqual(dashboard_data['overview']['total_views'], 5)
        self.assertEqual(dashboard_data['overview']['total_conversions'], 2)
        self.assertEqual(dashboard_data['overview']['conversion_rate'], 40.0)


class AnalyticsAPITest(TestCase):
    """Test analytics API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game'
        )
        
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.user,
            start_datetime=timezone.now() + timezone.timedelta(days=1),
            registration_start=timezone.now() - timezone.timedelta(hours=1),
            registration_end=timezone.now() + timezone.timedelta(hours=12),
            check_in_start=timezone.now() + timezone.timedelta(hours=12),
            max_participants=32,
            registration_fee=10.00
        )
        
        self.client = Client()
    
    def test_track_page_performance_api(self):
        """Test page performance tracking API"""
        url = reverse('tournaments:analytics_performance')
        data = {
            'url': f'/tournaments/{self.tournament.slug}/',
            'loadTime': 1200,
            'firstPaint': 600,
            'screenWidth': 1920,
            'screenHeight': 1080
        }
        
        # Ensure session exists
        session = self.client.session
        session.save()
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('page_view_id', response_data)
        
        # Verify page view was created
        page_view = PageView.objects.get(id=response_data['page_view_id'])
        self.assertEqual(page_view.load_time, 1200)
        self.assertEqual(page_view.first_paint, 600)
    
    def test_track_engagement_api(self):
        """Test engagement tracking API"""
        # First create a page view with session
        session = self.client.session
        session.save()
        
        # Create a page view first
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session = session
        
        AnalyticsService.track_page_view(
            request=request,
            url=f'/tournaments/{self.tournament.slug}/'
        )
        
        url = reverse('tournaments:analytics_engagement')
        data = {
            'timeOnPage': 90,
            'scrollDepth': 80,
            'clicksCount': 3,
            'registrationButtonClicks': 1
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('engagement_score', response_data)
    
    def test_track_conversion_api(self):
        """Test conversion tracking API"""
        # Ensure session exists
        session = self.client.session
        session.save()
        
        url = reverse('tournaments:analytics_conversion')
        data = {
            'eventType': 'registration_completed',
            'tournamentSlug': self.tournament.slug,
            'metadata': {'test': 'data'}
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('conversion_id', response_data)
        
        # Verify conversion was created
        conversion = ConversionEvent.objects.get(id=response_data['conversion_id'])
        self.assertEqual(conversion.event_type, 'registration_completed')
        self.assertEqual(conversion.content_object, self.tournament)
    
    def test_track_error_api(self):
        """Test error tracking API"""
        # Ensure session exists
        session = self.client.session
        session.save()
        
        url = reverse('tournaments:analytics_error')
        data = {
            'errorType': 'javascript',
            'message': 'Test error from API',
            'severity': 'medium',
            'fileName': 'test.js',
            'lineNumber': 123
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('error_id', response_data)
        
        # Verify error was created
        error_log = ErrorLog.objects.get(id=response_data['error_id'])
        self.assertEqual(error_log.message, 'Test error from API')
        self.assertEqual(error_log.severity, 'medium')
    
    def test_analytics_dashboard_api_permission(self):
        """Test analytics dashboard API requires proper permissions"""
        url = reverse('tournaments:analytics_dashboard')
        
        # Test without authentication
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        # Test with wrong user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client.force_login(other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Test with staff user
        staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(staff_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)


class AnalyticsMetricsCollectionTest(TestCase):
    """Test analytics metrics collection functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game'
        )
        
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.user,
            start_datetime=timezone.now() + timezone.timedelta(days=1),
            registration_start=timezone.now() - timezone.timedelta(hours=1),
            registration_end=timezone.now() + timezone.timedelta(hours=12),
            check_in_start=timezone.now() + timezone.timedelta(hours=12),
            max_participants=32,
            registration_fee=10.00
        )
        
        self.client = Client()
    
    def test_metrics_collection_accuracy(self):
        """Test that metrics are collected accurately"""
        # Create test data
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Track multiple page views with different performance data
        performance_data_sets = [
            {'loadTime': 1200, 'firstPaint': 600, 'screenWidth': 1920},
            {'loadTime': 1500, 'firstPaint': 800, 'screenWidth': 1366},
            {'loadTime': 900, 'firstPaint': 450, 'screenWidth': 1920}
        ]
        
        page_views = []
        for perf_data in performance_data_sets:
            page_view = AnalyticsService.track_page_view(
                request=request,
                url=f'/tournaments/{self.tournament.slug}/',
                performance_data=perf_data
            )
            page_views.append(page_view)
        
        # Verify each page view has correct data
        for i, page_view in enumerate(page_views):
            expected_data = performance_data_sets[i]
            self.assertEqual(page_view.load_time, expected_data['loadTime'])
            self.assertEqual(page_view.first_paint, expected_data['firstPaint'])
            self.assertEqual(page_view.screen_width, expected_data['screenWidth'])
        
        # Test aggregated metrics accuracy
        dashboard_data = AnalyticsService.get_dashboard_data(
            tournament_slug=self.tournament.slug,
            days=1
        )
        
        # Verify total views count
        self.assertEqual(dashboard_data['overview']['total_views'], 3)
        
        # Verify average load time calculation
        expected_avg_load_time = sum(data['loadTime'] for data in performance_data_sets) / len(performance_data_sets)
        self.assertEqual(dashboard_data['performance']['avg_load_time'], expected_avg_load_time)
        
        # Verify average first paint calculation
        expected_avg_first_paint = sum(data['firstPaint'] for data in performance_data_sets) / len(performance_data_sets)
        self.assertAlmostEqual(dashboard_data['performance']['avg_first_paint'], expected_avg_first_paint, places=2)
    
    def test_engagement_metrics_calculation(self):
        """Test engagement metrics calculation accuracy"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create page view
        page_view = AnalyticsService.track_page_view(
            request=request,
            url=f'/tournaments/{self.tournament.slug}/'
        )
        
        # Update engagement with specific values
        engagement_data = {
            'timeOnPage': 180,  # 3 minutes
            'scrollDepth': 85,
            'clicksCount': 8,
            'registrationButtonClicks': 2,
            'shareButtonClicks': 1,
            'tabSwitches': 3,
            'participantCardClicks': 2
        }
        
        engagement = AnalyticsService.update_engagement(
            session_key=request.session.session_key,
            engagement_data=engagement_data
        )
        
        # Verify all metrics were recorded correctly
        self.assertEqual(engagement.time_on_page, 180)
        self.assertEqual(engagement.scroll_depth, 85)
        self.assertEqual(engagement.clicks_count, 8)
        self.assertEqual(engagement.registration_button_clicks, 2)
        self.assertEqual(engagement.share_button_clicks, 1)
        self.assertEqual(engagement.tab_switches, 3)
        self.assertEqual(engagement.participant_card_clicks, 2)
        
        # Test engagement score calculation
        expected_score = (
            min(30, 180 / 10) +  # Time score: 18 points
            (85 / 100) * 20 +    # Scroll score: 17 points
            min(30, 2 * 10 + 1 * 5 + 3 * 2 + 2 * 1)  # Interaction score: 30 points (capped)
        )  # Total: 65 points
        
        calculated_score = engagement.calculate_engagement_score()
        self.assertEqual(calculated_score, expected_score)
    
    def test_conversion_rate_calculation(self):
        """Test conversion rate calculation accuracy"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create 10 page views
        for i in range(10):
            AnalyticsService.track_page_view(
                request=request,
                url=f'/tournaments/{self.tournament.slug}/'
            )
        
        # Create 3 conversions
        for i in range(3):
            AnalyticsService.track_conversion(
                event_type='registration_completed',
                content_object=self.tournament,
                user=self.user,
                session_key=request.session.session_key
            )
        
        # Get dashboard data
        dashboard_data = AnalyticsService.get_dashboard_data(
            tournament_slug=self.tournament.slug,
            days=1
        )
        
        # Verify conversion rate calculation (3/10 = 30%)
        self.assertEqual(dashboard_data['overview']['conversion_rate'], 30.0)
        self.assertEqual(dashboard_data['overview']['total_conversions'], 3)
        self.assertEqual(dashboard_data['overview']['total_views'], 10)
    
    def test_bounce_rate_calculation(self):
        """Test bounce rate calculation accuracy"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create page views with different engagement patterns
        bounced_sessions = []
        engaged_sessions = []
        
        # Create 3 bounced sessions (< 30 seconds, < 2 clicks)
        for i in range(3):
            page_view = AnalyticsService.track_page_view(
                request=request,
                url=f'/tournaments/{self.tournament.slug}/'
            )
            
            # Update with bounced engagement
            AnalyticsService.update_engagement(
                session_key=request.session.session_key,
                engagement_data={
                    'timeOnPage': 15,  # Less than 30 seconds
                    'clicksCount': 1   # Less than 2 clicks
                }
            )
            bounced_sessions.append(page_view)
        
        # Create 2 engaged sessions
        for i in range(2):
            page_view = AnalyticsService.track_page_view(
                request=request,
                url=f'/tournaments/{self.tournament.slug}/'
            )
            
            # Update with engaged behavior
            AnalyticsService.update_engagement(
                session_key=request.session.session_key,
                engagement_data={
                    'timeOnPage': 120,  # 2 minutes
                    'clicksCount': 5    # Multiple clicks
                }
            )
            engaged_sessions.append(page_view)
        
        # Get dashboard data
        dashboard_data = AnalyticsService.get_dashboard_data(
            tournament_slug=self.tournament.slug,
            days=1
        )
        
        # Verify bounce rate calculation (3/5 = 60%)
        self.assertEqual(dashboard_data['engagement']['bounce_rate'], 60.0)


class AnalyticsPerformanceMonitoringTest(TestCase):
    """Test performance monitoring functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game'
        )
        
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.user,
            start_datetime=timezone.now() + timezone.timedelta(days=1),
            registration_start=timezone.now() - timezone.timedelta(hours=1),
            registration_end=timezone.now() + timezone.timedelta(hours=12),
            check_in_start=timezone.now() + timezone.timedelta(hours=12),
            max_participants=32,
            registration_fee=10.00
        )
        
        self.client = Client()
    
    def test_performance_metric_tracking(self):
        """Test performance metric tracking and storage"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create page view
        page_view = AnalyticsService.track_page_view(
            request=request,
            url=f'/tournaments/{self.tournament.slug}/',
            performance_data={
                'loadTime': 1200,
                'firstPaint': 600,
                'firstContentfulPaint': 800,
                'largestContentfulPaint': 1500
            }
        )
        
        # Track additional performance metrics
        metrics_data = [
            ('time_to_interactive', 2000, 'navigation_timing', 'ms'),
            ('cumulative_layout_shift', 0.05, 'core_web_vitals', 'score'),
            ('first_input_delay', 50, 'core_web_vitals', 'ms'),
            ('resource_load_time', 300, 'resource_timing', 'ms')
        ]
        
        performance_metrics = []
        for metric_name, value, metric_type, unit in metrics_data:
            metric = AnalyticsService.track_performance_metric(
                page_view=page_view,
                metric_name=metric_name,
                metric_value=value,
                metric_type=metric_type,
                metric_unit=unit
            )
            performance_metrics.append(metric)
        
        # Verify metrics were stored correctly
        self.assertEqual(len(performance_metrics), 4)
        
        for i, metric in enumerate(performance_metrics):
            expected_data = metrics_data[i]
            self.assertEqual(metric.metric_name, expected_data[0])
            self.assertEqual(metric.metric_value, expected_data[1])
            self.assertEqual(metric.metric_type, expected_data[2])
            self.assertEqual(metric.metric_unit, expected_data[3])
            self.assertEqual(metric.page_view, page_view)
    
    def test_performance_aggregation(self):
        """Test performance metrics aggregation"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create multiple page views with performance data
        load_times = [1200, 1500, 900, 1800, 1100]
        first_paints = [600, 750, 450, 900, 550]
        
        for i in range(5):
            AnalyticsService.track_page_view(
                request=request,
                url=f'/tournaments/{self.tournament.slug}/',
                performance_data={
                    'loadTime': load_times[i],
                    'firstPaint': first_paints[i]
                }
            )
        
        # Get dashboard data
        dashboard_data = AnalyticsService.get_dashboard_data(
            tournament_slug=self.tournament.slug,
            days=1
        )
        
        # Verify performance aggregations
        expected_avg_load_time = sum(load_times) / len(load_times)
        expected_avg_first_paint = sum(first_paints) / len(first_paints)
        
        self.assertEqual(dashboard_data['performance']['avg_load_time'], expected_avg_load_time)
        self.assertEqual(dashboard_data['performance']['avg_first_paint'], expected_avg_first_paint)
    
    def test_mobile_vs_desktop_performance(self):
        """Test performance tracking for mobile vs desktop"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Mock mobile user agent
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        
        # Create mobile page view
        mobile_page_view = AnalyticsService.track_page_view(
            request=request,
            url=f'/tournaments/{self.tournament.slug}/',
            performance_data={'loadTime': 2000}
        )
        
        # Mock desktop user agent
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        # Create desktop page view
        desktop_page_view = AnalyticsService.track_page_view(
            request=request,
            url=f'/tournaments/{self.tournament.slug}/',
            performance_data={'loadTime': 1200}
        )
        
        # Verify mobile detection
        self.assertTrue(mobile_page_view.is_mobile)
        self.assertFalse(desktop_page_view.is_mobile)
        
        # Verify performance metrics include device type
        mobile_metric = AnalyticsService.track_performance_metric(
            page_view=mobile_page_view,
            metric_name='test_metric',
            metric_value=100
        )
        
        desktop_metric = AnalyticsService.track_performance_metric(
            page_view=desktop_page_view,
            metric_name='test_metric',
            metric_value=80
        )
        
        self.assertTrue(mobile_metric.is_mobile)
        self.assertFalse(desktop_metric.is_mobile)


class AnalyticsErrorTrackingTest(TestCase):
    """Test error tracking functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game'
        )
        
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.user,
            start_datetime=timezone.now() + timezone.timedelta(days=1),
            registration_start=timezone.now() - timezone.timedelta(hours=1),
            registration_end=timezone.now() + timezone.timedelta(hours=12),
            check_in_start=timezone.now() + timezone.timedelta(hours=12),
            max_participants=32,
            registration_fee=10.00
        )
        
        self.client = Client()
    
    def test_error_categorization(self):
        """Test error categorization and severity assignment"""
        error_test_cases = [
            {
                'error_type': 'javascript',
                'message': 'TypeError: Cannot read property of undefined',
                'severity': 'high',
                'expected_category': 'javascript'
            },
            {
                'error_type': 'network',
                'message': 'Failed to fetch: 500 Internal Server Error',
                'severity': 'critical',
                'expected_category': 'network'
            },
            {
                'error_type': 'performance',
                'message': 'Page load time exceeded 5 seconds',
                'severity': 'medium',
                'expected_category': 'performance'
            },
            {
                'error_type': 'accessibility',
                'message': 'Missing alt text on image',
                'severity': 'low',
                'expected_category': 'accessibility'
            }
        ]
        
        error_logs = []
        for test_case in error_test_cases:
            error_log = AnalyticsService.track_error(
                error_type=test_case['error_type'],
                message=test_case['message'],
                url=f'/tournaments/{self.tournament.slug}/',
                user=self.user,
                session_key='test_session',
                severity=test_case['severity']
            )
            error_logs.append(error_log)
        
        # Verify error categorization
        for i, error_log in enumerate(error_logs):
            test_case = error_test_cases[i]
            self.assertEqual(error_log.error_type, test_case['expected_category'])
            self.assertEqual(error_log.severity, test_case['severity'])
            self.assertEqual(error_log.message, test_case['message'])
    
    def test_error_rate_calculation(self):
        """Test error rate calculation"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create 10 page views
        for i in range(10):
            AnalyticsService.track_page_view(
                request=request,
                url=f'/tournaments/{self.tournament.slug}/'
            )
        
        # Create 2 errors
        for i in range(2):
            AnalyticsService.track_error(
                error_type='javascript',
                message=f'Test error {i}',
                url=f'/tournaments/{self.tournament.slug}/',
                user=self.user,
                session_key=request.session.session_key
            )
        
        # Get dashboard data
        dashboard_data = AnalyticsService.get_dashboard_data(
            tournament_slug=self.tournament.slug,
            days=1
        )
        
        # Verify error rate calculation (2/10 = 20%)
        self.assertEqual(dashboard_data['overview']['error_rate'], 20.0)
        self.assertEqual(dashboard_data['overview']['error_count'], 2)
    
    def test_error_metadata_storage(self):
        """Test error metadata storage and retrieval"""
        metadata = {
            'browser': 'Chrome',
            'version': '91.0.4472.124',
            'viewport': {'width': 1920, 'height': 1080},
            'stack_trace_lines': 15
        }
        
        error_log = AnalyticsService.track_error(
            error_type='javascript',
            message='Test error with metadata',
            url=f'/tournaments/{self.tournament.slug}/',
            user=self.user,
            session_key='test_session',
            stack_trace='Error\n    at function1\n    at function2',
            file_name='tournament-detail.js',
            line_number=42,
            column_number=15,
            metadata=metadata
        )
        
        # Verify metadata storage
        self.assertEqual(error_log.metadata, metadata)
        self.assertEqual(error_log.file_name, 'tournament-detail.js')
        self.assertEqual(error_log.line_number, 42)
        self.assertEqual(error_log.column_number, 15)
        self.assertIn('function1', error_log.stack_trace)


class AnalyticsDataAccuracyTest(TestCase):
    """Test data accuracy and integrity"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game'
        )
        
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.user,
            start_datetime=timezone.now() + timezone.timedelta(days=1),
            registration_start=timezone.now() - timezone.timedelta(hours=1),
            registration_end=timezone.now() + timezone.timedelta(hours=12),
            check_in_start=timezone.now() + timezone.timedelta(hours=12),
            max_participants=32,
            registration_fee=10.00
        )
        
        self.client = Client()
    
    def test_data_consistency_across_models(self):
        """Test data consistency across related analytics models"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create page view
        page_view = AnalyticsService.track_page_view(
            request=request,
            url=f'/tournaments/{self.tournament.slug}/'
        )
        
        # Update engagement
        engagement = AnalyticsService.update_engagement(
            session_key=request.session.session_key,
            engagement_data={'timeOnPage': 120, 'clicksCount': 5}
        )
        
        # Track conversion
        conversion = AnalyticsService.track_conversion(
            event_type='registration_completed',
            content_object=self.tournament,
            user=self.user,
            session_key=request.session.session_key
        )
        
        # Track performance metric
        performance_metric = AnalyticsService.track_performance_metric(
            page_view=page_view,
            metric_name='test_metric',
            metric_value=100
        )
        
        # Verify relationships
        self.assertEqual(engagement.page_view, page_view)
        self.assertEqual(conversion.page_view, page_view)
        self.assertEqual(performance_metric.page_view, page_view)
        
        # Verify conversion marked engagement as converted
        engagement.refresh_from_db()
        self.assertTrue(engagement.converted)
    
    def test_summary_report_accuracy(self):
        """Test analytics summary report generation accuracy"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create test data for yesterday
        yesterday = timezone.now() - timedelta(days=1)
        
        # Mock the creation time to be yesterday
        with patch('django.utils.timezone.now', return_value=yesterday):
            # Create 5 page views
            page_views = []
            for i in range(5):
                page_view = AnalyticsService.track_page_view(
                    request=request,
                    url=f'/tournaments/{self.tournament.slug}/',
                    performance_data={'loadTime': 1000 + i * 100}
                )
                page_views.append(page_view)
            
            # Create 2 conversions
            for i in range(2):
                AnalyticsService.track_conversion(
                    event_type='registration_completed',
                    content_object=self.tournament,
                    user=self.user,
                    session_key=request.session.session_key
                )
            
            # Create 1 error
            AnalyticsService.track_error(
                error_type='javascript',
                message='Test error',
                url=f'/tournaments/{self.tournament.slug}/',
                user=self.user,
                session_key=request.session.session_key
            )
        
        # Generate daily summary
        AnalyticsService.generate_summary_report('daily')
        
        # Verify summary was created
        summary = AnalyticsSummary.objects.filter(period_type='daily').first()
        self.assertIsNotNone(summary)
        
        # Verify summary accuracy
        self.assertEqual(summary.total_page_views, 5)
        self.assertEqual(summary.total_conversions, 2)
        self.assertEqual(summary.total_errors, 1)
        self.assertEqual(summary.conversion_rate, 0.4)  # 2/5
        self.assertEqual(summary.error_rate, 0.2)  # 1/5
        
        # Verify average load time
        expected_avg_load_time = (1000 + 1100 + 1200 + 1300 + 1400) / 5
        self.assertEqual(summary.avg_load_time, expected_avg_load_time)
    
    def test_unique_visitor_counting(self):
        """Test unique visitor counting accuracy"""
        # Create multiple sessions for same user
        sessions = []
        for i in range(3):
            session = self.client.session
            session.create()
            sessions.append(session.session_key)
        
        # Create page views with different sessions
        for session_key in sessions:
            request = self.client.get('/').wsgi_request
            request.user = self.user
            # Create a new session object with the session key
            from django.contrib.sessions.backends.db import SessionStore
            session = SessionStore(session_key=session_key)
            session.save()
            request.session = session
            
            AnalyticsService.track_page_view(
                request=request,
                url=f'/tournaments/{self.tournament.slug}/'
            )
        
        # Get dashboard data
        dashboard_data = AnalyticsService.get_dashboard_data(
            tournament_slug=self.tournament.slug,
            days=1
        )
        
        # Verify counts
        self.assertEqual(dashboard_data['overview']['total_views'], 3)
        self.assertEqual(dashboard_data['overview']['unique_visitors'], 3)
    
    def test_time_range_filtering(self):
        """Test time range filtering accuracy"""
        request = self.client.get('/').wsgi_request
        request.user = self.user
        request.session.create()
        
        # Create data for different time periods
        now = timezone.now()
        
        # Data from 2 days ago (should not be included in 1-day filter)
        with patch('django.utils.timezone.now', return_value=now - timedelta(days=2)):
            AnalyticsService.track_page_view(
                request=request,
                url=f'/tournaments/{self.tournament.slug}/'
            )
        
        # Data from today (should be included)
        AnalyticsService.track_page_view(
            request=request,
            url=f'/tournaments/{self.tournament.slug}/'
        )
        
        # Get dashboard data for 1 day
        dashboard_data = AnalyticsService.get_dashboard_data(
            tournament_slug=self.tournament.slug,
            days=1
        )
        
        # Should only include today's data
        self.assertEqual(dashboard_data['overview']['total_views'], 1)
        
        # Get dashboard data for 7 days
        dashboard_data_7_days = AnalyticsService.get_dashboard_data(
            tournament_slug=self.tournament.slug,
            days=7
        )
        
        # Should include both data points
        self.assertEqual(dashboard_data_7_days['overview']['total_views'], 2)