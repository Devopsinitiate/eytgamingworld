"""DRF serializers for EYTGaming API v1."""
from rest_framework import serializers
from core.models import User, Game, UserGameProfile
from tournaments.models import Tournament
from coaching.models import CoachProfile, CoachingSession


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'display_name', 'role', 'skill_level',
            'bio', 'avatar', 'country', 'date_joined', 'is_verified',
            'total_points', 'level', 'is_active',
        ]
        read_only_fields = ['id', 'date_joined', 'is_verified', 'total_points', 'level']


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'display_name', 'first_name', 'last_name',
            'role', 'skill_level', 'bio', 'avatar', 'banner',
            'discord_username', 'steam_id', 'twitch_username',
            'country', 'city', 'timezone', 'date_joined',
            'is_verified', 'is_active', 'total_points', 'level',
            'private_profile', 'online_status_visible',
        ]
        read_only_fields = ['id', 'date_joined', 'total_points', 'level']


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserGameProfileSerializer(serializers.ModelSerializer):
    user_display_name = serializers.CharField(source='user.get_display_name', read_only=True)
    game_name = serializers.CharField(source='game.name', read_only=True)

    class Meta:
        model = UserGameProfile
        fields = [
            'id', 'user', 'user_display_name', 'game', 'game_name',
            'in_game_name', 'skill_rating', 'mmr', 'rank',
            'matches_played', 'matches_won', 'matches_lost',
            'win_rate', 'is_main_game', 'preferred_role',
        ]
        read_only_fields = ['id', 'win_rate']


class TournamentSerializer(serializers.ModelSerializer):
    game_name = serializers.CharField(source='game.name', read_only=True)

    class Meta:
        model = Tournament
        fields = [
            'id', 'title', 'slug', 'game', 'game_name', 'description',
            'registration_fee', 'prize_pool', 'max_participants',
            'start_date', 'end_date', 'status', 'format',
            'skill_level', 'is_featured', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']


class CoachProfileSerializer(serializers.ModelSerializer):
    user_display_name = serializers.CharField(source='user.get_display_name', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = CoachProfile
        fields = [
            'id', 'user', 'user_display_name', 'user_avatar',
            'bio', 'specializations', 'experience_level', 'years_experience',
            'hourly_rate', 'status', 'accepting_students',
            'average_rating', 'total_reviews', 'total_sessions',
            'is_verified', 'offers_individual', 'offers_group',
        ]


class CoachingSessionSerializer(serializers.ModelSerializer):
    coach_name = serializers.CharField(source='coach.user.get_display_name', read_only=True)
    student_name = serializers.CharField(source='student.get_display_name', read_only=True)
    game_name = serializers.CharField(source='game.name', read_only=True)

    class Meta:
        model = CoachingSession
        fields = [
            'id', 'coach', 'coach_name', 'student', 'student_name',
            'game', 'game_name', 'session_type',
            'scheduled_start', 'scheduled_end',
            'duration_minutes', 'status', 'price', 'is_paid',
            'topics', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'is_paid']
