"""API v1 URL configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter(trailing_slash=False)
router.register(r'users', views.UserViewSet, basename='api-user')
router.register(r'games', views.GameViewSet, basename='api-game')
router.register(r'game-profiles', views.UserGameProfileViewSet, basename='api-game-profile')
router.register(r'tournaments', views.TournamentViewSet, basename='api-tournament')
router.register(r'coaches', views.CoachProfileViewSet, basename='api-coach')
router.register(r'sessions', views.CoachingSessionViewSet, basename='api-session')

urlpatterns = [
    path('', include(router.urls)),
    path('chat/', include('chat.urls')),
]
