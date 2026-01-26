"""
Team Achievement Service

This module handles the detection and awarding of team achievements.
Achievements are awarded based on tournament performance and team milestones.
"""

from django.utils import timezone
from django.db import transaction
from teams.models import Team, TeamAchievement, TeamMember, TeamAnnouncement
from notifications.models import Notification


class AchievementService:
    """Service for managing team achievements"""
    
    # Achievement type definitions with metadata
    ACHIEVEMENT_DEFINITIONS = {
        'first_win': {
            'title': 'First Victory',
            'description': 'Won your first tournament',
            'icon': '🏆',
        },
        'tournament_champion': {
            'title': 'Tournament Champion',
            'description': 'Won a tournament',
            'icon': '👑',
        },
        'undefeated': {
            'title': 'Undefeated Champion',
            'description': 'Won a tournament without losing a single match',
            'icon': '💎',
        },
        'comeback': {
            'title': 'Comeback Kings',
            'description': 'Won a tournament after dropping to the elimination bracket',
            'icon': '🔥',
        },
        'dynasty': {
            'title': 'Dynasty',
            'description': 'Won 3 tournaments in a row',
            'icon': '⭐',
        },
        'win_streak': {
            'title': 'Win Streak',
            'description': 'Won {count} matches in a row',
            'icon': '⚡',
        },
        'perfect_season': {
            'title': 'Perfect Season',
            'description': 'Won all matches in a tournament season',
            'icon': '✨',
        },
        'giant_slayer': {
            'title': 'Giant Slayer',
            'description': 'Defeated a higher-ranked team',
            'icon': '⚔️',
        },
        'getting_started': {
            'title': 'Getting Started',
            'description': 'Played your first tournament',
            'icon': '🎮',
        },
        'experienced': {
            'title': 'Experienced',
            'description': 'Played 10 tournaments',
            'icon': '🎯',
        },
        'veterans': {
            'title': 'Veterans',
            'description': 'Played 50 tournaments',
            'icon': '🛡️',
        },
        'legends': {
            'title': 'Legends',
            'description': 'Played 100 tournaments',
            'icon': '🏅',
        },
        'full_roster': {
            'title': 'Full Roster',
            'description': 'Reached maximum team capacity',
            'icon': '👥',
        },
    }
    
    @classmethod
    @transaction.atomic
    def award_achievement(cls, team, achievement_type, metadata=None):
        """
        Award an achievement to a team
        
        Args:
            team: Team instance
            achievement_type: Type of achievement (must be in ACHIEVEMENT_DEFINITIONS)
            metadata: Optional dict with achievement-specific data
        
        Returns:
            TeamAchievement instance if awarded, None if already exists
        """
        if achievement_type not in cls.ACHIEVEMENT_DEFINITIONS:
            raise ValueError(f"Invalid achievement type: {achievement_type}")
        
        # Get achievement definition
        definition = cls.ACHIEVEMENT_DEFINITIONS[achievement_type]
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Check if achievement already exists (for non-progressive achievements)
        # Progressive achievements (like win_streak) can have multiple instances
        if achievement_type not in ['win_streak']:
            existing = TeamAchievement.objects.filter(
                team=team,
                achievement_type=achievement_type
            ).first()
            
            if existing:
                return None  # Achievement already awarded
        
        # Create title and description with metadata interpolation
        title = definition['title']
        description = definition['description']
        
        # Handle dynamic descriptions (e.g., win streak count)
        if '{count}' in description and 'count' in metadata:
            description = description.format(count=metadata['count'])
        
        # Create TeamAchievement record (Requirement 15.1, 15.2)
        achievement = TeamAchievement.objects.create(
            team=team,
            achievement_type=achievement_type,
            title=title,
            description=description,
            icon=definition['icon'],
            metadata=metadata
        )
        
        # Send notifications to all active team members (Requirement 15.4)
        cls._notify_team_members(team, achievement)
        
        # Post automatic announcement to team feed (Requirement 15.4)
        cls._post_achievement_announcement(team, achievement)
        
        return achievement
    
    @classmethod
    def _notify_team_members(cls, team, achievement):
        """Send notifications to all active team members about the achievement"""
        from teams.notification_service import TeamNotificationService
        TeamNotificationService.notify_achievement_earned(team, achievement)
    
    @classmethod
    def _post_achievement_announcement(cls, team, achievement):
        """Post an automatic announcement about the achievement"""
        TeamAnnouncement.objects.create(
            team=team,
            posted_by=team.captain,
            title=f"🏆 Achievement Unlocked: {achievement.title}",
            content=f"The team has earned a new achievement: **{achievement.title}**\n\n{achievement.description}",
            priority='important',
            is_pinned=False
        )
    
    @classmethod
    def check_tournament_win_achievements(cls, team, tournament, participant):
        """
        Check and award achievements when a team wins a tournament
        
        Args:
            team: Team instance
            tournament: Tournament instance
            participant: Participant instance for the team
        """
        achievements_awarded = []
        
        # First Victory - Win your first tournament (Requirement 15.1)
        if team.tournaments_won == 1:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='first_win',
                metadata={'tournament_id': str(tournament.id)}
            )
            if achievement:
                achievements_awarded.append(achievement)
        
        # Tournament Champion - Win any tournament (Requirement 15.2)
        achievement = cls.award_achievement(
            team=team,
            achievement_type='tournament_champion',
            metadata={'tournament_id': str(tournament.id)}
        )
        if achievement:
            achievements_awarded.append(achievement)
        
        # Undefeated Champion - Win tournament without losing a match
        if participant.matches_lost == 0 and participant.matches_won > 0:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='undefeated',
                metadata={'tournament_id': str(tournament.id)}
            )
            if achievement:
                achievements_awarded.append(achievement)
        
        # Check for dynasty (3 tournaments in a row)
        cls._check_dynasty_achievement(team)
        
        return achievements_awarded
    
    @classmethod
    def check_tournament_participation_achievements(cls, team):
        """
        Check and award achievements based on tournament participation count
        
        Args:
            team: Team instance
        """
        achievements_awarded = []
        
        # Getting Started - First tournament
        if team.tournaments_played == 1:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='getting_started',
                metadata={'tournaments_played': 1}
            )
            if achievement:
                achievements_awarded.append(achievement)
        
        # Experienced - 10 tournaments
        if team.tournaments_played == 10:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='experienced',
                metadata={'tournaments_played': 10}
            )
            if achievement:
                achievements_awarded.append(achievement)
        
        # Veterans - 50 tournaments
        if team.tournaments_played == 50:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='veterans',
                metadata={'tournaments_played': 50}
            )
            if achievement:
                achievements_awarded.append(achievement)
        
        # Legends - 100 tournaments
        if team.tournaments_played == 100:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='legends',
                metadata={'tournaments_played': 100}
            )
            if achievement:
                achievements_awarded.append(achievement)
        
        return achievements_awarded
    
    @classmethod
    def check_roster_achievements(cls, team):
        """
        Check and award achievements based on roster status
        
        Args:
            team: Team instance
        """
        achievements_awarded = []
        
        # Full Roster - Reached maximum team capacity
        if team.is_full:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='full_roster',
                metadata={'max_members': team.max_members}
            )
            if achievement:
                achievements_awarded.append(achievement)
        
        return achievements_awarded
    
    @classmethod
    def check_win_streak_achievements(cls, team):
        """
        Check and award win streak achievements
        
        Args:
            team: Team instance
        """
        from django.db import models
        achievements_awarded = []
        
        # Calculate current win streak
        from tournaments.models import Match
        
        # Get team's recent matches in chronological order
        recent_matches = Match.objects.filter(
            tournament__is_team_based=True,
            status='completed'
        ).filter(
            models.Q(participant1__team=team) | models.Q(participant2__team=team)
        ).order_by('-completed_at')[:20]
        
        # Count consecutive wins from most recent
        win_streak = 0
        for match in recent_matches:
            if match.winner and (
                (match.participant1 and match.participant1.team == team and match.winner == match.participant1) or
                (match.participant2 and match.participant2.team == team and match.winner == match.participant2)
            ):
                win_streak += 1
            else:
                break
        
        # Award achievements for specific streak milestones
        if win_streak >= 20:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='win_streak',
                metadata={'count': 20, 'streak': win_streak}
            )
            if achievement:
                achievements_awarded.append(achievement)
        elif win_streak >= 10:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='win_streak',
                metadata={'count': 10, 'streak': win_streak}
            )
            if achievement:
                achievements_awarded.append(achievement)
        elif win_streak >= 5:
            achievement = cls.award_achievement(
                team=team,
                achievement_type='win_streak',
                metadata={'count': 5, 'streak': win_streak}
            )
            if achievement:
                achievements_awarded.append(achievement)
        
        return achievements_awarded
    
    @classmethod
    def _check_dynasty_achievement(cls, team):
        """Check if team has won 3 tournaments in a row"""
        from tournaments.models import Participant
        
        # Get team's last 3 tournament participations
        recent_tournaments = Participant.objects.filter(
            team=team,
            status='confirmed'
        ).select_related('tournament').order_by('-tournament__actual_end')[:3]
        
        if recent_tournaments.count() >= 3:
            # Check if all 3 were wins (final_placement == 1)
            all_wins = all(p.final_placement == 1 for p in recent_tournaments)
            
            if all_wins:
                cls.award_achievement(
                    team=team,
                    achievement_type='dynasty',
                    metadata={
                        'tournament_ids': [str(p.tournament.id) for p in recent_tournaments]
                    }
                )
