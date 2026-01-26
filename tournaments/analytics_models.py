"""
Analytics and monitoring models for tournament detail pages.
Tracks page performance, user engagement, and conversion metrics.
"""

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import User
import uuid
import json


class PageView(models.Model):
    """Track page views and performance metrics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Page information
    url = models.URLField(max_length=500)
    page_type = models.CharField(max_length=50, default='tournament_detail')
    
    # User information (optional for anonymous users)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, db_index=True)
    
    # Performance metrics (in milliseconds)
    load_time = models.PositiveIntegerField(null=True, blank=True, help_text="Total page load time in ms")
    dom_content_loaded = models.PositiveIntegerField(null=True, blank=True, help_text="DOM content loaded time in ms")
    first_paint = models.PositiveIntegerField(null=True, blank=True, help_text="First paint time in ms")
    first_contentful_paint = models.PositiveIntegerField(null=True, blank=True, help_text="First contentful paint time in ms")
    largest_contentful_paint = models.PositiveIntegerField(null=True, blank=True, help_text="Largest contentful paint time in ms")
    
    # Browser and device information
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referrer = models.URLField(max_length=500, blank=True)
    
    # Device information
    screen_width = models.PositiveIntegerField(null=True, blank=True)
    screen_height = models.PositiveIntegerField(null=True, blank=True)
    viewport_width = models.PositiveIntegerField(null=True, blank=True)
    viewport_height = models.PositiveIntegerField(null=True, blank=True)
    is_mobile = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_page_views'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['page_type', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_key', '-created_at']),
            models.Index(fields=['is_mobile', '-created_at']),
        ]
    
    def __str__(self):
        return f"PageView {self.url} at {self.created_at}"


class UserEngagement(models.Model):
    """Track user engagement metrics on pages"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Related page view
    page_view = models.OneToOneField(PageView, on_delete=models.CASCADE, related_name='engagement')
    
    # Engagement metrics
    time_on_page = models.PositiveIntegerField(null=True, blank=True, help_text="Time spent on page in seconds")
    scroll_depth = models.PositiveIntegerField(default=0, help_text="Maximum scroll depth as percentage (0-100)")
    clicks_count = models.PositiveIntegerField(default=0, help_text="Total number of clicks")
    
    # Specific interactions
    registration_button_clicks = models.PositiveIntegerField(default=0)
    share_button_clicks = models.PositiveIntegerField(default=0)
    tab_switches = models.PositiveIntegerField(default=0)
    participant_card_clicks = models.PositiveIntegerField(default=0)
    bracket_preview_clicks = models.PositiveIntegerField(default=0)
    
    # Engagement quality indicators
    bounced = models.BooleanField(default=False, help_text="User left without meaningful interaction")
    converted = models.BooleanField(default=False, help_text="User completed registration")
    
    # Timestamps
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_user_engagement'
        ordering = ['-session_start']
        indexes = [
            models.Index(fields=['converted', '-session_start']),
            models.Index(fields=['bounced', '-session_start']),
        ]
    
    def __str__(self):
        return f"Engagement for {self.page_view.url}"
    
    def calculate_engagement_score(self):
        """Calculate engagement score based on various metrics"""
        score = 0
        
        # Time on page (max 30 points)
        if self.time_on_page:
            score += min(30, self.time_on_page / 10)  # 1 point per 10 seconds, max 30
        
        # Scroll depth (max 20 points)
        score += (self.scroll_depth / 100) * 20
        
        # Interactions (max 30 points)
        interaction_score = (
            self.registration_button_clicks * 10 +
            self.share_button_clicks * 5 +
            self.tab_switches * 2 +
            self.participant_card_clicks * 1 +
            self.bracket_preview_clicks * 3
        )
        score += min(30, interaction_score)
        
        # Conversion bonus (20 points)
        if self.converted:
            score += 20
        
        return min(100, score)


class ConversionEvent(models.Model):
    """Track conversion events (registrations, payments, etc.)"""
    
    EVENT_TYPES = [
        ('registration_started', 'Registration Started'),
        ('registration_completed', 'Registration Completed'),
        ('payment_started', 'Payment Started'),
        ('payment_completed', 'Payment Completed'),
        ('share_completed', 'Share Completed'),
        ('email_signup', 'Email Signup'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Event information
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    
    # Related objects
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, db_index=True)
    
    # Conversion funnel tracking
    page_view = models.ForeignKey(PageView, on_delete=models.SET_NULL, null=True, blank=True)
    referrer_url = models.URLField(max_length=500, blank=True)
    
    # Event metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_conversion_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_key', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.content_object}"


class ErrorLog(models.Model):
    """Track JavaScript errors and performance issues"""
    
    ERROR_TYPES = [
        ('javascript', 'JavaScript Error'),
        ('network', 'Network Error'),
        ('performance', 'Performance Issue'),
        ('accessibility', 'Accessibility Issue'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Error information
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    
    # Error details
    message = models.TextField()
    stack_trace = models.TextField(blank=True)
    file_name = models.CharField(max_length=500, blank=True)
    line_number = models.PositiveIntegerField(null=True, blank=True)
    column_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Context information
    url = models.URLField(max_length=500)
    user_agent = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, db_index=True)
    
    # Additional context
    page_view = models.ForeignKey(PageView, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_error_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['error_type', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['is_resolved', '-created_at']),
            models.Index(fields=['url', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.error_type} - {self.message[:50]}"


class PerformanceMetric(models.Model):
    """Track detailed performance metrics"""
    
    METRIC_TYPES = [
        ('core_web_vitals', 'Core Web Vitals'),
        ('resource_timing', 'Resource Timing'),
        ('user_timing', 'User Timing'),
        ('navigation_timing', 'Navigation Timing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Metric information
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20, default='ms')
    
    # Context
    page_view = models.ForeignKey(PageView, on_delete=models.CASCADE, related_name='performance_metrics')
    url = models.URLField(max_length=500)
    
    # Device and browser context
    is_mobile = models.BooleanField(default=False)
    connection_type = models.CharField(max_length=20, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_performance_metrics'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['metric_type', 'metric_name', '-created_at']),
            models.Index(fields=['page_view', 'metric_name']),
            models.Index(fields=['is_mobile', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}{self.metric_unit}"


class AnalyticsSummary(models.Model):
    """Daily/hourly aggregated analytics data for dashboard"""
    
    AGGREGATION_PERIODS = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time period
    period_type = models.CharField(max_length=10, choices=AGGREGATION_PERIODS)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Page metrics
    total_page_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    avg_load_time = models.FloatField(null=True, blank=True)
    avg_time_on_page = models.FloatField(null=True, blank=True)
    
    # Engagement metrics
    total_clicks = models.PositiveIntegerField(default=0)
    avg_scroll_depth = models.FloatField(null=True, blank=True)
    bounce_rate = models.FloatField(null=True, blank=True)
    
    # Conversion metrics
    total_conversions = models.PositiveIntegerField(default=0)
    conversion_rate = models.FloatField(null=True, blank=True)
    
    # Performance metrics
    avg_first_paint = models.FloatField(null=True, blank=True)
    avg_largest_contentful_paint = models.FloatField(null=True, blank=True)
    
    # Error metrics
    total_errors = models.PositiveIntegerField(default=0)
    error_rate = models.FloatField(null=True, blank=True)
    
    # Device breakdown
    mobile_percentage = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_summary'
        ordering = ['-period_start']
        unique_together = ['period_type', 'period_start']
        indexes = [
            models.Index(fields=['period_type', '-period_start']),
            models.Index(fields=['-period_start']),
        ]
    
    def __str__(self):
        return f"{self.period_type} summary for {self.period_start.date()}"