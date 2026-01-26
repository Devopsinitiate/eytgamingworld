from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('activity/', views.dashboard_activity, name='activity'),
    path('stats/', views.dashboard_stats, name='stats'),
    path('payments/summary/', views.dashboard_payment_summary, name='payment_summary'),
    
    # Profile URLs - order matters! More specific patterns first
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/export/', views.profile_export, name='profile_export'),
    path('profile/<str:username>/report/', views.user_report, name='user_report'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    
    # Game Profile URLs
    path('games/', views.game_profile_list, name='game_profile_list'),
    path('games/add/', views.game_profile_create, name='game_profile_create'),
    path('games/<uuid:profile_id>/edit/', views.game_profile_edit, name='game_profile_edit'),
    path('games/<uuid:profile_id>/delete/', views.game_profile_delete, name='game_profile_delete'),
    path('games/<uuid:profile_id>/set-main/', views.game_profile_set_main, name='game_profile_set_main'),
    
    # Tournament History URLs
    path('tournaments/', views.tournament_history, name='tournament_history'),
    path('tournaments/<uuid:tournament_id>/', views.tournament_detail_history, name='tournament_detail_history'),
    
    # Team Membership URLs
    path('teams/', views.team_membership, name='team_membership'),
    
    # Settings URLs
    path('settings/profile/', views.settings_profile, name='settings_profile'),
    path('settings/privacy/', views.settings_privacy, name='settings_privacy'),
    path('settings/notifications/', views.settings_notifications, name='settings_notifications'),
    path('settings/security/', views.settings_security, name='settings_security'),
    path('settings/accounts/', views.settings_connected_accounts, name='settings_accounts'),
    path('settings/delete/', views.account_delete, name='account_delete'),
]
