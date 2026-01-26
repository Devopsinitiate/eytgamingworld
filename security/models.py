"""
Security and audit models for EYTGaming platform.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class AuditLog(models.Model):
    """
    Track important user actions for security and compliance.
    Provides audit trail for GDPR/CCPA compliance.
    """
    
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Data Export'),
        ('payment', 'Payment'),
        ('admin_action', 'Admin Action'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User Information
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    username = models.CharField(max_length=150, blank=True, help_text="Cached username")
    
    # Action Details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    # Request Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Metadata
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='low')
    details = models.JSONField(default=dict, blank=True, help_text="Additional context")
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        user_str = self.username or f"User {self.user_id}" if self.user_id else "Anonymous"
        return f"{user_str} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def log_action(cls, user, action, model_name='', object_id='', description='', 
                   severity='low', ip_address=None, user_agent='', request_path='', 
                   request_method='', details=None):
        """
        Convenience method to create audit log entries.
        
        Usage:
            AuditLog.log_action(
                user=request.user,
                action='create',
                model_name='Tournament',
                object_id=str(tournament.id),
                description='Created new tournament',
                ip_address=get_client_ip(request)
            )
        """
        return cls.objects.create(
            user=user,
            username=user.username if user else '',
            action=action,
            model_name=model_name,
            object_id=object_id,
            description=description,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else '',
            request_path=request_path[:500] if request_path else '',
            request_method=request_method,
            details=details or {}
        )


class SecurityEvent(models.Model):
    """
    Track security-related events (failed logins, suspicious activity, etc.)
    """
    
    EVENT_TYPE_CHOICES = [
        ('failed_login', 'Failed Login'),
        ('account_locked', 'Account Locked'),
        ('password_reset', 'Password Reset'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('unauthorized_access', 'Unauthorized Access'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Event Details
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    description = models.TextField()
    
    # User (if applicable)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_events'
    )
    
    # Request Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_events'
    )
    
    # Timestamp
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'security_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['resolved', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
