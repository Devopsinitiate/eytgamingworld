from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

User = get_user_model()


class Notification(models.Model):
    """User notifications for various events"""
    
    TYPE_CHOICES = [
        ('tournament', 'Tournament Update'),
        ('coaching', 'Coaching Session'),
        ('team', 'Team Activity'),
        ('payment', 'Payment'),
        ('system', 'System Notification'),
        ('security', 'Security Alert'),
        ('venue', 'Venue Booking'),
        ('match', 'Match Update'),
        ('message', 'Direct Message'),
        ('achievement', 'Achievement Unlocked'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('sms', 'SMS'),
        ('discord', 'Discord Webhook'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        help_text="User who will receive this notification"
    )
    
    # Content
    title = models.CharField(
        max_length=200,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Notification message content"
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        help_text="Type of notification"
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='normal'
    )
    
    # Related object (generic foreign key)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    object_id = models.CharField(max_length=100, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Action URL
    action_url = models.CharField(
        max_length=500, 
        blank=True,
        help_text="URL to navigate to when notification is clicked"
    )
    
    # Status
    read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    read_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the notification was read"
    )
    
    # Delivery tracking
    delivery_methods = models.JSONField(
        default=list,
        help_text="List of delivery methods used (e.g., ['in_app', 'email'])"
    )
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    push_sent = models.BooleanField(default=False)
    push_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional notification data"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this notification expires"
    )
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type='system',
                          priority='normal', content_object=None, action_url='',
                          delivery_methods=None, **metadata):
        """Convenience method to create notifications"""
        
        # Get content type and object id if content_object provided
        content_type = None
        object_id = ""
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = str(content_object.pk)
        
        notification = cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            content_type=content_type,
            object_id=object_id,
            action_url=action_url,
            delivery_methods=delivery_methods or ['in_app'],
            metadata=metadata
        )
        
        # Trigger delivery based on methods
        if 'email' in notification.delivery_methods:
            notification.send_email()
        if 'push' in notification.delivery_methods:
            notification.send_push()
        
        return notification
    
    def send_email(self):
        """Send notification via email"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        try:
            send_mail(
                subject=self.title,
                message=self.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                fail_silently=False,
            )
            from django.utils import timezone
            self.email_sent = True
            self.email_sent_at = timezone.now()
            self.save(update_fields=['email_sent', 'email_sent_at'])
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send email notification: {e}")
    
    def send_push(self):
        """Send push notification (placeholder for future implementation)"""
        # TODO: Implement push notification logic
        from django.utils import timezone
        self.push_sent = True
        self.push_sent_at = timezone.now()
        self.save(update_fields=['push_sent', 'push_sent_at'])


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_preferences'
    )
    
    # In-app notifications
    in_app_enabled = models.BooleanField(default=True)
    
    # Email notifications
    email_enabled = models.BooleanField(default=True)
    email_tournament_updates = models.BooleanField(default=True)
    email_coaching_reminders = models.BooleanField(default=True)
    email_team_activity = models.BooleanField(default=True)
    email_payment_receipts = models.BooleanField(default=True)
    email_security_alerts = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)
    
    # Push notifications
    push_enabled = models.BooleanField(default=False)
    push_tournament_updates = models.BooleanField(default=True)
    push_coaching_reminders = models.BooleanField(default=True)
    push_team_activity = models.BooleanField(default=True)
    push_match_updates = models.BooleanField(default=True)
    
    # SMS notifications
    sms_enabled = models.BooleanField(default=False)
    sms_urgent_only = models.BooleanField(default=True)
    
    # Discord webhook
    discord_enabled = models.BooleanField(default=False)
    discord_webhook_url = models.URLField(blank=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Notification Preferences for {self.user.email}"
    
    def should_send_notification(self, notification_type, delivery_method):
        """Check if notification should be sent based on preferences"""
        
        # Check if delivery method is enabled
        if delivery_method == 'email' and not self.email_enabled:
            return False
        if delivery_method == 'push' and not self.push_enabled:
            return False
        if delivery_method == 'sms' and not self.sms_enabled:
            return False
        if delivery_method == 'discord' and not self.discord_enabled:
            return False
        
        # Check specific notification type preferences
        if delivery_method == 'email':
            type_mapping = {
                'tournament': self.email_tournament_updates,
                'coaching': self.email_coaching_reminders,
                'team': self.email_team_activity,
                'payment': self.email_payment_receipts,
                'security': self.email_security_alerts,
            }
            return type_mapping.get(notification_type, True)
        
        if delivery_method == 'push':
            type_mapping = {
                'tournament': self.push_tournament_updates,
                'coaching': self.push_coaching_reminders,
                'team': self.push_team_activity,
                'match': self.push_match_updates,
            }
            return type_mapping.get(notification_type, True)
        
        return True
    
    def is_in_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        from django.utils import timezone
        now = timezone.now().time()
        
        if self.quiet_hours_start and self.quiet_hours_end:
            if self.quiet_hours_start < self.quiet_hours_end:
                return self.quiet_hours_start <= now <= self.quiet_hours_end
            else:  # Quiet hours span midnight
                return now >= self.quiet_hours_start or now <= self.quiet_hours_end
        
        return False


class NotificationTemplate(models.Model):
    """Templates for common notification types"""
    
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Template identifier"
    )
    notification_type = models.CharField(
        max_length=20,
        help_text="Type of notification this template is for"
    )
    
    # Template content
    title_template = models.CharField(
        max_length=200,
        help_text="Title template with placeholders (e.g., 'New message from {sender}')"
    )
    message_template = models.TextField(
        help_text="Message template with placeholders"
    )
    
    # Default settings
    default_priority = models.CharField(
        max_length=10, 
        choices=Notification.PRIORITY_CHOICES, 
        default='normal'
    )
    default_delivery_methods = models.JSONField(
        default=list,
        help_text="Default delivery methods for this template"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
    
    def __str__(self):
        return self.name
    
    def render(self, context):
        """Render template with context data"""
        title = self.title_template.format(**context)
        message = self.message_template.format(**context)
        return title, message
    
    def create_notification(self, user, context, **kwargs):
        """Create notification from template"""
        title, message = self.render(context)
        
        return Notification.create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=self.notification_type,
            priority=kwargs.get('priority', self.default_priority),
            delivery_methods=kwargs.get('delivery_methods', self.default_delivery_methods),
            **kwargs
        )
