"""
Notification views
"""
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.conf import settings

from .models import Notification, NotificationPreference, Device

logger = logging.getLogger(__name__)


@login_required
def notification_list(request):
    """List all notifications for the user"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Filter by read/unread
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(read=True)
    
    # Filter by type
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    context = {
        'notifications': notifications,
        'unread_count': Notification.objects.filter(user=request.user, read=False).count(),
        'filter_type': filter_type,
    }
    
    return render(request, 'notifications/list.html', context)


@login_required
def notification_detail(request, notification_id):
    """View notification details and mark as read"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    # Mark as read
    notification.mark_as_read()
    
    # Redirect to action URL if provided
    if notification.action_url:
        return redirect(notification.action_url)
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'notifications/detail.html', context)


@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    notification.mark_as_read()
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_all_as_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        user=request.user,
        read=False
    ).update(read=True)
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def delete_notification(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    notification.delete()
    
    return JsonResponse({'success': True})


@login_required
def unread_count(request):
    """Get unread notification count (for AJAX)"""
    count = Notification.objects.filter(
        user=request.user,
        read=False
    ).count()
    
    return JsonResponse({'count': count})


@login_required
def notification_preferences(request):
    """Manage notification preferences"""
    prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update preferences
        prefs.in_app_enabled = request.POST.get('in_app_enabled') == 'on'
        prefs.email_enabled = request.POST.get('email_enabled') == 'on'
        prefs.email_tournament_updates = request.POST.get('email_tournament_updates') == 'on'
        prefs.email_coaching_reminders = request.POST.get('email_coaching_reminders') == 'on'
        prefs.email_team_activity = request.POST.get('email_team_activity') == 'on'
        prefs.email_payment_receipts = request.POST.get('email_payment_receipts') == 'on'
        prefs.email_security_alerts = request.POST.get('email_security_alerts') == 'on'
        prefs.email_marketing = request.POST.get('email_marketing') == 'on'
        
        prefs.push_enabled = request.POST.get('push_enabled') == 'on'
        prefs.push_tournament_updates = request.POST.get('push_tournament_updates') == 'on'
        prefs.push_coaching_reminders = request.POST.get('push_coaching_reminders') == 'on'
        prefs.push_team_activity = request.POST.get('push_team_activity') == 'on'
        prefs.push_match_updates = request.POST.get('push_match_updates') == 'on'
        
        prefs.sms_enabled = request.POST.get('sms_enabled') == 'on'
        prefs.sms_urgent_only = request.POST.get('sms_urgent_only') == 'on'
        
        prefs.discord_enabled = request.POST.get('discord_enabled') == 'on'
        prefs.discord_webhook_url = request.POST.get('discord_webhook_url', '')
        
        prefs.quiet_hours_enabled = request.POST.get('quiet_hours_enabled') == 'on'
        
        if prefs.quiet_hours_enabled:
            quiet_start = request.POST.get('quiet_hours_start')
            quiet_end = request.POST.get('quiet_hours_end')
            if quiet_start:
                prefs.quiet_hours_start = quiet_start
            if quiet_end:
                prefs.quiet_hours_end = quiet_end
        
        prefs.save()
        
        return JsonResponse({'success': True, 'message': 'Preferences updated'})
    
    context = {
        'prefs': prefs,
    }
    
    return render(request, 'notifications/preferences.html', context)


@login_required
@require_POST
def subscribe_push(request):
    """Subscribe the current user's browser to push notifications"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    subscription_info = data.get('subscription')
    user_agent = data.get('user_agent', '')
    device_name = data.get('device_name', '')

    if not subscription_info or not subscription_info.get('endpoint'):
        return JsonResponse({'success': False, 'error': 'Missing subscription data'}, status=400)

    # Check if this subscription already exists
    existing = Device.objects.filter(
        user=request.user,
        subscription_info__endpoint=subscription_info['endpoint']
    ).first()

    if existing:
        # Re-activate if it was inactive
        if not existing.is_active:
            existing.is_active = True
            existing.subscription_info = subscription_info
            existing.save(update_fields=['is_active', 'subscription_info', 'updated_at'])
        return JsonResponse({'success': True, 'message': 'Subscription already exists'})

    Device.objects.create(
        user=request.user,
        subscription_info=subscription_info,
        user_agent=user_agent[:500] if user_agent else '',
        device_name=device_name[:200] if device_name else '',
    )

    logger.info(f'Push subscription added for user {request.user.id}')
    return JsonResponse({'success': True, 'message': 'Subscribed to push notifications'})


@login_required
@require_POST
def unsubscribe_push(request):
    """Unsubscribe the current user's browser from push notifications"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    endpoint = data.get('endpoint')

    if endpoint:
        Device.objects.filter(
            user=request.user,
            subscription_info__endpoint=endpoint
        ).update(is_active=False)
    else:
        # Unsubscribe all devices
        Device.objects.filter(user=request.user).update(is_active=False)

    logger.info(f'Push subscription removed for user {request.user.id}')
    return JsonResponse({'success': True, 'message': 'Unsubscribed from push notifications'})


@login_required
@require_POST
def test_push(request):
    """Send a test push notification to the current user"""
    notification = Notification.create_notification(
        user=request.user,
        title='Test Notification',
        message='This is a test push notification from EYTGaming!',
        notification_type='system',
        delivery_methods=['push'],
    )
    return JsonResponse({'success': True, 'notification_id': str(notification.id)})


@login_required
def recent_notifications(request):
    """Get recent notifications (for dropdown/widget)"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    unread_count = Notification.objects.filter(
        user=request.user,
        read=False
    ).count()
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'notifications': [
                {
                    'id': str(n.id),
                    'title': n.title,
                    'message': n.message,
                    'type': n.notification_type,
                    'priority': n.priority,
                    'read': n.read,
                    'created_at': n.created_at.isoformat(),
                    'action_url': n.action_url,
                }
                for n in notifications
            ],
            'unread_count': unread_count,
        }
        return JsonResponse(data)
    
    # Return HTML for regular requests
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'notifications/recent.html', context)
