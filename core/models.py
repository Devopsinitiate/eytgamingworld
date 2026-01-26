from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import uuid


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with role-based access"""
    
    ROLE_CHOICES = [
        ('player', 'Player'),
        ('coach', 'Coach/Tutor'),
        ('organizer', 'Tournament Organizer'),
        ('admin', 'Administrator'),
        ('parent', 'Parent/Guardian'),
    ]
    
    SKILL_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('professional', 'Professional'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=30, unique=True, db_index=True)
    
    # Profile information
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    display_name = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Gaming information
    discord_username = models.CharField(max_length=100, blank=True)
    steam_id = models.CharField(max_length=100, blank=True, db_index=True)
    twitch_username = models.CharField(max_length=100, blank=True)
    
    # Role & Permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='player')
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES, default='beginner')
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_minor = models.BooleanField(default=False)
    
    # Dates
    date_joined = models.DateTimeField(default=timezone.now)
    date_of_birth = models.DateField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Contact & Location
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Parent/Guardian (for minors)
    parent_email = models.EmailField(blank=True, help_text="Required for users under 18")
    parental_consent = models.BooleanField(default=False)
    
    # Gamification
    total_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Metadata
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    private_profile = models.BooleanField(default=False)
    
    # Profile dashboard fields
    banner = models.ImageField(upload_to='banners/', null=True, blank=True)
    online_status_visible = models.BooleanField(default=True)
    activity_visible = models.BooleanField(default=True)
    statistics_visible = models.BooleanField(default=True)
    
    # Stripe integration
    stripe_customer_id = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Stripe Customer ID for payment processing"
    )
    
    # Security & Account Status
    email_verified_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the email was verified"
    )
    account_locked = models.BooleanField(
        default=False,
        help_text="Lock account due to security concerns"
    )
    account_locked_reason = models.TextField(
        blank=True,
        help_text="Reason for account lock"
    )
    failed_login_attempts = models.IntegerField(
        default=0,
        help_text="Track failed login attempts"
    )
    last_failed_login = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Last failed login attempt"
    )
    
    # Profile completeness
    profile_completed = models.BooleanField(
        default=False,
        help_text="Whether user has completed their profile"
    )
    onboarding_completed = models.BooleanField(
        default=False,
        help_text="Whether user has completed onboarding"
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['username', 'is_active']),
            models.Index(fields=['role', 'is_active']),
        ]
    
    def __str__(self):
        return self.get_display_name()
    
    def get_display_name(self):
        """Return display name or username"""
        return self.display_name or self.username or self.email.split('@')[0]
    
    def get_full_name(self):
        """Return full name or display name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.get_display_name()
    
    def get_short_name(self):
        """Return first name or display name"""
        return self.first_name or self.get_display_name()
    
    def add_points(self, points):
        """Add points and potentially level up"""
        self.total_points += points
        self.update_level()
        self.save()
    
    def update_level(self):
        """Update user level based on points (100 points per level)"""
        new_level = (self.total_points // 100) + 1
        if new_level != self.level:
            self.level = new_level
            return True
        return False
    
    def can_organize_tournaments(self):
        """Check if user can create/manage tournaments"""
        return self.role in ['organizer', 'admin']
    
    def can_coach(self):
        """Check if user can offer coaching services"""
        return self.role in ['coach', 'admin']
    
    def age(self):
        """Calculate user's age if date of birth is set"""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    def requires_parental_consent(self):
        """Check if user requires parental consent"""
        age = self.age()
        return age is not None and age < 18
    
    def verify_email(self):
        """Mark email as verified"""
        self.is_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'email_verified_at'])
    
    def lock_account(self, reason=""):
        """Lock user account"""
        self.account_locked = True
        self.account_locked_reason = reason
        self.is_active = False
        self.save(update_fields=['account_locked', 'account_locked_reason', 'is_active'])
    
    def unlock_account(self):
        """Unlock user account"""
        self.account_locked = False
        self.account_locked_reason = ""
        self.is_active = True
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked', 'account_locked_reason', 'is_active', 'failed_login_attempts'])
    
    def record_failed_login(self):
        """Record a failed login attempt"""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account("Too many failed login attempts")
        else:
            self.save(update_fields=['failed_login_attempts', 'last_failed_login'])
    
    def reset_failed_logins(self):
        """Reset failed login counter after successful login"""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.last_failed_login = None
            self.save(update_fields=['failed_login_attempts', 'last_failed_login'])
    
    def check_profile_completeness(self):
        """Check if profile is complete"""
        required_fields = [
            self.first_name,
            self.last_name,
            self.date_of_birth,
            self.country,
        ]
        
        is_complete = all(required_fields)
        
        if is_complete != self.profile_completed:
            self.profile_completed = is_complete
            self.save(update_fields=['profile_completed'])
        
        return is_complete


class Game(models.Model):
    """Games supported on the platform"""
    
    GENRE_CHOICES = [
        ('fighting', 'Fighting'),
        ('fps', 'First-Person Shooter'),
        ('moba', 'MOBA'),
        ('sports', 'Sports'),
        ('racing', 'Racing'),
        ('strategy', 'Strategy'),
        ('battle_royale', 'Battle Royale'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES)
    
    # Media
    logo = models.ImageField(upload_to='games/logos/', null=True, blank=True)
    banner = models.ImageField(upload_to='games/banners/', null=True, blank=True)
    
    # Game details
    developer = models.CharField(max_length=100, blank=True)
    release_date = models.DateField(null=True, blank=True)
    official_website = models.URLField(blank=True)
    
    # Platform support
    is_active = models.BooleanField(default=True)
    supports_teams = models.BooleanField(default=False)
    min_team_size = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    max_team_size = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'games'
        ordering = ['name']
        verbose_name = 'Game'
        verbose_name_plural = 'Games'
    
    def __str__(self):
        return self.name


class UserGameProfile(models.Model):
    """User's profile for specific games"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_profiles')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='user_profiles')
    
    # Game-specific info
    in_game_name = models.CharField(max_length=100, blank=True)
    skill_rating = models.IntegerField(default=1000, validators=[MinValueValidator(0)])
    mmr = models.IntegerField(default=1000, validators=[MinValueValidator(0)])  # Alias for skill rating
    rank = models.CharField(max_length=50, blank=True)
    
    # Statistics
    matches_played = models.IntegerField(default=0)
    matches_won = models.IntegerField(default=0)
    matches_lost = models.IntegerField(default=0)
    tournaments_participated = models.IntegerField(default=0)
    tournaments_won = models.IntegerField(default=0)
    
    # Preferences
    preferred_role = models.CharField(max_length=50, blank=True)
    is_main_game = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_game_profiles'
        unique_together = ['user', 'game']
        ordering = ['-is_main_game', '-skill_rating']
        verbose_name = 'User Game Profile'
        verbose_name_plural = 'User Game Profiles'
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_main_game=True),
                name='unique_main_game_per_user'
            )
        ]
    
    def __str__(self):
        return f"{self.user.get_display_name()} - {self.game.name}"
    
    def clean(self):
        """
        Validate that only one game profile can be main per user
        
        This enforces the main game uniqueness constraint at the model level
        to ensure data integrity regardless of how the model is saved.
        """
        from django.core.exceptions import ValidationError
        
        if self.is_main_game:
            # Check if another profile for this user is already main
            existing_main = UserGameProfile.objects.filter(
                user=self.user,
                is_main_game=True
            ).exclude(pk=self.pk)
            
            if existing_main.exists():
                raise ValidationError({
                    'is_main_game': 'Only one game profile can be set as main per user.'
                })
    
    def save(self, *args, **kwargs):
        """
        Override save to enforce main game uniqueness constraint
        
        When a profile is set as main game, automatically unset any other
        main games for the same user to maintain the uniqueness constraint.
        """
        # If this profile is being set as main, unset any other main games FIRST
        if self.is_main_game:
            # Unset other main games for this user BEFORE validation
            UserGameProfile.objects.filter(
                user=self.user,
                is_main_game=True
            ).exclude(pk=self.pk).update(is_main_game=False)
        
        # Always run validation when is_main_game is being changed
        # Check if is_main_game is being updated
        update_fields = kwargs.get('update_fields')
        if update_fields is None or 'is_main_game' in update_fields:
            self.full_clean()
        
        # Save this profile
        super().save(*args, **kwargs)
    
    @property
    def win_rate(self):
        """Calculate win rate percentage"""
        if self.matches_played == 0:
            return 0
        return round((self.matches_won / self.matches_played) * 100, 2)


class SiteSettings(models.Model):
    """Global site settings (singleton pattern)"""
    
    site_name = models.CharField(max_length=100, default='EYTGaming')
    site_tagline = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    support_email = models.EmailField(blank=True)
    
    # Social Links
    discord_server = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    twitch_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    
    # Features toggles
    registrations_open = models.BooleanField(default=True)
    tournaments_enabled = models.BooleanField(default=True)
    coaching_enabled = models.BooleanField(default=True)
    
    # Maintenance
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'site_settings'
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton)"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Load or create site settings"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj