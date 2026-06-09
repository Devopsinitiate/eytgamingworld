"""Admin configuration for the accounts app."""
from django.contrib import admin, messages
from django.utils import timezone
from .models import OrganizerApplication
from .services import send_organizer_approved, send_organizer_rejected


@admin.action(description='Approve selected organizer applications')
def approve_applications(modeladmin, request, queryset):
    for app in queryset.filter(status='pending'):
        app.status = OrganizerApplication.STATUS_APPROVED
        app.reviewed_at = timezone.now()
        app.reviewed_by = request.user
        app.save()

        # Upgrade user to organizer
        user = app.user
        user.role = 'organizer'
        user.save(update_fields=['role'])

        # Send approval notification
        send_organizer_approved(user, app)

        from security.utils import log_audit_action
        log_audit_action(
            user=request.user,
            action='organizer_approved',
            description=f'Approved organizer application for {app.full_name} ({user.email})',
            severity='medium',
            content_object=app,
        )

    count = queryset.filter(status='pending').update(status='approved', reviewed_at=timezone.now(), reviewed_by=request.user)
    if count:
        messages.success(request, f'{count} application(s) approved and users upgraded to organizers.')
    else:
        messages.warning(request, 'No pending applications were selected.')


@admin.action(description='Reject selected organizer applications')
def reject_applications(modeladmin, request, queryset):
    for app in queryset.filter(status='pending'):
        rejection_reason = request.POST.get('rejection_reason', '')
        app.status = OrganizerApplication.STATUS_REJECTED
        app.reviewed_at = timezone.now()
        app.reviewed_by = request.user
        if rejection_reason:
            app.rejection_reason = rejection_reason
        app.save()

        send_organizer_rejected(app.user, app)

        from security.utils import log_audit_action
        log_audit_action(
            user=request.user,
            action='organizer_rejected',
            description=f'Rejected organizer application for {app.full_name} ({app.user.email})',
            severity='low',
            content_object=app,
        )

    count = queryset.filter(status='pending').update(
        status='rejected', reviewed_at=timezone.now(), reviewed_by=request.user
    )
    if count:
        messages.success(request, f'{count} application(s) rejected.')
    else:
        messages.warning(request, 'No pending applications were selected.')


class OrganizerApplicationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user_email', 'country', 'status', 'submitted_at', 'reviewed_at']
    list_filter = ['status', 'country', 'submitted_at']
    search_fields = ['full_name', 'user__email', 'user__username', 'reason']
    readonly_fields = ['submitted_at', 'reviewed_at', 'reviewed_by']
    actions = [approve_applications, reject_applications]
    fieldsets = [
        ('Applicant Info', {
            'fields': ['user', 'full_name', 'phone_number', 'country']
        }),
        ('Application', {
            'fields': ['reason', 'experience', 'agreed_to_terms']
        }),
        ('Status', {
            'fields': ['status', 'rejection_reason', 'admin_notes', 'submitted_at', 'reviewed_at', 'reviewed_by']
        }),
    ]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user
            if obj.status == 'approved':
                user = obj.user
                user.role = 'organizer'
                user.save(update_fields=['role'])
                send_organizer_approved(user, obj)
            elif obj.status == 'rejected':
                send_organizer_rejected(obj.user, obj)
        super().save_model(request, obj, form, change)


admin.site.register(OrganizerApplication, OrganizerApplicationAdmin)
