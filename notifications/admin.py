from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Notification, NotificationPreference, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'user_email', 'title', 'notification_type', 
        'priority_display', 'read_status', 'delivery_status'
    ]
    list_filter = [
        'notification_type', 'priority', 'read', 
        'email_sent', 'push_sent', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__username', 'title', 'message'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'read_at', 
        'email_sent_at', 'push_sent_at'
    ]
    fieldsets = [
        ('Recipient', {
            'fields': ('user',)
        }),
        ('Content', {
            'fields': (
                'title', 'message', 'notification_type', 
                'priority', 'action_url'
            )
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('read', 'read_at')
        }),
        ('Delivery', {
            'fields': (
                'delivery_methods', 'email_sent', 'email_sent_at',
                'push_sent', 'push_sent_at'
            )
        }),
        ('Metadata', {
            'fields': ('metadata', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    actions = ['mark_as_read', 'mark_as_unread']
    
    def user_email(self, obj):
        url = reverse('admin:core_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def priority_display(self, obj):
        colors = {
            'urgent': 'red',
            'high': 'orange',
            'normal': 'blue',
            'low': 'gray',
        }
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_display.short_description = 'Priority'
    priority_display.admin_order_field = 'priority'
    
    def read_status(self, obj):
        if obj.read:
            return format_html('<span style="color: green;">✓ Read</span>')
        return format_html('<span style="color: orange;">⏳ Unread</span>')
    read_status.short_description = 'Read Status'
    read_status.admin_order_field = 'read'
    
    def delivery_status(self, obj):
        statuses = []
        if 'in_app' in obj.delivery_methods:
            statuses.append('📱 App')
        if obj.email_sent:
            statuses.append('✉️ Email')
        if obj.push_sent:
            statuses.append('🔔 Push')
        return ' '.join(statuses) if statuses else '-'
    delivery_status.short_description = 'Delivered Via'
    
    def mark_as_read(self, request, queryset):
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(request, f"{queryset.count()} notifications marked as read.")
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(read=False, read_at=None)
        self.message_user(request, f"{queryset.count()} notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected as unread"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'in_app_enabled', 'email_enabled', 
        'push_enabled', 'sms_enabled', 'discord_enabled'
    ]
    list_filter = [
        'in_app_enabled', 'email_enabled', 'push_enabled', 
        'sms_enabled', 'discord_enabled', 'quiet_hours_enabled'
    ]
    search_fields = ['user__email', 'user__username']
    fieldsets = [
        ('User', {
            'fields': ('user',)
        }),
        ('General Settings', {
            'fields': ('in_app_enabled',)
        }),
        ('Email Notifications', {
            'fields': (
                'email_enabled', 'email_tournament_updates',
                'email_coaching_reminders', 'email_team_activity',
                'email_payment_receipts', 'email_security_alerts',
                'email_marketing'
            )
        }),
        ('Push Notifications', {
            'fields': (
                'push_enabled', 'push_tournament_updates',
                'push_coaching_reminders', 'push_team_activity',
                'push_match_updates'
            )
        }),
        ('SMS Notifications', {
            'fields': ('sms_enabled', 'sms_urgent_only')
        }),
        ('Discord Integration', {
            'fields': ('discord_enabled', 'discord_webhook_url')
        }),
        ('Quiet Hours', {
            'fields': (
                'quiet_hours_enabled', 'quiet_hours_start', 
                'quiet_hours_end'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    def user_email(self, obj):
        url = reverse('admin:core_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'notification_type', 'default_priority', 
        'is_active', 'updated_at'
    ]
    list_filter = ['notification_type', 'default_priority', 'is_active']
    search_fields = ['name', 'title_template', 'message_template']
    fieldsets = [
        ('Template Information', {
            'fields': ('name', 'notification_type', 'is_active')
        }),
        ('Content Templates', {
            'fields': ('title_template', 'message_template'),
            'description': 'Use {variable_name} for placeholders'
        }),
        ('Default Settings', {
            'fields': ('default_priority', 'default_delivery_methods')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    readonly_fields = ['created_at', 'updated_at']
