from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from core.models import User, Game
from teams.models import Team
import uuid
from datetime import timedelta
import json
from .cache_utils import CacheInvalidationMixin


class Tournament(models.Model):
    """Main tournament model"""
    
    FORMAT_CHOICES = [
        ('single_elim', 'Single Elimination'),
        ('double_elim', 'Double Elimination'),
        ('swiss', 'Swiss System'),
        ('round_robin', 'Round Robin'),
        ('group_stage', 'Group Stage + Playoffs'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('registration', 'Registration Open'),
        ('check_in', 'Check-in Period'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TYPE_CHOICES = [
        ('online', 'Online'),
        ('local', 'Local/Venue'),
        ('hybrid', 'Hybrid'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    rules = models.TextField(blank=True, help_text="Tournament specific rules")
    
    # Tournament Configuration
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name='tournaments')
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='single_elim')
    tournament_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='online')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Organizer & Venue
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_tournaments')
    venue = models.ForeignKey('venues.Venue', on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='tournaments')
    
    # Participants
    is_team_based = models.BooleanField(default=False)
    min_participants = models.IntegerField(default=4, validators=[MinValueValidator(2)])
    max_participants = models.IntegerField(default=32, validators=[MinValueValidator(2)])
    team_size = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Registration
    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()
    requires_approval = models.BooleanField(default=False)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Schedule
    check_in_start = models.DateTimeField(help_text="When check-in opens")
    start_datetime = models.DateTimeField(help_text="Tournament start time")
    estimated_end = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Prize & Settings
    prize_pool = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    prize_distribution = models.JSONField(default=dict, blank=True, 
                                          help_text="e.g., {'1st': 50, '2nd': 30, '3rd': 20}")
    
    # Bracket Settings
    seeding_method = models.CharField(max_length=20, choices=[
        ('random', 'Random'),
        ('skill', 'Skill-based'),
        ('manual', 'Manual'),
        ('registration', 'Registration Order'),
    ], default='random')
    
    best_of = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(7)],
                                   help_text="Best of X games per match")
    
    # Media
    banner = models.ImageField(upload_to='tournaments/banners/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='tournaments/thumbnails/', null=True, blank=True)
    
    # Visibility & Access
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    requires_verification = models.BooleanField(default=False, 
                                                 help_text="Only verified users can join")
    skill_requirement = models.CharField(max_length=20, blank=True, 
                                         help_text="Minimum skill level required")
    
    # Streaming
    stream_url = models.URLField(blank=True, help_text="Twitch/YouTube stream link")
    discord_invite = models.URLField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_registered = models.IntegerField(default=0)
    total_checked_in = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    
    # Enhanced metadata for UI
    primary_color = models.CharField(max_length=7, default='#b91c1c', help_text="Hex color code")
    secondary_color = models.CharField(max_length=7, default='#111827', help_text="Hex color code")
    meta_description = models.TextField(max_length=160, blank=True, help_text="SEO description")
    social_image = models.ImageField(upload_to='tournaments/social/', null=True, blank=True)
    
    class Meta:
        db_table = 'tournaments'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['status', '-start_datetime']),
            models.Index(fields=['game', 'status']),
            models.Index(fields=['is_public', 'is_featured']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('tournaments:detail', kwargs={'slug': self.slug})
    
    @property
    def is_registration_open(self):
        now = timezone.now()
        return (self.status == 'registration' and 
                self.registration_start <= now <= self.registration_end and
                self.total_registered < self.max_participants)
    
    @property
    def is_full(self):
        return self.total_registered >= self.max_participants
    
    @property
    def is_check_in_open(self):
        now = timezone.now()
        return self.status == 'check_in' and self.check_in_start <= now < self.start_datetime
    
    @property
    def spots_remaining(self):
        return max(0, self.max_participants - self.total_registered)
    
    @property
    def registration_progress(self):
        if self.max_participants == 0:
            return 0
        return min(100, (self.total_registered / self.max_participants) * 100)
    
    def can_user_register(self, user):
        """Check if user can register for tournament"""
        # Check if already registered first
        if Participant.objects.filter(tournament=self, user=user).exists():
            return False, "Already registered"
        
        # Check if tournament is full
        if self.is_full:
            return False, "Tournament is full"
        
        # Check if registration is open (status and dates)
        now = timezone.now()
        if self.status != 'registration':
            return False, "Registration is not open"
        
        if now < self.registration_start:
            return False, "Registration has not started yet"
        
        if now > self.registration_end:
            return False, "Registration has closed"
        
        # Check verification requirement
        if self.requires_verification and not user.is_verified:
            return False, "Verified account required"
        
        return True, "Can register"
    
    def get_registrations_today(self):
        """Get number of registrations in the last 24 hours"""
        yesterday = timezone.now() - timezone.timedelta(days=1)
        return self.participants.filter(registered_at__gte=yesterday).count()
    
    def get_timeline_phases(self):
        """Get tournament phases for timeline display"""
        now = timezone.now()
        phases = []
        
        phases.append({
            'name': 'Registration',
            'start_time': self.registration_start,
            'end_time': self.registration_end,
            'status': 'completed' if now > self.registration_end else 'active' if now >= self.registration_start else 'upcoming',
            'description': f'Sign up period (${self.registration_fee} entry fee)',
            'icon': 'person_add'
        })
        
        phases.append({
            'name': 'Check-in',
            'start_time': self.check_in_start,
            'end_time': self.start_datetime,
            'status': 'completed' if now > self.start_datetime else 'active' if now >= self.check_in_start else 'upcoming',
            'description': 'Confirm participation',
            'icon': 'check_circle'
        })
        
        phases.append({
            'name': 'Tournament',
            'start_time': self.start_datetime,
            'end_time': self.estimated_end or self.actual_end,
            'status': 'completed' if self.status == 'completed' else 'active' if self.status == 'in_progress' else 'upcoming',
            'description': f'{self.get_format_display()} format',
            'icon': 'emoji_events'
        })
        
        return phases
    
    def get_prize_breakdown(self):
        """Get detailed prize breakdown with amounts and percentages"""
        if self.prize_pool <= 0:
            return []
        
        # Default distribution if none specified
        default_distribution = {
            '1st': 50,
            '2nd': 30, 
            '3rd': 20
        }
        
        distribution = self.prize_distribution if self.prize_distribution else default_distribution
        breakdown = []
        
        # Define placement order and styling
        placement_styles = {
            '1st': {'icon': '🥇', 'color': 'gold', 'gradient': 'from-yellow-400 to-yellow-600'},
            '2nd': {'icon': '🥈', 'color': 'silver', 'gradient': 'from-gray-300 to-gray-500'},
            '3rd': {'icon': '🥉', 'color': 'bronze', 'gradient': 'from-amber-600 to-amber-800'},
            '4th': {'icon': '4️⃣', 'color': 'fourth', 'gradient': 'from-blue-500 to-blue-700'},
            '5th': {'icon': '5️⃣', 'color': 'fifth', 'gradient': 'from-purple-500 to-purple-700'},
            '6th': {'icon': '6️⃣', 'color': 'sixth', 'gradient': 'from-indigo-500 to-indigo-700'},
            '7th': {'icon': '7️⃣', 'color': 'seventh', 'gradient': 'from-pink-500 to-pink-700'},
            '8th': {'icon': '8️⃣', 'color': 'eighth', 'gradient': 'from-green-500 to-green-700'},
        }
        
        # Sort placements by numeric value
        sorted_placements = sorted(distribution.items(), key=lambda x: self._extract_placement_number(x[0]))
        
        for placement, percentage in sorted_placements:
            amount = float(self.prize_pool) * (float(percentage) / 100)
            style = placement_styles.get(placement, {
                'icon': '🏆', 
                'color': 'default', 
                'gradient': 'from-gray-600 to-gray-800'
            })
            
            breakdown.append({
                'placement': placement,
                'percentage': percentage,
                'amount': amount,
                'formatted_amount': f"${amount:,.2f}",
                'icon': style['icon'],
                'color': style['color'],
                'gradient': style['gradient'],
                'is_top_three': placement in ['1st', '2nd', '3rd']
            })
        
        return breakdown
    
    def _extract_placement_number(self, placement):
        """Extract numeric value from placement string for sorting"""
        import re
        match = re.search(r'\d+', placement)
        return int(match.group()) if match else 999
    
    def get_non_monetary_prizes(self):
        """Get list of non-monetary prizes if any"""
        # This could be extended to support non-monetary prizes
        # For now, return empty list but structure is ready for future enhancement
        return []
    
    def has_prize_pool(self):
        """Check if tournament has any prizes (monetary or non-monetary)"""
        return self.prize_pool > 0 or len(self.get_non_monetary_prizes()) > 0
    
    def start_tournament(self):
        """Initialize tournament and create bracket"""
        if self.status != 'check_in':
            return False
        
        self.status = 'in_progress'
        self.save()
        
        # Create bracket structure
        self.create_bracket()
        return True
    
    def create_bracket(self):
        """Create bracket based on tournament format"""
        from .services.bracket import generate_bracket
        
        participants = list(self.participants.filter(checked_in=True, status='confirmed'))
        generator = BracketGenerator(self, participants)
        
        if self.format == 'single_elim':
            generator.generate_single_elimination()
        elif self.format == 'double_elim':
            generator.generate_double_elimination()
        elif self.format == 'swiss':
            generator.generate_swiss_rounds()
        elif self.format == 'round_robin':
            generator.generate_round_robin()


class Participant(CacheInvalidationMixin, models.Model):
    """Tournament participant (user or team)"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('pending_payment', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('disqualified', 'Disqualified'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='participants')
    
    # Either user OR team (not both)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                             related_name='tournament_participations')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True,
                             related_name='tournament_participations')
    
    # Registration details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    seed = models.IntegerField(null=True, blank=True, help_text="Seeding position")
    
    # Check-in
    checked_in = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    matches_won = models.IntegerField(default=0)
    matches_lost = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    games_lost = models.IntegerField(default=0)
    
    # Placement
    final_placement = models.IntegerField(null=True, blank=True)
    prize_won = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Payment
    has_paid = models.BooleanField(default=False)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Metadata
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Admin notes")
    
    class Meta:
        db_table = 'tournament_participants'
        unique_together = [
            ['tournament', 'user'],
            ['tournament', 'team'],
        ]
        ordering = ['seed', 'registered_at']
    
    def __str__(self):
        name = self.team.name if self.team else self.user.get_display_name()
        return f"{name} - {self.tournament.name}"
    
    @property
    def display_name(self):
        return self.team.name if self.team else self.user.get_display_name()
    
    @property
    def win_rate(self):
        total = self.matches_won + self.matches_lost
        if total == 0:
            return 0
        return round((self.matches_won / total) * 100, 2)
    
    def check_in_participant(self):
        """Mark participant as checked in"""
        if not self.tournament.is_check_in_open:
            return False
        
        self.checked_in = True
        self.check_in_time = timezone.now()
        self.save()
        
        self.tournament.total_checked_in += 1
        self.tournament.save()
        return True


class Bracket(models.Model):
    """Bracket structure for tournament"""
    
    BRACKET_TYPE_CHOICES = [
        ('main', 'Main Bracket'),
        ('losers', 'Losers Bracket'),
        ('groups', 'Group Stage'),
        ('finals', 'Finals'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='brackets')
    
    bracket_type = models.CharField(max_length=20, choices=BRACKET_TYPE_CHOICES, default='main')
    name = models.CharField(max_length=100)
    
    # Structure
    total_rounds = models.IntegerField(default=0)
    current_round = models.IntegerField(default=1)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tournament_brackets'
        ordering = ['tournament', 'bracket_type']
    
    def __str__(self):
        return f"{self.tournament.name} - {self.name}"
    
    @property
    def completed_matches(self):
        """Count of completed matches in this bracket"""
        return self.matches.filter(status='completed').count()
    
    @property
    def total_matches(self):
        """Total number of matches in this bracket"""
        return self.matches.count()


class Match(CacheInvalidationMixin, models.Model):
    """Individual match in tournament"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ready', 'Ready to Start'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name='matches')
    
    # Match position
    round_number = models.IntegerField()
    match_number = models.IntegerField(help_text="Position within round")
    
    # Participants
    participant1 = models.ForeignKey(Participant, on_delete=models.CASCADE, 
                                     related_name='matches_as_p1', null=True, blank=True)
    participant2 = models.ForeignKey(Participant, on_delete=models.CASCADE,
                                     related_name='matches_as_p2', null=True, blank=True)
    
    # Winner/Next match progression
    winner = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='won_matches')
    loser = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='lost_matches')
    
    # For bracket progression
    next_match_winner = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='previous_winner_matches')
    next_match_loser = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='previous_loser_matches')
    
    # Score
    score_p1 = models.IntegerField(default=0)
    score_p2 = models.IntegerField(default=0)
    
    # Status & Schedule
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_time = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_grand_finals = models.BooleanField(default=False)
    bracket_reset = models.BooleanField(default=False, help_text="Double elim grand finals reset")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tournament_matches'
        ordering = ['round_number', 'match_number']
        indexes = [
            models.Index(fields=['tournament', 'status']),
            models.Index(fields=['bracket', 'round_number']),
        ]
        verbose_name_plural = 'Matches'
    
    def __str__(self):
        p1_name = self.participant1.display_name if self.participant1 else "TBD"
        p2_name = self.participant2.display_name if self.participant2 else "TBD"
        return f"R{self.round_number}M{self.match_number}: {p1_name} vs {p2_name}"
    
    @property
    def is_ready(self):
        """Check if both participants are assigned"""
        return self.participant1 is not None and self.participant2 is not None
    
    @property
    def is_bye(self):
        """Check if this is a bye match (only one participant)"""
        return (self.participant1 is not None) != (self.participant2 is not None)
    
    def report_score(self, score_p1, score_p2, reporter=None):
        """Report match result"""
        if self.status == 'completed':
            return False, "Match already completed"
        
        if not self.is_ready:
            return False, "Both participants must be assigned"
        
        self.score_p1 = score_p1
        self.score_p2 = score_p2
        
        # Determine winner
        if score_p1 > score_p2:
            self.winner = self.participant1
            self.loser = self.participant2
        elif score_p2 > score_p1:
            self.winner = self.participant2
            self.loser = self.participant1
        else:
            return False, "Scores cannot be tied"
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update participant stats
        self.participant1.matches_won += 1 if self.winner == self.participant1 else 0
        self.participant1.matches_lost += 1 if self.loser == self.participant1 else 0
        self.participant1.games_won += score_p1
        self.participant1.games_lost += score_p2
        self.participant1.save()
        
        self.participant2.matches_won += 1 if self.winner == self.participant2 else 0
        self.participant2.matches_lost += 1 if self.loser == self.participant2 else 0
        self.participant2.games_won += score_p2
        self.participant2.games_lost += score_p1
        self.participant2.save()
        
        # Update team statistics if team-based tournament (Requirement 13.3, 13.4)
        if self.tournament.is_team_based:
            self._update_team_statistics()
        
        # Progress bracket
        self.progress_bracket()
        
        return True, "Match result recorded"
    
    def _update_team_statistics(self):
        """Update team statistics on match completion (Requirement 13.3, 13.4)"""
        from teams.models import Team, TeamMember
        from teams.achievement_service import AchievementService
        
        # Update team statistics for both teams
        for participant in [self.participant1, self.participant2]:
            if not participant or not participant.team:
                continue
            
            team = participant.team
            is_winner = participant == self.winner
            
            # Update team match statistics (Requirement 13.3)
            if is_winner:
                team.total_wins += 1
            else:
                team.total_losses += 1
            team.save()
            
            # Update team member statistics for participating members (Requirement 13.4)
            # All active team members get credit for the match
            active_members = team.members.filter(status='active')
            for member in active_members:
                member.matches_played += 1
                if is_winner:
                    member.matches_won += 1
                member.save()
            
            # Check and award achievements (Requirement 13.4)
            AchievementService.check_win_streak_achievements(team)
            
            # Post automatic announcement about match result (Requirement 13.4)
            self._post_match_result_announcement(team, is_winner)
    
    def _post_match_result_announcement(self, team, is_winner):
        """Post automatic announcement about match result to team feed (Requirement 13.4)"""
        from teams.models import TeamAnnouncement
        
        result_text = "won" if is_winner else "lost"
        opponent = self.participant2 if self.participant1 and self.participant1.team == team else self.participant1
        opponent_name = opponent.display_name if opponent else "Unknown"
        
        score_text = f"{self.score_p1}-{self.score_p2}"
        if self.participant2 and self.participant2.team == team:
            score_text = f"{self.score_p2}-{self.score_p1}"
        
        TeamAnnouncement.objects.create(
            team=team,
            posted_by=team.captain,
            title=f"Match Result: {result_text.title()} vs {opponent_name}",
            content=f"The team {result_text} against {opponent_name} with a score of {score_text} in {self.tournament.name} (Round {self.round_number}).",
            priority='normal',
            is_pinned=False
        )
    
    def progress_bracket(self):
        """Move winner/loser to next matches"""
        if self.next_match_winner and self.winner:
            # Assign winner to next match
            if not self.next_match_winner.participant1:
                self.next_match_winner.participant1 = self.winner
            elif not self.next_match_winner.participant2:
                self.next_match_winner.participant2 = self.winner
            self.next_match_winner.save()
        
        if self.next_match_loser and self.loser:
            # Assign loser to losers bracket
            if not self.next_match_loser.participant1:
                self.next_match_loser.participant1 = self.loser
            elif not self.next_match_loser.participant2:
                self.next_match_loser.participant2 = self.loser
            self.next_match_loser.save()


class MatchDispute(models.Model):
    """Handle match disputes"""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='disputes')
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_disputes')
    reason = models.TextField()
    evidence = models.FileField(upload_to='disputes/', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    admin_notes = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='resolved_disputes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'match_disputes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Dispute #{self.id} - {self.match}"


class Payment(models.Model):
    """Record of a payment attempt for a participant's registration."""

    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('paystack', 'Paystack'),
        ('local', 'Local/Manual')
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('charged', 'Charged'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider_transaction_id = models.CharField(max_length=200, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tournament_payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} - {self.provider} - {self.status}"


class TournamentShare(models.Model):
    """Track social shares of tournaments"""
    
    PLATFORM_CHOICES = [
        ('twitter', 'Twitter'),
        ('discord', 'Discord'),
        ('direct', 'Direct Link'),
        ('facebook', 'Facebook'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='shares')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    shared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'tournament_shares'
        ordering = ['-shared_at']
        indexes = [
            models.Index(fields=['tournament', 'platform']),
            models.Index(fields=['shared_at']),
        ]
    
    def __str__(self):
        return f"{self.tournament.name} shared on {self.platform}"


class WebhookEvent(models.Model):
    """Stores raw webhook payloads for reconciliation and debugging."""

    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('paystack', 'Paystack'),
        ('other', 'Other')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='other')
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_events'
        ordering = ['-received_at']

    def __str__(self):
        return f"WebhookEvent {self.provider} @ {self.received_at.isoformat()}"