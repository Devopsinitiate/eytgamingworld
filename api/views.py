"""DRF viewsets for EYTGaming API v1."""
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from core.models import User, Game, UserGameProfile
from tournaments.models import Tournament
from coaching.models import CoachProfile, CoachingSession
from .serializers import (
    UserSerializer, UserDetailSerializer, GameSerializer,
    UserGameProfileSerializer, TournamentSerializer,
    CoachProfileSerializer, CoachingSessionSerializer,
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'skill_level', 'country', 'is_verified']
    search_fields = ['username', 'email', 'display_name']
    ordering_fields = ['date_joined', 'total_points', 'level']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Game.objects.filter(is_active=True)
    serializer_class = GameSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'genre', 'developer']
    ordering_fields = ['name', 'display_order']


class UserGameProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserGameProfile.objects.select_related('user', 'game')
    serializer_class = UserGameProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'game', 'is_main_game']
    ordering = ['-is_main_game', '-skill_rating']


class TournamentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tournament.objects.select_related('game')
    serializer_class = TournamentSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'game', 'format', 'skill_level', 'is_featured']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'prize_pool', 'created_at']
    ordering = ['-start_date']


class CoachProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CoachProfile.objects.filter(status='active').select_related('user')
    serializer_class = CoachProfileSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['experience_level', 'is_verified', 'accepting_students']
    search_fields = ['bio', 'specializations']
    ordering_fields = ['average_rating', 'total_sessions', 'hourly_rate']
    ordering = ['-average_rating']


class CoachingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CoachingSession.objects.select_related('coach__user', 'student', 'game')
    serializer_class = CoachingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'session_type', 'coach', 'student', 'game']
    ordering_fields = ['scheduled_start', 'created_at']
    ordering = ['-scheduled_start']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(coach__user=user) | qs.filter(student=user)


@require_http_methods(["GET"])
@login_required
def onboarding_status(request):
    return JsonResponse({'completed': request.user.onboarding_completed})


@require_POST
@csrf_protect
@login_required
def complete_onboarding(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
    if data.get('completed'):
        request.user.onboarding_completed = True
        request.user.save(update_fields=['onboarding_completed'])
    return JsonResponse({'status': 'ok'})
