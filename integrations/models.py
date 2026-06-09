from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class ExternalProvider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Provider name (e.g. start.gg, PandaScore)")
    base_url = models.URLField(help_text="API base URL")
    api_key = models.TextField(blank=True, help_text="Encrypted API key / personal access token")
    is_active = models.BooleanField(default=True)
    rate_limit_per_min = models.IntegerField(default=60, help_text="Max requests per minute")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'external_providers'

    def __str__(self):
        return self.name


class ExternalTournament(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ExternalProvider, on_delete=models.CASCADE, related_name='tournaments')
    external_id = models.CharField(max_length=200, help_text="Provider's tournament ID")
    title = models.CharField(max_length=500)
    game = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    local_tournament = models.ForeignKey(
        'tournaments.Tournament', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='external_references'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'external_tournaments'
        unique_together = ['provider', 'external_id']
        indexes = [
            models.Index(fields=['provider', 'status']),
        ]

    def __str__(self):
        return f"[{self.provider.name}] {self.title}"


class ExternalPlayer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ExternalProvider, on_delete=models.CASCADE, related_name='players')
    external_id = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    game = models.CharField(max_length=200, blank=True)
    avatar_url = models.URLField(blank=True)
    stats = models.JSONField(default=dict, blank=True, help_text="Provider-specific stats (rank, win rate, etc.)")
    local_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='external_profiles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'external_players'
        unique_together = ['provider', 'external_id']
        indexes = [
            models.Index(fields=['provider', 'game']),
        ]

    def __str__(self):
        return f"[{self.provider.name}] {self.username}"


class ExternalMatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ExternalProvider, on_delete=models.CASCADE, related_name='matches')
    external_id = models.CharField(max_length=200)
    tournament = models.ForeignKey(ExternalTournament, on_delete=models.CASCADE, related_name='matches')
    round = models.IntegerField(default=1)
    players = models.JSONField(default=list, help_text="List of player external_ids or usernames")
    scores = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, default='pending')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'external_matches'
        unique_together = ['provider', 'external_id']

    def __str__(self):
        return f"[{self.provider.name}] Match {self.external_id}"


class SyncLog(models.Model):
    SYNC_TYPES = [
        ('tournament', 'Tournament Sync'),
        ('player', 'Player Sync'),
        ('standings', 'Standings Sync'),
        ('discovery', 'Tournament Discovery'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ExternalProvider, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, default='running')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    items_processed = models.IntegerField(default=0)

    class Meta:
        db_table = 'sync_logs'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.sync_type} - {self.provider.name} - {self.status}"
