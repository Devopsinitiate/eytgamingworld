from django.urls import path
from django.views.generic import TemplateView, RedirectView
from . import views
from . import session_views

app_name = 'accounts'

urlpatterns = [
    # Redirect to dashboard profile/settings
    path('profile/', RedirectView.as_view(pattern_name='dashboard:profile_view', permanent=False), name='profile'),
    path('settings/', RedirectView.as_view(pattern_name='dashboard:settings_profile', permanent=False), name='settings'),
    # Become an Organizer
    path('become-organizer/', views.become_organizer, name='become_organizer'),
    path('organizer-status/', views.organizer_status, name='organizer_status'),
    # Two-Factor Authentication
    path('2fa/', views.two_factor_setup, name='two_factor_setup'),
    path('2fa/verify/<int:device_id>/', views.two_factor_verify, name='two_factor_verify'),
    path('2fa/dismiss/', views.two_factor_dismiss, name='two_factor_dismiss'),
    # Session management
    path('sessions/', session_views.session_list, name='session_list'),
    path('sessions/logout-all/', session_views.logout_all_sessions, name='logout_all_sessions'),
    path('sessions/<str:session_key>/logout/', session_views.logout_session, name='logout_session'),
]
