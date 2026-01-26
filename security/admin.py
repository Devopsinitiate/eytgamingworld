"""
Admin interface for security and audit models.
"""
from django.contrib import admin
from .models import AuditLog, SecurityEvent


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'severity', 'ip_address']
    list_filter = ['action', 'severity', 'timestamp', 'model_name']
    search_fields = ['username', 'description', 'ip_address', 'object_id']
    readonly_fields = ['id', 'timestamp', 'user', 'username', 'action', 'model_name', 
                       'object_id', 'description', 'ip_address', 'user_agent', 
                       'request_path', 'request_method', 'severity', 'details']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'event_type', 'user', 'ip_address', 'resolved']
    list_filter = ['event_type', 'resolved', 'created_at']
    search_fields = ['description', 'ip_address', 'user__email']
    readonly_fields = ['id', 'created_at', 'event_type', 'description', 'user', 
                       'ip_address', 'user_agent', 'request_path', 'metadata']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'event_type', 'description', 'created_at')
        }),
        ('User & Request', {
            'fields': ('user', 'ip_address', 'user_agent', 'request_path')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_at', 'resolved_by')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
