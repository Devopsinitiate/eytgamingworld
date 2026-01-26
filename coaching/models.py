from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
from core.models import User, Game
from datetime import timedelta
import uuid


class CoachProfile(models.Model):
    """Extended profile for coaches/tutors"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_break', 'On Break'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('beginner', 'Beginner Coach'),
        ('intermediate', 'Intermediate Coach'),
        ('advanced', 'Advanced Coach'),
        ('professional', 'Professional/Pro Player'),
        ('world_class', 'World Class'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coach_profile')
    
    # Profile Information
    bio = models.TextField(help_text="Tell students about yourself")
    specializations = models.JSONField(default=list, blank=True,
                                       help_text='e.g., ["Character coaching", "Strategy", "Mechanics"]')
    
    # Experience
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES,
                                        default='intermediate')
    years_experience = models.IntegerField(default=0)
    achievements = models.TextField(blank=True, help_text="Tournament wins, rankings, etc.")
    
    # Pricing (per hour in USD)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2,
                                      validators=[MinValueValidator(0)])
    
    # Availability
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    accepting_students = models.BooleanField(default=True)
    max_students_per_week = models.IntegerField(default=10,
                                                 validators=[MinValueValidator(1)])
    
    # Session Settings
    min_session_duration = models.IntegerField(default=60, help_text="Minutes")
    max_session_duration = models.IntegerField(default=180, help_text="Minutes")
    session_increment = models.IntegerField(default=30, help_text="Booking increment in minutes")
    
    # Teaching Methods
    offers_individual = models.BooleanField(default=True)
    offers_group = models.BooleanField(default=False)
    max_group_size = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Video Platform
    preferred_platform = models.CharField(max_length=50, default='Discord',
                                         help_text="Discord, Zoom, etc.")
    platform_username = models.CharField(max_length=100, blank=True)
    
    # Media
    profile_video = models.URLField(blank=True, help_text="YouTube/Twitch intro video")
    
    # Statistics
    total_sessions = models.IntegerField(default=0)
    total_students = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00,
                                         validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.IntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Verification
    is_verified = models.BooleanField(default=False, help_text="Verified by admin")
    verification_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coach_profiles'
        ordering = ['-average_rating', '-total_sessions']
    
    def __str__(self):
        return f"Coach: {self.user.get_display_name()}"
    
    def get_absolute_url(self):
        return reverse('coaching:coach_detail', kwargs={'pk': self.pk})
    
    @property
    def is_available(self):
        return self.status == 'active' and self.accepting_students
    
    def update_rating(self):
        """Recalculate average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.total_reviews = reviews.count()
            self.save(update_fields=['average_rating', 'total_reviews'])


class CoachGameExpertise(models.Model):
    """Games a coach teaches"""
    
    RANK_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('diamond', 'Diamond'),
        ('master', 'Master'),
        ('grandmaster', 'Grandmaster'),
        ('challenger', 'Challenger/Pro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name='game_expertise')
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    
    # Expertise Details
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, blank=True)
    rank_proof = models.URLField(blank=True, help_text="Link to profile/stats")
    specialization_notes = models.TextField(blank=True)
    
    # Pricing (can differ per game)
    custom_hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                             help_text="Override default rate for this game")
    
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'coach_game_expertise'
        unique_together = ['coach', 'game']
        ordering = ['-is_primary']
    
    def __str__(self):
        return f"{self.coach.user.get_display_name()} - {self.game.name}"
    
    @property
    def effective_rate(self):
        """Get the rate for this game (custom or default)"""
        return self.custom_hourly_rate or self.coach.hourly_rate


class CoachAvailability(models.Model):
    """Coach's weekly availability schedule"""
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name='availability')
    
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'coach_availability'
        ordering = ['weekday', 'start_time']
        unique_together = ['coach', 'weekday', 'start_time']
    
    def __str__(self):
        return f"{self.coach.user.get_display_name()} - {self.get_weekday_display()}: {self.start_time}-{self.end_time}"


class CoachingSession(models.Model):
    """Individual coaching session"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    SESSION_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('group', 'Group'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Participants
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name='sessions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coaching_sessions')
    
    # Session Details
    game = models.ForeignKey(Game, on_delete=models.PROTECT)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='individual')
    
    # Schedule
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Duration
    duration_minutes = models.IntegerField()
    
    # Additional students (for group sessions)
    additional_students = models.ManyToManyField(User, blank=True,
                                                  related_name='group_sessions')
    
    # Topics & Notes
    topics = models.JSONField(default=list, blank=True,
                              help_text='e.g., ["Lane control", "Combos", "Game sense"]')
    student_notes = models.TextField(blank=True, help_text="Student's goals for session")
    coach_notes = models.TextField(blank=True, help_text="Coach's session notes")
    
    # Payment
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_intent_id = models.CharField(max_length=200, blank=True, help_text="Stripe payment ID")
    
    # Video Call
    video_link = models.URLField(blank=True, help_text="Meeting link")
    recording_link = models.URLField(blank=True, help_text="Optional session recording")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Cancellation
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='cancelled_sessions')
    cancellation_reason = models.TextField(blank=True)
    cancellation_time = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coaching_sessions'
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['coach', 'status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['scheduled_start']),
        ]
    
    def __str__(self):
        return f"{self.coach.user.get_display_name()} → {self.student.get_display_name()} ({self.scheduled_start.date()})"
    
    def get_absolute_url(self):
        return reverse('coaching:session_detail', kwargs={'pk': self.pk})
    
    @property
    def can_cancel(self):
        """Check if session can be cancelled (24h before start)"""
        if self.status in ['completed', 'cancelled', 'no_show']:
            return False
        now = timezone.now()
        hours_until = (self.scheduled_start - now).total_seconds() / 3600
        return hours_until >= 24
    
    @property
    def is_upcoming(self):
        """Check if session is in the future"""
        return self.scheduled_start > timezone.now() and self.status in ['pending', 'confirmed']
    
    @property
    def duration_hours(self):
        """Get duration in hours"""
        return self.duration_minutes / 60
    
    def start_session(self):
        """Mark session as started"""
        if self.status == 'confirmed':
            self.status = 'in_progress'
            self.actual_start = timezone.now()
            self.save()
            return True
        return False
    
    def complete_session(self):
        """Mark session as completed"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.actual_end = timezone.now()
            self.save()
            
            # Update coach statistics
            self.coach.total_sessions += 1
            if not CoachingSession.objects.filter(
                coach=self.coach, student=self.student, status='completed'
            ).exclude(id=self.id).exists():
                self.coach.total_students += 1
            
            self.coach.total_earnings += self.price
            self.coach.save()
            
            return True
        return False
    
    def cancel_session(self, user, reason=""):
        """Cancel the session"""
        if self.can_cancel:
            self.status = 'cancelled'
            self.cancelled_by = user
            self.cancellation_reason = reason
            self.cancellation_time = timezone.now()
            self.save()
            return True
        return False


class SessionReview(models.Model):
    """Student review of coaching session"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(CoachingSession, on_delete=models.CASCADE,
                                    related_name='review')
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='written_reviews')
    
    # Rating (1-5)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    
    # Detailed Ratings
    communication_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)],
                                               null=True, blank=True)
    knowledge_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)],
                                           null=True, blank=True)
    patience_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)],
                                          null=True, blank=True)
    
    # Written Review
    title = models.CharField(max_length=200, blank=True)
    review = models.TextField()
    
    # Recommendation
    would_recommend = models.BooleanField(default=True)
    improvement_seen = models.BooleanField(default=True)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    
    # Coach Response
    coach_response = models.TextField(blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'session_reviews'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review: {self.coach.user.get_display_name()} ({self.rating}★)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update coach's average rating
        self.coach.update_rating()


class CoachingPackage(models.Model):
    """Pre-defined coaching packages"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name='packages')
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Package Details
    number_of_sessions = models.IntegerField(validators=[MinValueValidator(1)])
    session_duration = models.IntegerField(help_text="Minutes per session")
    
    # Game specific (optional)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    
    # Pricing
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                              validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Validity
    valid_for_days = models.IntegerField(default=90, help_text="Days to use package")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coaching_packages'
        ordering = ['coach', 'total_price']
    
    def __str__(self):
        return f"{self.name} - {self.coach.user.get_display_name()}"
    
    @property
    def price_per_session(self):
        return self.total_price / self.number_of_sessions
    
    @property
    def original_price(self):
        """Calculate original price before discount"""
        if self.discount_percentage > 0:
            return self.total_price / (1 - (self.discount_percentage / 100))
        return self.total_price
    
    @property
    def savings(self):
        return self.original_price - self.total_price


class PackagePurchase(models.Model):
    """Purchased coaching package"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package = models.ForeignKey(CoachingPackage, on_delete=models.PROTECT)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='package_purchases')
    
    # Usage
    sessions_remaining = models.IntegerField()
    sessions_used = models.IntegerField(default=0)
    
    # Payment
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_intent_id = models.CharField(max_length=200, blank=True)
    
    # Validity
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        db_table = 'package_purchases'
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"{self.student.get_display_name()} - {self.package.name} ({self.sessions_remaining} left)"
    
    @property
    def is_valid(self):
        """Check if package is still valid"""
        if self.status != 'active':
            return False
        if self.sessions_remaining <= 0:
            return False
        if self.expires_at < timezone.now():
            return False
        return True
    
    def use_session(self):
        """Use one session from package"""
        if self.is_valid:
            self.sessions_remaining -= 1
            self.sessions_used += 1
            
            if self.sessions_remaining == 0:
                self.status = 'completed'
            
            self.save()
            return True
        return False