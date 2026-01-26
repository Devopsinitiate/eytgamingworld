"""
Analytics service for tournament detail pages.
Handles data collection, processing, and dashboard generation.
"""

from django.db import models, transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg, Count, Sum, F, Q
from django.core.cache import cache
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional, Any

from .analytics_models import (
    PageView, UserEngagement, ConversionEvent, 
    ErrorLog, PerformanceMetric, AnalyticsSummary
)
from .models import Tournament, Participant

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for handling analytics data collection and processing"""
    
    @staticmethod
    def track_page_view(request, url: str, performance_data: Optional[Dict] = None) -> PageView:
        """
        Track a page view with performance metrics
        
        Args:
            request: Django request object
            url: Page URL
            performance_data: Optional performance timing data
            
        Returns:
            PageView instance
        """
        try:
            # Extract user information
            user = request.user if request.user.is_authenticated else None
            session_key = request.session.session_key or request.session.create()
            
            # Extract device information
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = AnalyticsService._get_client_ip(request)
            referrer = request.META.get('HTTP_REFERER', '')
            
            # Detect mobile device
            is_mobile = AnalyticsService._is_mobile_device(user_agent)
            
            # Create page view record
            page_view_data = {
                'url': url,
                'page_type': 'tournament_detail',
                'user': user,
                'session_key': session_key,
                'user_agent': user_agent,
                'ip_address': ip_address,
                'referrer': referrer,
                'is_mobile': is_mobile,
            }
            
            # Add performance data if provided
            if performance_data:
                page_view_data.update({
                    'load_time': performance_data.get('loadTime'),
                    'dom_content_loaded': performance_data.get('domContentLoaded'),
                    'first_paint': performance_data.get('firstPaint'),
                    'first_contentful_paint': performance_data.get('firstContentfulPaint'),
                    'largest_contentful_paint': performance_data.get('largestContentfulPaint'),
                    'screen_width': performance_data.get('screenWidth'),
                    'screen_height': performance_data.get('screenHeight'),
                    'viewport_width': performance_data.get('viewportWidth'),
                    'viewport_height': performance_data.get('viewportHeight'),
                })
            
            page_view = PageView.objects.create(**page_view_data)
            
            # Create initial engagement record
            UserEngagement.objects.create(page_view=page_view)
            
            logger.info(f"Page view tracked: {url} for user {user}")
            return page_view
            
        except Exception as e:
            logger.error(f"Error tracking page view: {e}")
            raise
    
    @staticmethod
    def update_engagement(session_key: str, engagement_data: Dict) -> Optional[UserEngagement]:
        """
        Update user engagement metrics
        
        Args:
            session_key: User session key
            engagement_data: Dictionary containing engagement metrics
            
        Returns:
            Updated UserEngagement instance or None
        """
        try:
            # Find the most recent page view for this session
            page_view = PageView.objects.filter(
                session_key=session_key
            ).order_by('-created_at').first()
            
            if not page_view:
                logger.warning(f"No page view found for session {session_key}")
                return None
            
            engagement = page_view.engagement
            
            # Update engagement metrics
            if 'timeOnPage' in engagement_data:
                engagement.time_on_page = engagement_data['timeOnPage']
            
            if 'scrollDepth' in engagement_data:
                engagement.scroll_depth = max(engagement.scroll_depth, engagement_data['scrollDepth'])
            
            if 'clicksCount' in engagement_data:
                engagement.clicks_count = engagement_data['clicksCount']
            
            # Update specific interaction counts
            interaction_fields = [
                'registrationButtonClicks', 'shareButtonClicks', 'tabSwitches',
                'participantCardClicks', 'bracketPreviewClicks'
            ]
            
            for field in interaction_fields:
                if field in engagement_data:
                    snake_case_field = AnalyticsService._camel_to_snake(field)
                    setattr(engagement, snake_case_field, engagement_data[field])
            
            # Update session end time
            engagement.session_end = timezone.now()
            
            # Calculate if user bounced (less than 30 seconds and minimal interaction)
            if engagement.time_on_page and engagement.time_on_page < 30 and engagement.clicks_count < 2:
                engagement.bounced = True
            
            engagement.save()
            
            logger.info(f"Engagement updated for session {session_key}")
            return engagement
            
        except Exception as e:
            logger.error(f"Error updating engagement: {e}")
            return None
    
    @staticmethod
    def track_conversion(event_type: str, content_object: Any, user=None, 
                        session_key: str = None, metadata: Dict = None) -> ConversionEvent:
        """
        Track a conversion event
        
        Args:
            event_type: Type of conversion event
            content_object: Related object (Tournament, etc.)
            user: User who performed the action
            session_key: Session key
            metadata: Additional event data
            
        Returns:
            ConversionEvent instance
        """
        try:
            content_type = ContentType.objects.get_for_model(content_object)
            
            # Find related page view
            page_view = None
            if session_key:
                page_view = PageView.objects.filter(
                    session_key=session_key
                ).order_by('-created_at').first()
            
            conversion = ConversionEvent.objects.create(
                event_type=event_type,
                content_type=content_type,
                object_id=str(content_object.pk),
                user=user,
                session_key=session_key,
                page_view=page_view,
                metadata=metadata or {}
            )
            
            # Mark engagement as converted if it's a registration
            if event_type == 'registration_completed' and page_view:
                try:
                    engagement = page_view.engagement
                    engagement.converted = True
                    engagement.save()
                except UserEngagement.DoesNotExist:
                    pass
            
            logger.info(f"Conversion tracked: {event_type} for {content_object}")
            return conversion
            
        except Exception as e:
            logger.error(f"Error tracking conversion: {e}")
            raise
    
    @staticmethod
    def track_error(error_type: str, message: str, url: str, user=None, 
                   session_key: str = None, **kwargs) -> ErrorLog:
        """
        Track an error event
        
        Args:
            error_type: Type of error
            message: Error message
            url: URL where error occurred
            user: User who encountered the error
            session_key: Session key
            **kwargs: Additional error details
            
        Returns:
            ErrorLog instance
        """
        try:
            # Find related page view
            page_view = None
            if session_key:
                page_view = PageView.objects.filter(
                    session_key=session_key,
                    url=url
                ).order_by('-created_at').first()
            
            error_log = ErrorLog.objects.create(
                error_type=error_type,
                message=message,
                url=url,
                user=user,
                session_key=session_key,
                page_view=page_view,
                stack_trace=kwargs.get('stack_trace', ''),
                file_name=kwargs.get('file_name', ''),
                line_number=kwargs.get('line_number'),
                column_number=kwargs.get('column_number'),
                user_agent=kwargs.get('user_agent', ''),
                severity=kwargs.get('severity', 'medium'),
                metadata=kwargs.get('metadata', {})
            )
            
            logger.error(f"Error tracked: {error_type} - {message}")
            return error_log
            
        except Exception as e:
            logger.error(f"Error tracking error log: {e}")
            raise
    
    @staticmethod
    def track_performance_metric(page_view: PageView, metric_name: str, 
                               metric_value: float, metric_type: str = 'user_timing',
                               metric_unit: str = 'ms', metadata: Dict = None) -> PerformanceMetric:
        """
        Track a performance metric
        
        Args:
            page_view: Related PageView instance
            metric_name: Name of the metric
            metric_value: Metric value
            metric_type: Type of metric
            metric_unit: Unit of measurement
            metadata: Additional metric data
            
        Returns:
            PerformanceMetric instance
        """
        try:
            performance_metric = PerformanceMetric.objects.create(
                metric_type=metric_type,
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                page_view=page_view,
                url=page_view.url,
                is_mobile=page_view.is_mobile,
                metadata=metadata or {}
            )
            
            logger.info(f"Performance metric tracked: {metric_name} = {metric_value}{metric_unit}")
            return performance_metric
            
        except Exception as e:
            logger.error(f"Error tracking performance metric: {e}")
            raise
    
    @staticmethod
    def get_dashboard_data(tournament_slug: str = None, days: int = 7) -> Dict:
        """
        Get analytics dashboard data
        
        Args:
            tournament_slug: Optional tournament slug to filter by
            days: Number of days to include in analysis
            
        Returns:
            Dictionary containing dashboard metrics
        """
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Base queryset
            page_views_qs = PageView.objects.filter(
                created_at__gte=start_date,
                page_type='tournament_detail'
            )
            
            # Filter by tournament if specified
            if tournament_slug:
                page_views_qs = page_views_qs.filter(url__contains=tournament_slug)
            
            # Basic metrics
            total_views = page_views_qs.count()
            unique_visitors = page_views_qs.values('session_key').distinct().count()
            
            # Performance metrics
            performance_metrics = page_views_qs.aggregate(
                avg_load_time=Avg('load_time'),
                avg_first_paint=Avg('first_paint'),
                avg_largest_contentful_paint=Avg('largest_contentful_paint')
            )
            
            # Engagement metrics
            engagement_metrics = UserEngagement.objects.filter(
                page_view__in=page_views_qs
            ).aggregate(
                avg_time_on_page=Avg('time_on_page'),
                avg_scroll_depth=Avg('scroll_depth'),
                total_clicks=Sum('clicks_count'),
                bounce_rate=Avg(models.Case(
                    models.When(bounced=True, then=1),
                    default=0,
                    output_field=models.FloatField()
                )) * 100
            )
            
            # Conversion metrics
            conversions = ConversionEvent.objects.filter(
                created_at__gte=start_date,
                event_type='registration_completed'
            )
            
            if tournament_slug:
                tournament_ct = ContentType.objects.get_for_model(Tournament)
                tournament = Tournament.objects.filter(slug=tournament_slug).first()
                if tournament:
                    conversions = conversions.filter(
                        content_type=tournament_ct,
                        object_id=str(tournament.pk)
                    )
            
            total_conversions = conversions.count()
            conversion_rate = (total_conversions / total_views * 100) if total_views > 0 else 0
            
            # Error metrics
            error_count = ErrorLog.objects.filter(
                created_at__gte=start_date
            ).count()
            error_rate = (error_count / total_views * 100) if total_views > 0 else 0
            
            # Device breakdown
            mobile_views = page_views_qs.filter(is_mobile=True).count()
            mobile_percentage = (mobile_views / total_views * 100) if total_views > 0 else 0
            
            # Daily breakdown
            daily_data = []
            for i in range(days):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                day_views = page_views_qs.filter(
                    created_at__gte=day_start,
                    created_at__lt=day_end
                ).count()
                
                day_conversions = conversions.filter(
                    created_at__gte=day_start,
                    created_at__lt=day_end
                ).count()
                
                daily_data.append({
                    'date': day_start.date().isoformat(),
                    'views': day_views,
                    'conversions': day_conversions,
                    'conversion_rate': (day_conversions / day_views * 100) if day_views > 0 else 0
                })
            
            return {
                'overview': {
                    'total_views': total_views,
                    'unique_visitors': unique_visitors,
                    'total_conversions': total_conversions,
                    'conversion_rate': round(conversion_rate, 2),
                    'error_count': error_count,
                    'error_rate': round(error_rate, 2),
                    'mobile_percentage': round(mobile_percentage, 2)
                },
                'performance': {
                    'avg_load_time': round(performance_metrics['avg_load_time'] or 0, 2),
                    'avg_first_paint': round(performance_metrics['avg_first_paint'] or 0, 2),
                    'avg_largest_contentful_paint': round(performance_metrics['avg_largest_contentful_paint'] or 0, 2)
                },
                'engagement': {
                    'avg_time_on_page': round(engagement_metrics['avg_time_on_page'] or 0, 2),
                    'avg_scroll_depth': round(engagement_metrics['avg_scroll_depth'] or 0, 2),
                    'total_clicks': engagement_metrics['total_clicks'] or 0,
                    'bounce_rate': round(engagement_metrics['bounce_rate'] or 0, 2)
                },
                'daily_data': daily_data,
                'period': {
                    'start_date': start_date.date().isoformat(),
                    'end_date': end_date.date().isoformat(),
                    'days': days
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return {}
    
    @staticmethod
    def generate_summary_report(period_type: str = 'daily') -> None:
        """
        Generate aggregated analytics summary
        
        Args:
            period_type: Type of aggregation period ('hourly', 'daily', 'weekly', 'monthly')
        """
        try:
            now = timezone.now()
            
            if period_type == 'daily':
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                period_end = period_start + timedelta(days=1)
            elif period_type == 'hourly':
                period_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
                period_end = period_start + timedelta(hours=1)
            else:
                logger.warning(f"Unsupported period type: {period_type}")
                return
            
            # Check if summary already exists
            existing_summary = AnalyticsSummary.objects.filter(
                period_type=period_type,
                period_start=period_start
            ).first()
            
            if existing_summary:
                logger.info(f"Summary already exists for {period_type} period {period_start}")
                return
            
            # Generate summary data
            page_views_qs = PageView.objects.filter(
                created_at__gte=period_start,
                created_at__lt=period_end,
                page_type='tournament_detail'
            )
            
            # Calculate metrics
            total_page_views = page_views_qs.count()
            unique_visitors = page_views_qs.values('session_key').distinct().count()
            
            performance_data = page_views_qs.aggregate(
                avg_load_time=Avg('load_time'),
                avg_first_paint=Avg('first_paint'),
                avg_largest_contentful_paint=Avg('largest_contentful_paint')
            )
            
            engagement_data = UserEngagement.objects.filter(
                page_view__in=page_views_qs
            ).aggregate(
                avg_time_on_page=Avg('time_on_page'),
                total_clicks=Sum('clicks_count'),
                avg_scroll_depth=Avg('scroll_depth'),
                bounce_rate=Avg(models.Case(
                    models.When(bounced=True, then=1),
                    default=0,
                    output_field=models.FloatField()
                ))
            )
            
            conversions = ConversionEvent.objects.filter(
                created_at__gte=period_start,
                created_at__lt=period_end,
                event_type='registration_completed'
            ).count()
            
            conversion_rate = (conversions / total_page_views) if total_page_views > 0 else 0
            
            errors = ErrorLog.objects.filter(
                created_at__gte=period_start,
                created_at__lt=period_end
            ).count()
            
            error_rate = (errors / total_page_views) if total_page_views > 0 else 0
            
            mobile_views = page_views_qs.filter(is_mobile=True).count()
            mobile_percentage = (mobile_views / total_page_views) if total_page_views > 0 else 0
            
            # Create summary record
            AnalyticsSummary.objects.create(
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                total_page_views=total_page_views,
                unique_visitors=unique_visitors,
                avg_load_time=performance_data['avg_load_time'],
                avg_time_on_page=engagement_data['avg_time_on_page'],
                total_clicks=engagement_data['total_clicks'] or 0,
                avg_scroll_depth=engagement_data['avg_scroll_depth'],
                bounce_rate=engagement_data['bounce_rate'],
                total_conversions=conversions,
                conversion_rate=conversion_rate,
                avg_first_paint=performance_data['avg_first_paint'],
                avg_largest_contentful_paint=performance_data['avg_largest_contentful_paint'],
                total_errors=errors,
                error_rate=error_rate,
                mobile_percentage=mobile_percentage
            )
            
            logger.info(f"Generated {period_type} summary for {period_start}")
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
    
    @staticmethod
    def _get_client_ip(request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def _is_mobile_device(user_agent: str) -> bool:
        """Detect if user agent is from a mobile device"""
        mobile_keywords = [
            'Mobile', 'Android', 'iPhone', 'iPad', 'iPod', 
            'BlackBerry', 'Windows Phone', 'Opera Mini'
        ]
        return any(keyword in user_agent for keyword in mobile_keywords)
    
    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """Convert camelCase to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()