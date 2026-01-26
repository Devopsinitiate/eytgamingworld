"""
API views for analytics data collection.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from .analytics_service import AnalyticsService
from .analytics_models import PageView
from .models import Tournament

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@csrf_exempt
def track_page_performance(request):
    """
    Track page load performance metrics
    
    Expected POST data:
    {
        "url": "string",
        "loadTime": number,
        "domContentLoaded": number,
        "firstPaint": number,
        "firstContentfulPaint": number,
        "largestContentfulPaint": number,
        "screenWidth": number,
        "screenHeight": number,
        "viewportWidth": number,
        "viewportHeight": number
    }
    """
    try:
        data = json.loads(request.body)
        url = data.get('url', request.META.get('HTTP_REFERER', ''))
        
        # Track page view with performance data
        page_view = AnalyticsService.track_page_view(
            request=request,
            url=url,
            performance_data=data
        )
        
        return JsonResponse({
            'success': True,
            'page_view_id': str(page_view.id)
        })
        
    except Exception as e:
        logger.error(f"Error tracking page performance: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def track_engagement(request):
    """
    Track user engagement metrics
    
    Expected POST data:
    {
        "timeOnPage": number (seconds),
        "scrollDepth": number (0-100),
        "clicksCount": number,
        "registrationButtonClicks": number,
        "shareButtonClicks": number,
        "tabSwitches": number,
        "participantCardClicks": number,
        "bracketPreviewClicks": number
    }
    """
    try:
        data = json.loads(request.body)
        session_key = request.session.session_key
        
        if not session_key:
            return JsonResponse({
                'success': False,
                'error': 'No session key found'
            }, status=400)
        
        # Update engagement metrics
        engagement = AnalyticsService.update_engagement(
            session_key=session_key,
            engagement_data=data
        )
        
        if engagement:
            return JsonResponse({
                'success': True,
                'engagement_score': engagement.calculate_engagement_score()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No page view found for session'
            }, status=404)
        
    except Exception as e:
        logger.error(f"Error tracking engagement: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def track_conversion(request):
    """
    Track conversion events
    
    Expected POST data:
    {
        "eventType": "registration_started|registration_completed|payment_started|payment_completed|share_completed",
        "tournamentSlug": "string",
        "metadata": {}
    }
    """
    try:
        data = json.loads(request.body)
        event_type = data.get('eventType')
        tournament_slug = data.get('tournamentSlug')
        metadata = data.get('metadata', {})
        
        if not event_type or not tournament_slug:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        # Get tournament
        try:
            tournament = Tournament.objects.get(slug=tournament_slug)
        except Tournament.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Tournament not found'
            }, status=404)
        
        # Track conversion
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        
        conversion = AnalyticsService.track_conversion(
            event_type=event_type,
            content_object=tournament,
            user=user,
            session_key=session_key,
            metadata=metadata
        )
        
        return JsonResponse({
            'success': True,
            'conversion_id': str(conversion.id)
        })
        
    except Exception as e:
        logger.error(f"Error tracking conversion: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def track_error(request):
    """
    Track JavaScript errors
    
    Expected POST data:
    {
        "errorType": "javascript|network|performance|accessibility",
        "message": "string",
        "stackTrace": "string",
        "fileName": "string",
        "lineNumber": number,
        "columnNumber": number,
        "severity": "low|medium|high|critical",
        "metadata": {}
    }
    """
    try:
        data = json.loads(request.body)
        error_type = data.get('errorType', 'javascript')
        message = data.get('message', '')
        url = data.get('url', request.META.get('HTTP_REFERER', ''))
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'Missing error message'
            }, status=400)
        
        # Track error
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        error_log = AnalyticsService.track_error(
            error_type=error_type,
            message=message,
            url=url,
            user=user,
            session_key=session_key,
            stack_trace=data.get('stackTrace', ''),
            file_name=data.get('fileName', ''),
            line_number=data.get('lineNumber'),
            column_number=data.get('columnNumber'),
            user_agent=user_agent,
            severity=data.get('severity', 'medium'),
            metadata=data.get('metadata', {})
        )
        
        return JsonResponse({
            'success': True,
            'error_id': str(error_log.id)
        })
        
    except Exception as e:
        logger.error(f"Error tracking error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def track_performance_metric(request):
    """
    Track custom performance metrics
    
    Expected POST data:
    {
        "metricName": "string",
        "metricValue": number,
        "metricType": "core_web_vitals|resource_timing|user_timing|navigation_timing",
        "metricUnit": "ms|s|bytes",
        "metadata": {}
    }
    """
    try:
        data = json.loads(request.body)
        metric_name = data.get('metricName')
        metric_value = data.get('metricValue')
        
        if not metric_name or metric_value is None:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        # Find the most recent page view for this session
        session_key = request.session.session_key
        if not session_key:
            return JsonResponse({
                'success': False,
                'error': 'No session key found'
            }, status=400)
        
        page_view = PageView.objects.filter(
            session_key=session_key
        ).order_by('-created_at').first()
        
        if not page_view:
            return JsonResponse({
                'success': False,
                'error': 'No page view found for session'
            }, status=404)
        
        # Track performance metric
        performance_metric = AnalyticsService.track_performance_metric(
            page_view=page_view,
            metric_name=metric_name,
            metric_value=float(metric_value),
            metric_type=data.get('metricType', 'user_timing'),
            metric_unit=data.get('metricUnit', 'ms'),
            metadata=data.get('metadata', {})
        )
        
        return JsonResponse({
            'success': True,
            'metric_id': str(performance_metric.id)
        })
        
    except Exception as e:
        logger.error(f"Error tracking performance metric: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def track_page_view(request, slug):
    """
    Track page view for a specific tournament
    
    Expected POST data:
    {
        "referrer": "string",
        "user_agent": "string",
        "timestamp": "string",
        "metadata": {}
    }
    """
    try:
        # Get tournament
        try:
            tournament = Tournament.objects.get(slug=slug)
        except Tournament.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Tournament not found'
            }, status=404)
        
        # Parse request data
        data = {}
        if request.body:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                pass
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        # Track page view using AnalyticsService
        page_view = AnalyticsService.track_page_view(
            request=request,
            url=request.build_absolute_uri(),
            performance_data=data.get('performance_data')
        )
        
        return JsonResponse({
            'success': True,
            'page_view_id': str(page_view.id) if page_view else None
        })
        
    except Exception as e:
        logger.error(f"Error tracking page view for tournament {slug}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
def get_analytics_dashboard(request, tournament_slug=None):
    """
    Get analytics dashboard data
    
    Query parameters:
    - days: Number of days to include (default: 7)
    """
    try:
        # Check if user has permission to view analytics
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        
        # If tournament slug is provided, check if user is organizer
        if tournament_slug:
            try:
                tournament = Tournament.objects.get(slug=tournament_slug)
                if tournament.organizer != request.user and not request.user.is_staff:
                    return JsonResponse({
                        'success': False,
                        'error': 'Permission denied'
                    }, status=403)
            except Tournament.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Tournament not found'
                }, status=404)
        elif not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        
        # Get dashboard data
        days = int(request.GET.get('days', 7))
        dashboard_data = AnalyticsService.get_dashboard_data(
            tournament_slug=tournament_slug,
            days=days
        )
        
        return JsonResponse({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)