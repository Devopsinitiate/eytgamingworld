from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from core.models import User, Game
import uuid


class Team(models.Model):
    """Gaming team model"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('disbanded', 'Disbanded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Info
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    tag = models.CharField(max_length=10, help_text="Team abbreviation (e.g., TSM, C9)")
    description = models.TextField(blank=True)
    
    # Team Details
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name='teams')
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captained_teams')
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='owned_teams', help_text="Economic owner (usually a celebrity)")
    
    # Media
    logo = models.ImageField(upload_to='teams/logos/', null=True, blank=True)
    banner = models.ImageField(upload_to='teams/banners/', null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_recruiting = models.BooleanField(default=False)
    
    # Celebrity Ownership
    is_celebrity_owned = models.BooleanField(default=False, help_text="Flagged for premium display")
    market_value = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                       help_text="Calculated team valuation in USD")
    is_listed_for_sale = models.BooleanField(default=False)
    sale_price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price_points = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Social
    discord_server = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    twitch_url = models.URLField(blank=True)
    
    # Settings
    is_public = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    max_members = models.IntegerField(default=10)
    
    # Statistics
    tournaments_played = models.IntegerField(default=0)
    tournaments_won = models.IntegerField(default=0)
    total_wins = models.IntegerField(default=0)
    total_losses = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teams'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['game', 'status']),
            models.Index(fields=['is_public', 'is_recruiting']),
        ]
    
    def __str__(self):
        return f"{self.name} [{self.tag}]"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('teams:detail', kwargs={'slug': self.slug})
    
    @property
    def member_count(self):
        return self.members.filter(status='active').count()
    
    @property
    def is_full(self):
        return self.member_count >= self.max_members
    
    @property
    def win_rate(self):
        total = self.total_wins + self.total_losses
        if total == 0:
            return 0
        return round((self.total_wins / total) * 100, 2)

    @property
    def valuation_tier(self):
        """Return a tier label based on market_value."""
        v = self.market_value
        if v >= 1_000_000:
            return 'platinum'
        elif v >= 100_000:
            return 'gold'
        elif v >= 10_000:
            return 'silver'
        elif v > 0:
            return 'bronze'
        return 'unvalued'

    def can_manage(self, user):
        """Check if user has management rights over this team."""
        if not user or not user.is_authenticated:
            return False
        return (
            user == self.captain or
            user == self.owner or
            user.is_staff or
            self.members.filter(user=user, role__in=['captain', 'co_captain']).exists()
        )


class TeamTransfer(models.Model):
    """Record of team ownership transfer (celebrity ecosystem)."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='transfers')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfers_out')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfers_in')
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_transfers')

    price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_points = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'team_transfers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.team.name}: {self.from_user} → {self.to_user}"


class TeamMember(models.Model):
    """Team membership model"""
    
    ROLE_CHOICES = [
        ('captain', 'Captain'),
        ('co_captain', 'Co-Captain'),
        ('member', 'Member'),
        ('substitute', 'Substitute'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('removed', 'Removed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Statistics (as team member)
    matches_played = models.IntegerField(default=0)
    matches_won = models.IntegerField(default=0)
    
    # Dates
    joined_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, help_text="Admin/Captain notes")
    
    class Meta:
        db_table = 'team_members'
        unique_together = ['team', 'user']
        ordering = ['role', '-joined_at']
    
    def __str__(self):
        return f"{self.user.get_display_name()} - {self.team.name}"
    
    def is_captain_or_co_captain(self):
        return self.role in ['captain', 'co_captain']


class TeamInvite(models.Model):
    """Team invitation model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invites')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_invites')
    
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'team_invites'
        ordering = ['-created_at']
        unique_together = ['team', 'invited_user', 'status']
    
    def __str__(self):
        return f"{self.team.name} → {self.invited_user.get_display_name()}"


class TeamAnnouncement(models.Model):
    """Team announcement model for team communication"""
    
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='announcements')
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_announcements')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    is_pinned = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'team_announcements'
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['team', '-created_at']),
            models.Index(fields=['team', 'is_pinned']),
        ]
    
    def __str__(self):
        return f"{self.team.name} - {self.title}"


class TeamAchievement(models.Model):
    """Team achievement model for gamification"""
    
    ACHIEVEMENT_TYPE_CHOICES = [
        ('first_win', 'First Victory'),
        ('tournament_champion', 'Tournament Champion'),
        ('undefeated', 'Undefeated Champion'),
        ('comeback', 'Comeback Kings'),
        ('dynasty', 'Dynasty'),
        ('win_streak', 'Win Streak'),
        ('perfect_season', 'Perfect Season'),
        ('giant_slayer', 'Giant Slayer'),
        ('getting_started', 'Getting Started'),
        ('experienced', 'Experienced'),
        ('veterans', 'Veterans'),
        ('legends', 'Legends'),
        ('full_roster', 'Full Roster'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPE_CHOICES)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=100, help_text="Icon identifier or emoji")
    metadata = models.JSONField(default=dict, blank=True, help_text="Achievement-specific data")
    
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'team_achievements'
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['team', '-earned_at']),
            models.Index(fields=['achievement_type']),
        ]
        unique_together = ['team', 'achievement_type', 'metadata']
    
    def __str__(self):
        return f"{self.team.name} - {self.title}"