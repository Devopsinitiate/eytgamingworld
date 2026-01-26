from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from core.models import User
import uuid


class Activity(models.Model):
    """User activity log"""
    
    ACTIVITY_TYPES = [
        ('tournament_registered', 'Tournament Registered'),
        ('tournament_completed', 'Tournament Completed'),
        ('team_joined', 'Team Joined'),
        ('team_left', 'Team Left'),
        ('achievement_earned', 'Achievement Earned'),
        ('payment_completed', 'Payment Completed'),
        ('profile_updated', 'Profile Updated'),
        ('friend_added', 'Friend Added'),
        ('game_profile_added', 'Game Profile Added'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Activity data (JSON for flexibility)
    data = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.user.get_display_name()} - {self.get_activity_type_display()} - {self.created_at}"



class Achievement(models.Model):
    """Achievement definitions"""
    
    ACHIEVEMENT_TYPES = [
        ('tournament', 'Tournament'),
        ('team', 'Team'),
        ('social', 'Social'),
        ('platform', 'Platform'),
    ]
    
    RARITY_LEVELS = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    rarity = models.CharField(max_length=20, choices=RARITY_LEVELS, default='common')
    
    # Icon and display
    icon = models.ImageField(upload_to='achievements/', null=True, blank=True)
    icon_url = models.URLField(blank=True)  # Alternative to uploaded icon
    
    # Requirements
    is_progressive = models.BooleanField(default=False)
    target_value = models.IntegerField(default=1)  # For progressive achievements
    points_reward = models.IntegerField(default=10)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False)  # Hidden until earned
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'achievements'
        ordering = ['achievement_type', 'name']
        verbose_name = 'Achievement'
        verbose_name_plural = 'Achievements'
    
    def __str__(self):
        return self.name



class UserAchievement(models.Model):
    """User's earned achievements"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    
    # Progress tracking
    current_value = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    # Showcase
    in_showcase = models.BooleanField(default=False)
    showcase_order = models.IntegerField(default=0)
    
    # Metadata
    earned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_achievements'
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'is_completed']),
            models.Index(fields=['user', 'in_showcase', 'showcase_order']),
        ]
        verbose_name = 'User Achievement'
        verbose_name_plural = 'User Achievements'
    
    def __str__(self):
        return f"{self.user.get_display_name()} - {self.achievement.name}"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage for progressive achievements"""
        if not self.achievement.is_progressive:
            return 100 if self.is_completed else 0
        return min(100, (self.current_value / self.achievement.target_value) * 100)



class Recommendation(models.Model):
    """Cached recommendations for users"""
    
    RECOMMENDATION_TYPES = [
        ('tournament', 'Tournament'),
        ('team', 'Team'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    
    # Generic relation to recommended item
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Recommendation metadata
    score = models.FloatField(default=0.0)  # Relevance score
    reason = models.CharField(max_length=200)  # Why recommended
    
    # Status
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Recommendations expire after 24 hours
    
    class Meta:
        db_table = 'recommendations'
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['user', 'recommendation_type', '-score']),
            models.Index(fields=['user', 'is_dismissed']),
        ]
        verbose_name = 'Recommendation'
        verbose_name_plural = 'Recommendations'
    
    def __str__(self):
        return f"{self.user.get_display_name()} - {self.get_recommendation_type_display()} - Score: {self.score}"


class ProfileCompleteness(models.Model):
    """Track profile completeness with weighted fields"""
    
    FIELD_WEIGHTS = {
        'first_name': 5,
        'last_name': 5,
        'display_name': 5,
        'avatar': 10,
        'bio': 10,
        'date_of_birth': 5,
        'country': 5,
        'city': 3,
        'discord_username': 7,
        'steam_id': 7,
        'twitch_username': 7,
        'game_profile': 15,  # At least one game profile
        'email_verified': 10,
        'phone_number': 6,
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='completeness')
    
    # Completeness tracking
    total_points = models.IntegerField(default=0)
    max_points = models.IntegerField(default=100)
    percentage = models.IntegerField(default=0)
    
    # Field completion status (JSON for flexibility)
    completed_fields = models.JSONField(default=dict)
    incomplete_fields = models.JSONField(default=list)
    
    # Metadata
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'profile_completeness'
        verbose_name = 'Profile Completeness'
        verbose_name_plural = 'Profile Completeness'
    
    def __str__(self):
        return f"{self.user.get_display_name()} - {self.percentage}% complete"
    
    @classmethod
    def calculate_for_user(cls, user):
        """Calculate profile completeness for a user"""
        total_points = 0
        completed = {}
        incomplete = []
        
        # Check each field
        if user.first_name:
            total_points += cls.FIELD_WEIGHTS['first_name']
            completed['first_name'] = True
        else:
            incomplete.append('first_name')
        
        if user.last_name:
            total_points += cls.FIELD_WEIGHTS['last_name']
            completed['last_name'] = True
        else:
            incomplete.append('last_name')
        
        if user.display_name:
            total_points += cls.FIELD_WEIGHTS['display_name']
            completed['display_name'] = True
        else:
            incomplete.append('display_name')
        
        if user.avatar:
            total_points += cls.FIELD_WEIGHTS['avatar']
            completed['avatar'] = True
        else:
            incomplete.append('avatar')
        
        if user.bio:
            total_points += cls.FIELD_WEIGHTS['bio']
            completed['bio'] = True
        else:
            incomplete.append('bio')
        
        if user.date_of_birth:
            total_points += cls.FIELD_WEIGHTS['date_of_birth']
            completed['date_of_birth'] = True
        else:
            incomplete.append('date_of_birth')
        
        if user.country:
            total_points += cls.FIELD_WEIGHTS['country']
            completed['country'] = True
        else:
            incomplete.append('country')
        
        if user.city:
            total_points += cls.FIELD_WEIGHTS['city']
            completed['city'] = True
        else:
            incomplete.append('city')
        
        if user.discord_username:
            total_points += cls.FIELD_WEIGHTS['discord_username']
            completed['discord_username'] = True
        else:
            incomplete.append('discord_username')
        
        if user.steam_id:
            total_points += cls.FIELD_WEIGHTS['steam_id']
            completed['steam_id'] = True
        else:
            incomplete.append('steam_id')
        
        if user.twitch_username:
            total_points += cls.FIELD_WEIGHTS['twitch_username']
            completed['twitch_username'] = True
        else:
            incomplete.append('twitch_username')
        
        if user.game_profiles.exists():
            total_points += cls.FIELD_WEIGHTS['game_profile']
            completed['game_profile'] = True
        else:
            incomplete.append('game_profile')
        
        if user.is_verified:
            total_points += cls.FIELD_WEIGHTS['email_verified']
            completed['email_verified'] = True
        else:
            incomplete.append('email_verified')
        
        if user.phone_number:
            total_points += cls.FIELD_WEIGHTS['phone_number']
            completed['phone_number'] = True
        else:
            incomplete.append('phone_number')
        
        # Calculate percentage
        max_points = sum(cls.FIELD_WEIGHTS.values())
        percentage = int((total_points / max_points) * 100)
        
        # Update or create completeness record
        completeness, created = cls.objects.update_or_create(
            user=user,
            defaults={
                'total_points': total_points,
                'max_points': max_points,
                'percentage': percentage,
                'completed_fields': completed,
                'incomplete_fields': incomplete,
            }
        )
        
        # Update user's profile_completed flag
        if percentage == 100 and not user.profile_completed:
            user.profile_completed = True
            user.add_points(50)  # Award bonus points
            user.save(update_fields=['profile_completed'])
            
            # Check for profile completion achievement
            from dashboard.tasks import check_user_achievements
            check_user_achievements.delay(str(user.id), 'profile_completed')
        
        return completeness


class UserReport(models.Model):
    """User reports for moderation"""
    
    REPORT_CATEGORIES = [
        ('inappropriate_content', 'Inappropriate Username or Avatar'),
        ('harassment', 'Harassment or Abusive Behavior'),
        ('spam', 'Spam or Advertising'),
        ('cheating', 'Cheating or Unfair Play'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    
    # Report details
    category = models.CharField(max_length=50, choices=REPORT_CATEGORIES)
    description = models.TextField(max_length=1000)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reported_user', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
        verbose_name = 'User Report'
        verbose_name_plural = 'User Reports'
    
    def __str__(self):
        return f"Report: {self.reported_user.get_display_name()} by {self.reporter.get_display_name()} - {self.get_status_display()}"
