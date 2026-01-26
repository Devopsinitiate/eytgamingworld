"""
Notification URL configuration
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification list and detail
    path('', views.notification_list, name='list'),
    path('<uuid:notification_id>/', views.notification_detail, name='detail'),
    path('recent/', views.recent_notifications, name='recent'),
    
    # Actions
    path('<uuid:notification_id>/read/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('<uuid:notification_id>/delete/', views.delete_notification, name='delete'),
    path('unread-count/', views.unread_count, name='unread_count'),
    
    # Preferences
    path('preferences/', views.notification_preferences, name='preferences'),
]
