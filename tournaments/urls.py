from django.urls import path
from . import views
from .live_updates import tournament_live_updates, tournament_stats_api
from . import api_views
from . import analytics_views

app_name = 'tournaments'

urlpatterns = [
    # Tournament listing & detail
    path('', views.TournamentListView.as_view(), name='list'),
    path('create/', views.TournamentCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.TournamentDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.TournamentUpdateView.as_view(), name='edit'),
    path('<slug:slug>/delete/', views.TournamentDeleteView.as_view(), name='delete'),
    
    # Registration & Check-in
    path('<slug:slug>/register/', views.tournament_register, name='register'),
    path('<slug:slug>/unregister/', views.tournament_unregister, name='unregister'),
    path('<slug:slug>/check-in/', views.tournament_check_in, name='check_in'),
    
    # Bracket views
    path('<slug:slug>/bracket/', views.BracketView.as_view(), name='bracket'),
    path('<slug:slug>/bracket/json/', views.bracket_json, name='bracket_json'),
    path('<slug:slug>/bracket/partial/', views.bracket_partial, name='bracket_partial'),
    path('<slug:slug>/bracket-preview-data/', views.bracket_preview_data, name='bracket_preview_data'),
    
    # Match management
    path('<slug:slug>/matches/', views.MatchListView.as_view(), name='matches'),
    path('match/<uuid:pk>/', views.MatchDetailView.as_view(), name='match_detail'),
    path('match/<uuid:pk>/report/', views.match_report_score, name='match_report'),
    path('match/<uuid:pk>/dispute/', views.match_dispute, name='match_dispute'),
    
    # Admin actions
    path('<slug:slug>/start/', views.tournament_start, name='start'),
    path('<slug:slug>/change-status/', views.tournament_change_status, name='change_status'),
    path('<slug:slug>/participants/', views.ParticipantListView.as_view(), name='participants'),
    path('<slug:slug>/generate-bracket/', views.generate_bracket, name='generate_bracket'),
    path('participant/<uuid:participant_id>/payment/', views.tournament_payment, name='payment'),
    path('stripe/create/<uuid:payment_id>/', views.stripe_create, name='stripe_create'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('paystack/init/<uuid:payment_id>/', views.paystack_init, name='paystack_init'),
    path('paystack/success/', views.paystack_success, name='paystack_success'),
    path('paystack/webhook/', views.paystack_webhook, name='paystack_webhook'),
    
    # API endpoints (HTMX)
    path('api/upcoming/', views.upcoming_tournaments_api, name='api_upcoming'),
    
    # Live match display API endpoints
    path('api/<slug:slug>/matches/live/', views.live_matches_api, name='api_live_matches'),
    path('api/<slug:slug>/stats/', tournament_stats_api, name='api_tournament_stats'),
    
    # New optimized API endpoints
    path('<slug:slug>/api/stats/', api_views.tournament_stats_api, name='api_stats'),
    path('<slug:slug>/api/participants/', api_views.tournament_participants_api, name='api_participants'),
    path('<slug:slug>/api/matches/', api_views.tournament_matches_api, name='api_matches'),
    path('<slug:slug>/api/updates/', api_views.tournament_updates_api, name='api_updates'),
    path('<slug:slug>/api/bracket/', api_views.tournament_bracket_api, name='api_bracket'),
    path('<slug:slug>/api/cache/invalidate/', api_views.invalidate_tournament_cache, name='api_cache_invalidate'),
    
    # Real-time updates endpoints
    path('<slug:slug>/live-updates/', tournament_live_updates, name='live_updates'),
    
    # Social sharing endpoints
    path('<slug:slug>/share/', views.tournament_share, name='share'),
    path('<slug:slug>/share-count/', views.tournament_share_count, name='share_count'),
    
    # Analytics endpoints
    path('analytics/performance/', analytics_views.track_page_performance, name='analytics_performance'),
    path('analytics/engagement/', analytics_views.track_engagement, name='analytics_engagement'),
    path('analytics/conversion/', analytics_views.track_conversion, name='analytics_conversion'),
    path('analytics/error/', analytics_views.track_error, name='analytics_error'),
    path('analytics/metric/', analytics_views.track_performance_metric, name='analytics_metric'),
    path('analytics/dashboard/', analytics_views.get_analytics_dashboard, name='analytics_dashboard'),
    path('<slug:slug>/analytics/dashboard/', analytics_views.get_analytics_dashboard, name='analytics_dashboard_tournament'),
    
    # Page view tracking endpoint
    path('<slug:slug>/view/', analytics_views.track_page_view, name='track_page_view'),
]