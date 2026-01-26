"""
Service layer for dashboard functionality.

This module provides services for statistics calculation, caching, and data aggregation.
"""

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Count, Q, Avg, Min
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import uuid


class StatisticsService:
    """
    Service for calculating and caching user statistics.
    
    Provides methods for aggregating tournament participation data,
    calculating win rates, and tracking performance trends.
    """
    
    # Cache TTL in seconds (1 hour)
    CACHE_TTL = 3600
    
    @classmethod
    def get_user_statistics(cls, user_id: uuid.UUID) -> Dict:
        """
        Get aggregated statistics for a user across all games.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dictionary containing:
                - total_tournaments: Total tournaments participated in
                - total_matches: Total matches played
                - matches_won: Total matches won
                - matches_lost: Total matches lost
                - win_rate: Overall win rate percentage
                - total_prize_won: Total prize money won
                - top_3_finishes: Number of top 3 placements
                - average_placement: Average tournament placement
        
        **Validates: Requirements 3.1, 3.5**
        """
        cache_key = f"user_stats:{user_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Import here to avoid circular imports
        from tournaments.models import Participant
        
        # Get all participations for this user
        participations = Participant.objects.filter(
            user_id=user_id,
            status='confirmed'
        ).select_related('tournament')
        
        # Calculate statistics
        total_tournaments = participations.count()
        
        # Aggregate match statistics
        aggregates = participations.aggregate(
            total_matches_won=Sum('matches_won'),
            total_matches_lost=Sum('matches_lost'),
            total_prize=Sum('prize_won'),
            avg_placement=Avg('final_placement')
        )
        
        matches_won = aggregates['total_matches_won'] or 0
        matches_lost = aggregates['total_matches_lost'] or 0
        total_matches = matches_won + matches_lost
        
        # Calculate win rate
        win_rate = cls.calculate_win_rate(user_id)
        
        # Count top 3 finishes
        top_3_finishes = participations.filter(
            final_placement__lte=3,
            final_placement__isnull=False
        ).count()
        
        stats = {
            'total_tournaments': total_tournaments,
            'total_matches': total_matches,
            'matches_won': matches_won,
            'matches_lost': matches_lost,
            'win_rate': win_rate,
            'total_prize_won': aggregates['total_prize'] or Decimal('0.00'),
            'top_3_finishes': top_3_finishes,
            'average_placement': round(aggregates['avg_placement'], 2) if aggregates['avg_placement'] else None,
        }
        
        # Cache the result
        cache.set(cache_key, stats, cls.CACHE_TTL)
        
        return stats
    
    @classmethod
    def get_game_statistics(cls, user_id: uuid.UUID, game_id: uuid.UUID) -> Dict:
        """
        Get statistics for a user in a specific game.
        
        Args:
            user_id: UUID of the user
            game_id: UUID of the game
            
        Returns:
            Dictionary containing game-specific statistics:
                - tournaments_participated: Tournaments for this game
                - matches_won: Matches won in this game
                - matches_lost: Matches lost in this game
                - win_rate: Win rate for this game
                - total_prize_won: Prize money won in this game
                - best_placement: Best tournament placement
        
        **Validates: Requirements 3.2**
        """
        cache_key = f"user_game_stats:{user_id}:{game_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Import here to avoid circular imports
        from tournaments.models import Participant
        
        # Get participations for this game
        participations = Participant.objects.filter(
            user_id=user_id,
            tournament__game_id=game_id,
            status='confirmed'
        ).select_related('tournament')
        
        # Calculate statistics
        tournaments_participated = participations.count()
        
        aggregates = participations.aggregate(
            total_matches_won=Sum('matches_won'),
            total_matches_lost=Sum('matches_lost'),
            total_prize=Sum('prize_won'),
            best_placement=Min('final_placement')
        )
        
        matches_won = aggregates['total_matches_won'] or 0
        matches_lost = aggregates['total_matches_lost'] or 0
        total_matches = matches_won + matches_lost
        
        # Calculate win rate for this game
        if total_matches > 0:
            win_rate = round((matches_won / total_matches) * 100, 2)
        else:
            win_rate = 0.0
        
        stats = {
            'tournaments_participated': tournaments_participated,
            'matches_won': matches_won,
            'matches_lost': matches_lost,
            'total_matches': total_matches,
            'win_rate': win_rate,
            'total_prize_won': aggregates['total_prize'] or Decimal('0.00'),
            'best_placement': aggregates['best_placement'],
        }
        
        # Cache the result
        cache.set(cache_key, stats, cls.CACHE_TTL)
        
        return stats
    
    @classmethod
    def get_tournament_history(cls, user_id: uuid.UUID, filters: Optional[Dict] = None):
        """
        Get tournament history for a user with optional filtering.
        
        Args:
            user_id: UUID of the user
            filters: Optional dictionary with keys:
                - game_id: Filter by game UUID
                - date_from: Filter tournaments after this date
                - date_to: Filter tournaments before this date
                - placement_min: Minimum placement (e.g., 1 for winners only)
                - placement_max: Maximum placement (e.g., 3 for top 3)
                
        Returns:
            QuerySet of Participant objects with related tournament data
        
        **Validates: Requirements 3.3, 5.1, 5.2**
        """
        # Import here to avoid circular imports
        from tournaments.models import Participant
        
        queryset = Participant.objects.filter(
            user_id=user_id,
            status='confirmed'
        ).select_related('tournament', 'tournament__game').order_by('-tournament__start_datetime')
        
        if filters:
            # Filter by game - handle invalid UUIDs gracefully
            if 'game_id' in filters and filters['game_id']:
                try:
                    queryset = queryset.filter(tournament__game_id=filters['game_id'])
                except (ValueError, TypeError, ValidationError):
                    # Invalid UUID format - ignore this filter
                    pass
            
            # Filter by date range - handle invalid dates gracefully
            if 'date_from' in filters and filters['date_from']:
                try:
                    queryset = queryset.filter(tournament__start_datetime__gte=filters['date_from'])
                except (ValueError, TypeError, ValidationError):
                    # Invalid date format - ignore this filter
                    pass
            
            if 'date_to' in filters and filters['date_to']:
                try:
                    queryset = queryset.filter(tournament__start_datetime__lte=filters['date_to'])
                except (ValueError, TypeError, ValidationError):
                    # Invalid date format - ignore this filter
                    pass
            
            # Filter by placement - handle invalid numbers gracefully
            if 'placement_min' in filters and filters['placement_min']:
                try:
                    placement_min = int(filters['placement_min'])
                    if placement_min > 0:  # Only positive placements are valid
                        queryset = queryset.filter(
                            final_placement__gte=placement_min,
                            final_placement__isnull=False
                        )
                except (ValueError, TypeError):
                    # Invalid number format - ignore this filter
                    pass
            
            if 'placement_max' in filters and filters['placement_max']:
                try:
                    placement_max = int(filters['placement_max'])
                    if placement_max > 0:  # Only positive placements are valid
                        queryset = queryset.filter(
                            final_placement__lte=placement_max,
                            final_placement__isnull=False
                        )
                except (ValueError, TypeError):
                    # Invalid number format - ignore this filter
                    pass
        
        return queryset
    
    @classmethod
    def calculate_win_rate(cls, user_id: uuid.UUID, game_id: Optional[uuid.UUID] = None) -> float:
        """
        Calculate win rate percentage for a user.
        
        Args:
            user_id: UUID of the user
            game_id: Optional UUID of game to filter by
            
        Returns:
            Win rate as a percentage (0.0 to 100.0)
        
        **Validates: Requirements 3.5**
        """
        # Import here to avoid circular imports
        from tournaments.models import Participant
        
        queryset = Participant.objects.filter(
            user_id=user_id,
            status='confirmed'
        )
        
        if game_id:
            queryset = queryset.filter(tournament__game_id=game_id)
        
        aggregates = queryset.aggregate(
            total_won=Sum('matches_won'),
            total_lost=Sum('matches_lost')
        )
        
        matches_won = aggregates['total_won'] or 0
        matches_lost = aggregates['total_lost'] or 0
        total_matches = matches_won + matches_lost
        
        if total_matches == 0:
            return 0.0
        
        win_rate = (matches_won / total_matches) * 100
        return round(win_rate, 2)
    
    @classmethod
    def get_performance_trend(cls, user_id: uuid.UUID, days: int = 30) -> List[Dict]:
        """
        Get performance trend data for the last N days.
        
        Args:
            user_id: UUID of the user
            days: Number of days to look back (default 30)
            
        Returns:
            List of dictionaries with date and win_rate for each day with matches
        
        **Validates: Requirements 3.4**
        """
        cache_key = f"user_performance_trend:{user_id}:{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Import here to avoid circular imports
        from tournaments.models import Match
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all matches for this user in the date range
        matches = Match.objects.filter(
            Q(participant1__user_id=user_id) | Q(participant2__user_id=user_id),
            status='completed',
            completed_at__gte=start_date,
            completed_at__lte=end_date
        ).select_related('participant1', 'participant2', 'winner').order_by('completed_at')
        
        # Group by date and calculate win rate
        trend_data = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            day_matches = [m for m in matches if m.completed_at.date() == current_date]
            
            if day_matches:
                wins = sum(1 for m in day_matches if m.winner and (
                    (m.participant1 and m.participant1.user_id == user_id and m.winner == m.participant1) or
                    (m.participant2 and m.participant2.user_id == user_id and m.winner == m.participant2)
                ))
                total = len(day_matches)
                win_rate = round((wins / total) * 100, 2) if total > 0 else 0.0
                
                trend_data.append({
                    'date': current_date.isoformat(),
                    'matches': total,
                    'wins': wins,
                    'win_rate': win_rate
                })
            
            current_date += timedelta(days=1)
        
        # Cache the result
        cache.set(cache_key, trend_data, cls.CACHE_TTL)
        
        return trend_data
    
    @classmethod
    def invalidate_cache(cls, user_id: uuid.UUID) -> None:
        """
        Invalidate all cached statistics for a user.
        
        Args:
            user_id: UUID of the user
        
        **Validates: Requirements 16.3**
        """
        # Invalidate main stats cache
        cache.delete(f"user_stats:{user_id}")
        
        # Invalidate performance trend cache (for common day ranges)
        for days in [7, 14, 30, 60, 90]:
            cache.delete(f"user_performance_trend:{user_id}:{days}")
        
        # Note: We can't easily invalidate all game-specific caches without knowing
        # which games the user has played. This could be improved by maintaining
        # a set of cache keys per user, but for now we'll rely on TTL expiration.


class ActivityService:
    """
    Service for recording and retrieving user activity.
    
    Provides methods for creating activity records, retrieving activity feeds
    with filtering and pagination, and managing activity data.
    """
    
    # Cache TTL in seconds (15 minutes)
    CACHE_TTL = 900
    
    @classmethod
    def record_activity(cls, user_id: uuid.UUID, activity_type: str, data: Optional[Dict] = None) -> 'Activity':
        """
        Record a new activity for a user.
        
        Args:
            user_id: UUID of the user
            activity_type: Type of activity (must be one of Activity.ACTIVITY_TYPES)
            data: Optional dictionary with additional activity data
            
        Returns:
            Created Activity instance
        
        **Validates: Requirements 1.3, 8.1, 8.2**
        """
        from dashboard.models import Activity
        
        # Validate activity type
        valid_types = [choice[0] for choice in Activity.ACTIVITY_TYPES]
        if activity_type not in valid_types:
            raise ValueError(f"Invalid activity type: {activity_type}. Must be one of {valid_types}")
        
        # Create activity record
        activity = Activity.objects.create(
            user_id=user_id,
            activity_type=activity_type,
            data=data or {}
        )
        
        # Invalidate activity feed cache for this user
        cache.delete(f"activity_feed:{user_id}")
        
        return activity
    
    @classmethod
    def get_activity_feed(cls, user_id: uuid.UUID, filters: Optional[Dict] = None, page: int = 1, page_size: int = 25):
        """
        Get activity feed for a user with optional filtering and pagination.
        
        Args:
            user_id: UUID of the user
            filters: Optional dictionary with keys:
                - activity_type: Filter by activity type
                - date_from: Filter activities after this date
                - date_to: Filter activities before this date
            page: Page number (1-indexed)
            page_size: Number of activities per page (default 25)
            
        Returns:
            Dictionary containing:
                - activities: QuerySet of Activity objects
                - total_count: Total number of activities matching filters
                - page: Current page number
                - page_size: Activities per page
                - total_pages: Total number of pages
        
        **Validates: Requirements 1.3, 8.1, 8.3, 8.5**
        """
        from dashboard.models import Activity
        from django.core.paginator import Paginator
        
        # Build base queryset
        queryset = Activity.objects.filter(user_id=user_id).select_related('user')
        
        # Apply filters
        if filters:
            # Filter by activity type
            if 'activity_type' in filters and filters['activity_type']:
                queryset = queryset.filter(activity_type=filters['activity_type'])
            
            # Filter by date range
            if 'date_from' in filters and filters['date_from']:
                queryset = queryset.filter(created_at__gte=filters['date_from'])
            
            if 'date_to' in filters and filters['date_to']:
                queryset = queryset.filter(created_at__lte=filters['date_to'])
        
        # Get total count before pagination
        total_count = queryset.count()
        
        # Apply pagination
        paginator = Paginator(queryset, page_size)
        
        # Ensure page is within valid range
        if page < 1:
            page = 1
        elif page > paginator.num_pages and paginator.num_pages > 0:
            page = paginator.num_pages
        
        # Get page
        page_obj = paginator.get_page(page)
        
        return {
            'activities': page_obj.object_list,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    @classmethod
    def get_activity_types(cls) -> List[tuple]:
        """
        Get list of available activity types.
        
        Returns:
            List of tuples (type_code, type_display_name)
        
        **Validates: Requirements 8.3**
        """
        from dashboard.models import Activity
        return Activity.ACTIVITY_TYPES
    
    @classmethod
    def delete_old_activities(cls, days: int = 90) -> int:
        """
        Delete activities older than specified number of days.
        
        This is a cleanup method to maintain database size and comply
        with data retention policies.
        
        Args:
            days: Number of days to keep (default 90)
            
        Returns:
            Number of activities deleted
        
        **Validates: Requirements 8.2 (data privacy)**
        """
        from dashboard.models import Activity
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete old activities
        deleted_count, _ = Activity.objects.filter(created_at__lt=cutoff_date).delete()
        
        return deleted_count



class AchievementService:
    """
    Service for managing user achievements.
    
    Provides methods for checking achievement criteria, awarding achievements,
    tracking progress, and managing achievement showcase.
    """
    
    @classmethod
    def check_achievements(cls, user_id: uuid.UUID, event_type: str) -> List['UserAchievement']:
        """
        Check and award achievements based on an event.
        
        This method checks if the user has met the criteria for any achievements
        based on the event type and awards them if criteria are met.
        
        Args:
            user_id: UUID of the user
            event_type: Type of event that triggered the check
                - 'tournament_completed': Check tournament-related achievements
                - 'team_joined': Check team-related achievements
                - 'profile_completed': Check profile completion achievement
                
        Returns:
            List of UserAchievement objects that were newly awarded or updated
        
        **Validates: Requirements 7.1**
        """
        from dashboard.models import Achievement, UserAchievement
        from tournaments.models import Participant
        from teams.models import TeamMember
        
        awarded_achievements = []
        
        # Get active achievements for this event type
        if event_type == 'tournament_completed':
            achievement_type = 'tournament'
        elif event_type == 'team_joined':
            achievement_type = 'social'
        elif event_type == 'profile_completed':
            achievement_type = 'platform'
        else:
            return awarded_achievements
        
        # Get all active achievements of this type
        achievements = Achievement.objects.filter(
            achievement_type=achievement_type,
            is_active=True
        )
        
        for achievement in achievements:
            # Check if user already has this achievement
            user_achievement, created = UserAchievement.objects.get_or_create(
                user_id=user_id,
                achievement=achievement,
                defaults={'current_value': 0}
            )
            
            # Skip if already completed
            if user_achievement.is_completed:
                continue
            
            # Check criteria based on achievement slug
            should_award = False
            current_value = 0
            
            if achievement.slug == 'first-tournament-win':
                # Check if user has won a tournament
                wins = Participant.objects.filter(
                    user_id=user_id,
                    final_placement=1,
                    status='confirmed'
                ).count()
                current_value = wins
                should_award = wins >= 1
            
            elif achievement.slug == 'ten-tournaments':
                # Check if user has participated in 10 tournaments
                participations = Participant.objects.filter(
                    user_id=user_id,
                    status='confirmed'
                ).count()
                current_value = participations
                should_award = participations >= 10
            
            elif achievement.slug == 'top-three-finish':
                # Check if user has finished in top 3
                top_3 = Participant.objects.filter(
                    user_id=user_id,
                    final_placement__lte=3,
                    final_placement__isnull=False,
                    status='confirmed'
                ).count()
                current_value = top_3
                should_award = top_3 >= 1
            
            elif achievement.slug == 'first-team':
                # Check if user has joined a team
                team_memberships = TeamMember.objects.filter(
                    user_id=user_id,
                    status='active'
                ).count()
                current_value = team_memberships
                should_award = team_memberships >= 1
            
            elif achievement.slug == 'profile-complete':
                # Check if profile is 100% complete
                from core.models import User
                user = User.objects.get(id=user_id)
                should_award = user.profile_completed
                current_value = 100 if should_award else 0
            
            # Update progress
            user_achievement.current_value = current_value
            
            # Award if criteria met
            if should_award and not user_achievement.is_completed:
                user_achievement.is_completed = True
                user_achievement.earned_at = timezone.now()
                user_achievement.save()
                
                # Award points to user
                from core.models import User
                user = User.objects.get(id=user_id)
                user.add_points(achievement.points_reward)
                
                # Record activity
                ActivityService.record_activity(
                    user_id=user_id,
                    activity_type='achievement_earned',
                    data={
                        'achievement_id': str(achievement.id),
                        'achievement_name': achievement.name,
                        'points_reward': achievement.points_reward
                    }
                )
                
                awarded_achievements.append(user_achievement)
            elif current_value != user_achievement.current_value:
                # Just update progress
                user_achievement.save()
                awarded_achievements.append(user_achievement)
        
        return awarded_achievements
    
    @classmethod
    def award_achievement(cls, user_id: uuid.UUID, achievement_id: uuid.UUID) -> 'UserAchievement':
        """
        Manually award an achievement to a user.
        
        This method is used for manually awarding achievements, typically
        by administrators or for special events.
        
        Args:
            user_id: UUID of the user
            achievement_id: UUID of the achievement to award
            
        Returns:
            UserAchievement object
        
        Raises:
            Achievement.DoesNotExist: If achievement doesn't exist
            ValueError: If achievement is already completed
        
        **Validates: Requirements 7.1**
        """
        from dashboard.models import Achievement, UserAchievement
        from core.models import User
        
        # Get achievement
        achievement = Achievement.objects.get(id=achievement_id)
        
        # Get or create user achievement
        user_achievement, created = UserAchievement.objects.get_or_create(
            user_id=user_id,
            achievement=achievement,
            defaults={
                'current_value': achievement.target_value,
                'is_completed': True,
                'earned_at': timezone.now()
            }
        )
        
        # If already exists and completed, raise error
        if not created and user_achievement.is_completed:
            raise ValueError(f"User has already earned achievement: {achievement.name}")
        
        # If not completed, complete it now
        if not user_achievement.is_completed:
            user_achievement.current_value = achievement.target_value
            user_achievement.is_completed = True
            user_achievement.earned_at = timezone.now()
            user_achievement.save()
            
            # Award points to user
            user = User.objects.get(id=user_id)
            user.add_points(achievement.points_reward)
            
            # Record activity
            ActivityService.record_activity(
                user_id=user_id,
                activity_type='achievement_earned',
                data={
                    'achievement_id': str(achievement.id),
                    'achievement_name': achievement.name,
                    'points_reward': achievement.points_reward
                }
            )
        
        return user_achievement
    
    @classmethod
    def get_user_achievements(cls, user_id: uuid.UUID):
        """
        Get all achievements for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            QuerySet of UserAchievement objects with related achievement data
        
        **Validates: Requirements 7.1**
        """
        from dashboard.models import UserAchievement
        
        return UserAchievement.objects.filter(
            user_id=user_id
        ).select_related('achievement').order_by('-earned_at', 'achievement__name')
    
    @classmethod
    def get_achievement_progress(cls, user_id: uuid.UUID, achievement_id: uuid.UUID) -> Dict:
        """
        Get progress information for a specific achievement.
        
        Args:
            user_id: UUID of the user
            achievement_id: UUID of the achievement
            
        Returns:
            Dictionary containing:
                - achievement: Achievement object
                - current_value: Current progress value
                - target_value: Target value to complete
                - progress_percentage: Progress as percentage (0-100)
                - is_completed: Whether achievement is completed
                - earned_at: When achievement was earned (if completed)
        
        **Validates: Requirements 7.2**
        """
        from dashboard.models import Achievement, UserAchievement
        
        achievement = Achievement.objects.get(id=achievement_id)
        
        try:
            user_achievement = UserAchievement.objects.get(
                user_id=user_id,
                achievement=achievement
            )
            current_value = user_achievement.current_value
            is_completed = user_achievement.is_completed
            earned_at = user_achievement.earned_at
        except UserAchievement.DoesNotExist:
            current_value = 0
            is_completed = False
            earned_at = None
        
        # Calculate progress percentage
        if achievement.is_progressive:
            progress_percentage = min(100, (current_value / achievement.target_value) * 100)
        else:
            progress_percentage = 100 if is_completed else 0
        
        return {
            'achievement': achievement,
            'current_value': current_value,
            'target_value': achievement.target_value,
            'progress_percentage': round(progress_percentage, 2),
            'is_completed': is_completed,
            'earned_at': earned_at,
        }
    
    @classmethod
    def update_showcase(cls, user_id: uuid.UUID, achievement_ids: List[uuid.UUID]) -> None:
        """
        Update the user's achievement showcase.
        
        The showcase displays up to 6 achievements prominently on the user's profile.
        
        Args:
            user_id: UUID of the user
            achievement_ids: List of achievement UUIDs to showcase (max 6)
            
        Raises:
            ValueError: If more than 6 achievements provided or if user hasn't earned an achievement
        
        **Validates: Requirements 7.5**
        """
        from dashboard.models import UserAchievement
        
        # Validate max 6 achievements
        if len(achievement_ids) > 6:
            raise ValueError("Cannot showcase more than 6 achievements")
        
        # Clear current showcase
        UserAchievement.objects.filter(
            user_id=user_id,
            in_showcase=True
        ).update(in_showcase=False, showcase_order=0)
        
        # Set new showcase
        for order, achievement_id in enumerate(achievement_ids, start=1):
            try:
                user_achievement = UserAchievement.objects.get(
                    user_id=user_id,
                    achievement_id=achievement_id,
                    is_completed=True
                )
                user_achievement.in_showcase = True
                user_achievement.showcase_order = order
                user_achievement.save(update_fields=['in_showcase', 'showcase_order'])
            except UserAchievement.DoesNotExist:
                raise ValueError(f"User has not earned achievement: {achievement_id}")
    
    @classmethod
    def get_rare_achievements(cls, user_id: uuid.UUID):
        """
        Get rare achievements earned by the user.
        
        Rare achievements are those earned by fewer than 10% of users.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            QuerySet of UserAchievement objects for rare achievements
        
        **Validates: Requirements 7.4**
        """
        from dashboard.models import UserAchievement, Achievement
        from core.models import User
        from django.db.models import Count, F
        
        # Get total user count
        total_users = User.objects.filter(is_active=True).count()
        
        if total_users == 0:
            return UserAchievement.objects.none()
        
        # Get achievements where the percentage of users who earned it is < 10%
        # We need to use raw SQL or a more complex query to calculate percentages
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT a.id
                FROM achievements a
                LEFT JOIN (
                    SELECT achievement_id, COUNT(*) as earned_count
                    FROM user_achievements 
                    WHERE is_completed = true
                    GROUP BY achievement_id
                ) ua ON a.id = ua.achievement_id
                WHERE COALESCE(ua.earned_count, 0) > 0 
                AND (COALESCE(ua.earned_count, 0) * 100.0 / %s) < 10.0
            """, [total_users])
            
            rare_achievement_ids = [row[0] for row in cursor.fetchall()]
        
        # Get user's rare achievements
        return UserAchievement.objects.filter(
            user_id=user_id,
            achievement_id__in=rare_achievement_ids,
            is_completed=True
        ).select_related('achievement')



class RecommendationService:
    """
    Service for generating and managing personalized recommendations.
    
    Provides methods for recommending tournaments and teams based on user
    preferences, game profiles, and skill level.
    """
    
    # Cache TTL in seconds (24 hours)
    CACHE_TTL = 86400
    
    # Dismissal cooldown in days
    DISMISSAL_COOLDOWN_DAYS = 30
    
    @classmethod
    def get_tournament_recommendations(cls, user_id: uuid.UUID, limit: int = 3):
        """
        Get tournament recommendations for a user.
        
        Matches tournaments based on:
        - User's game profiles
        - Skill level (±1 level)
        - Past participation patterns
        - Excludes dismissed recommendations
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of recommendations to return (default 3)
            
        Returns:
            QuerySet of Recommendation objects for tournaments
        
        **Validates: Requirements 13.1, 13.2, 13.3**
        """
        from dashboard.models import Recommendation
        from tournaments.models import Tournament
        from core.models import UserGameProfile
        from django.contrib.contenttypes.models import ContentType
        
        # Get user's game profiles
        game_profiles = UserGameProfile.objects.filter(user_id=user_id)
        
        if not game_profiles.exists():
            return Recommendation.objects.none()
        
        # Get games user plays
        user_game_ids = list(game_profiles.values_list('game_id', flat=True))
        
        # Get user's skill ratings by game
        skill_ratings = {
            profile.game_id: profile.skill_rating or 0
            for profile in game_profiles
        }
        
        # Get active tournaments for user's games
        now = timezone.now()
        tournaments = Tournament.objects.filter(
            game_id__in=user_game_ids,
            status__in=['registration', 'draft'],
            registration_end__gt=now,
            start_datetime__gt=now
        ).select_related('game')
        
        # Get existing recommendations (including dismissed ones for filtering)
        existing_recs = Recommendation.objects.filter(
            user_id=user_id,
            recommendation_type='tournament'
        )
        
        # Get dismissed tournament IDs within cooldown period
        cooldown_date = now - timedelta(days=cls.DISMISSAL_COOLDOWN_DAYS)
        dismissed_tournament_ids = set(
            existing_recs.filter(
                is_dismissed=True,
                dismissed_at__gte=cooldown_date
            ).values_list('object_id', flat=True)
        )
        
        # Get already recommended tournament IDs (not expired)
        already_recommended_ids = set(
            existing_recs.filter(
                is_dismissed=False,
                expires_at__gt=now
            ).values_list('object_id', flat=True)
        )
        
        # Filter out dismissed and already recommended tournaments
        tournaments = tournaments.exclude(id__in=dismissed_tournament_ids)
        tournaments = tournaments.exclude(id__in=already_recommended_ids)
        
        # Score and rank tournaments
        scored_tournaments = []
        for tournament in tournaments:
            from core.models import User
            user = User.objects.get(id=user_id)
            score = cls.calculate_recommendation_score(user, tournament)
            if score > 0:
                scored_tournaments.append((tournament, score))
        
        # Sort by score descending
        scored_tournaments.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N
        top_tournaments = scored_tournaments[:limit]
        
        # Create or update recommendations
        tournament_content_type = ContentType.objects.get_for_model(Tournament)
        recommendations = []
        
        for tournament, score in top_tournaments:
            # Generate reason
            reason = cls._generate_tournament_reason(user_id, tournament, skill_ratings)
            
            # Create or update recommendation
            rec, created = Recommendation.objects.update_or_create(
                user_id=user_id,
                recommendation_type='tournament',
                content_type=tournament_content_type,
                object_id=tournament.id,
                defaults={
                    'score': score,
                    'reason': reason,
                    'expires_at': now + timedelta(hours=24),
                    'is_dismissed': False,
                    'dismissed_at': None,
                }
            )
            recommendations.append(rec)
        
        return Recommendation.objects.filter(
            id__in=[r.id for r in recommendations]
        ).select_related('user')
    
    @classmethod
    def get_team_recommendations(cls, user_id: uuid.UUID, limit: int = 3):
        """
        Get team recommendations for a user.
        
        Matches teams based on:
        - User's game profiles
        - Teams actively recruiting
        - Skill level compatibility
        - Excludes dismissed recommendations
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of recommendations to return (default 3)
            
        Returns:
            QuerySet of Recommendation objects for teams
        
        **Validates: Requirements 13.1, 13.2, 13.3**
        """
        from dashboard.models import Recommendation
        from teams.models import Team
        from core.models import UserGameProfile
        from django.contrib.contenttypes.models import ContentType
        
        # Get user's game profiles
        game_profiles = UserGameProfile.objects.filter(user_id=user_id)
        
        if not game_profiles.exists():
            return Recommendation.objects.none()
        
        # Get games user plays
        user_game_ids = list(game_profiles.values_list('game_id', flat=True))
        
        # Get recruiting teams for user's games
        now = timezone.now()
        teams = Team.objects.filter(
            game_id__in=user_game_ids,
            is_recruiting=True,
            status='active'
        ).select_related('game')
        
        # Get existing recommendations (including dismissed ones for filtering)
        existing_recs = Recommendation.objects.filter(
            user_id=user_id,
            recommendation_type='team'
        )
        
        # Get dismissed team IDs within cooldown period
        cooldown_date = now - timedelta(days=cls.DISMISSAL_COOLDOWN_DAYS)
        dismissed_team_ids = set(
            existing_recs.filter(
                is_dismissed=True,
                dismissed_at__gte=cooldown_date
            ).values_list('object_id', flat=True)
        )
        
        # Get already recommended team IDs (not expired)
        already_recommended_ids = set(
            existing_recs.filter(
                is_dismissed=False,
                expires_at__gt=now
            ).values_list('object_id', flat=True)
        )
        
        # Filter out dismissed and already recommended teams
        teams = teams.exclude(id__in=dismissed_team_ids)
        teams = teams.exclude(id__in=already_recommended_ids)
        
        # Score and rank teams
        scored_teams = []
        for team in teams:
            from core.models import User
            user = User.objects.get(id=user_id)
            score = cls.calculate_recommendation_score(user, team)
            if score > 0:
                scored_teams.append((team, score))
        
        # Sort by score descending
        scored_teams.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N
        top_teams = scored_teams[:limit]
        
        # Create or update recommendations
        team_content_type = ContentType.objects.get_for_model(Team)
        recommendations = []
        
        for team, score in top_teams:
            # Generate reason
            reason = cls._generate_team_reason(user_id, team)
            
            # Create or update recommendation
            rec, created = Recommendation.objects.update_or_create(
                user_id=user_id,
                recommendation_type='team',
                content_type=team_content_type,
                object_id=team.id,
                defaults={
                    'score': score,
                    'reason': reason,
                    'expires_at': now + timedelta(hours=24),
                    'is_dismissed': False,
                    'dismissed_at': None,
                }
            )
            recommendations.append(rec)
        
        return Recommendation.objects.filter(
            id__in=[r.id for r in recommendations]
        ).select_related('user')
    
    @classmethod
    def calculate_recommendation_score(cls, user, item) -> float:
        """
        Calculate relevance score for a recommendation.
        
        Scoring algorithm considers:
        - Game match (50 points)
        - Skill level match (30 points)
        - Past participation patterns (20 points)
        
        Args:
            user: User object
            item: Tournament or Team object
            
        Returns:
            Float score between 0 and 100
        
        **Validates: Requirements 13.3**
        """
        from tournaments.models import Tournament, Participant
        from teams.models import Team
        from core.models import UserGameProfile
        
        score = 0.0
        
        # Determine item type
        if isinstance(item, Tournament):
            # Game match (50 points)
            user_profile = UserGameProfile.objects.filter(
                user=user,
                game=item.game
            ).first()
            
            if user_profile:
                score += 50.0
                
                # Skill level match (30 points)
                # Check if tournament has skill requirements
                if hasattr(item, 'min_skill_rating') and hasattr(item, 'max_skill_rating'):
                    if item.min_skill_rating and item.max_skill_rating:
                        user_skill = user_profile.skill_rating or 0
                        if item.min_skill_rating <= user_skill <= item.max_skill_rating:
                            score += 30.0
                        else:
                            # Partial points for being close
                            distance = min(
                                abs(user_skill - item.min_skill_rating),
                                abs(user_skill - item.max_skill_rating)
                            )
                            if distance <= 500:  # Within 500 rating points
                                score += 15.0
                else:
                    # No skill requirements, give full points
                    score += 30.0
                
                # Past participation patterns (20 points)
                # Check if user has participated in similar tournaments
                past_participations = Participant.objects.filter(
                    user=user,
                    tournament__game=item.game,
                    status='confirmed'
                ).count()
                
                if past_participations > 0:
                    # More participations = higher score (capped at 20)
                    score += min(20.0, past_participations * 5.0)
        
        elif isinstance(item, Team):
            # Game match (50 points)
            user_profile = UserGameProfile.objects.filter(
                user=user,
                game=item.game
            ).first()
            
            if user_profile:
                score += 50.0
                
                # Skill level match (30 points)
                # Check if team has skill requirements
                if hasattr(item, 'min_skill_rating') and hasattr(item, 'max_skill_rating'):
                    if item.min_skill_rating and item.max_skill_rating:
                        user_skill = user_profile.skill_rating or 0
                        if item.min_skill_rating <= user_skill <= item.max_skill_rating:
                            score += 30.0
                        else:
                            # Partial points for being close
                            distance = min(
                                abs(user_skill - item.min_skill_rating),
                                abs(user_skill - item.max_skill_rating)
                            )
                            if distance <= 500:  # Within 500 rating points
                                score += 15.0
                else:
                    # No skill requirements, give full points
                    score += 30.0
                
                # Team activity (20 points)
                # Check team's recent activity
                if hasattr(item, 'member_count'):
                    # More active teams get higher scores
                    if item.member_count >= 5:
                        score += 20.0
                    elif item.member_count >= 3:
                        score += 15.0
                    elif item.member_count >= 1:
                        score += 10.0
                else:
                    score += 10.0  # Default partial points
        
        return round(score, 2)
    
    @classmethod
    def dismiss_recommendation(cls, user_id: uuid.UUID, rec_id: uuid.UUID) -> None:
        """
        Mark a recommendation as dismissed.
        
        Dismissed recommendations will not reappear for 30 days.
        
        Args:
            user_id: UUID of the user
            rec_id: UUID of the recommendation to dismiss
            
        Raises:
            Recommendation.DoesNotExist: If recommendation doesn't exist
            ValueError: If recommendation doesn't belong to user
        
        **Validates: Requirements 13.4**
        """
        from dashboard.models import Recommendation
        
        # Get recommendation
        recommendation = Recommendation.objects.get(id=rec_id)
        
        # Verify ownership
        if recommendation.user_id != user_id:
            raise ValueError("Recommendation does not belong to this user")
        
        # Mark as dismissed
        recommendation.is_dismissed = True
        recommendation.dismissed_at = timezone.now()
        recommendation.save(update_fields=['is_dismissed', 'dismissed_at'])
    
    @classmethod
    def refresh_recommendations(cls, user_id: uuid.UUID) -> Dict:
        """
        Regenerate recommendations for a user.
        
        This method clears expired recommendations and generates fresh ones.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dictionary containing:
                - tournament_recommendations: QuerySet of tournament recommendations
                - team_recommendations: QuerySet of team recommendations
                - total_count: Total number of recommendations generated
        
        **Validates: Requirements 13.5**
        """
        from dashboard.models import Recommendation
        
        # Delete expired recommendations
        now = timezone.now()
        Recommendation.objects.filter(
            user_id=user_id,
            expires_at__lt=now
        ).delete()
        
        # Generate new recommendations
        tournament_recs = cls.get_tournament_recommendations(user_id, limit=3)
        team_recs = cls.get_team_recommendations(user_id, limit=3)
        
        return {
            'tournament_recommendations': tournament_recs,
            'team_recommendations': team_recs,
            'total_count': tournament_recs.count() + team_recs.count(),
        }
    
    @classmethod
    def _generate_tournament_reason(cls, user_id: uuid.UUID, tournament, skill_ratings: Dict) -> str:
        """
        Generate a human-readable reason for tournament recommendation.
        
        Args:
            user_id: UUID of the user
            tournament: Tournament object
            skill_ratings: Dictionary mapping game_id to skill_rating
            
        Returns:
            String explaining why tournament is recommended
        """
        reasons = []
        
        # Game match
        if tournament.game_id in skill_ratings:
            reasons.append(f"Matches your {tournament.game.name} profile")
        
        # Skill level
        user_skill = skill_ratings.get(tournament.game_id, 0)
        if hasattr(tournament, 'min_skill_rating') and hasattr(tournament, 'max_skill_rating'):
            if tournament.min_skill_rating and tournament.max_skill_rating:
                if tournament.min_skill_rating <= user_skill <= tournament.max_skill_rating:
                    reasons.append("Skill level match")
        
        # Default reason if no specific reasons
        if not reasons:
            reasons.append("Based on your gaming preferences")
        
        return " • ".join(reasons[:2])  # Max 2 reasons to fit in 200 chars
    
    @classmethod
    def _generate_team_reason(cls, user_id: uuid.UUID, team) -> str:
        """
        Generate a human-readable reason for team recommendation.
        
        Args:
            user_id: UUID of the user
            team: Team object
            
        Returns:
            String explaining why team is recommended
        """
        reasons = []
        
        # Game match
        reasons.append(f"Plays {team.game.name}")
        
        # Recruiting status
        if team.is_recruiting:
            reasons.append("Actively recruiting")
        
        return " • ".join(reasons[:2])  # Max 2 reasons to fit in 200 chars



class PrivacyService:
    """
    Service for managing user privacy settings and enforcing privacy controls.
    
    Provides methods for checking permissions, filtering profile data based on
    privacy settings, and managing privacy preferences.
    """
    
    @classmethod
    def can_view_profile(cls, viewer, profile_owner) -> bool:
        """
        Check if viewer can view profile owner's profile.
        
        Public profiles are viewable by all authenticated users.
        Private profiles are only viewable by the owner and friends.
        
        Args:
            viewer: User object of the viewer (can be None for anonymous)
            profile_owner: User object of the profile being viewed
            
        Returns:
            Boolean indicating if viewer can view the profile
        
        **Validates: Requirements 2.5, 10.1, 10.2**
        """
        # Owner can always view their own profile
        if viewer and viewer.id == profile_owner.id:
            return True
        
        # Check if profile is public (no privacy restrictions)
        # If all privacy fields are True, profile is considered public
        if (profile_owner.online_status_visible and 
            profile_owner.activity_visible and 
            profile_owner.statistics_visible):
            return True
        
        # For private profiles, check if viewer is a friend
        if viewer:
            return cls.are_friends(viewer, profile_owner)
        
        # Anonymous users can only view public profiles
        return False
    
    @classmethod
    def can_view_statistics(cls, viewer, profile_owner) -> bool:
        """
        Check if viewer can view profile owner's statistics.
        
        Statistics visibility is controlled by the statistics_visible field.
        Owner and friends can always view statistics.
        
        Args:
            viewer: User object of the viewer (can be None for anonymous)
            profile_owner: User object of the profile being viewed
            
        Returns:
            Boolean indicating if viewer can view statistics
        
        **Validates: Requirements 2.5, 10.2, 10.5**
        """
        # Owner can always view their own statistics
        if viewer and viewer.id == profile_owner.id:
            return True
        
        # Check statistics_visible setting
        if profile_owner.statistics_visible:
            return True
        
        # Friends can view statistics even if not public
        if viewer:
            return cls.are_friends(viewer, profile_owner)
        
        return False
    
    @classmethod
    def can_view_activity(cls, viewer, profile_owner) -> bool:
        """
        Check if viewer can view profile owner's activity feed.
        
        Activity visibility is controlled by the activity_visible field.
        Owner and friends can always view activity.
        
        Args:
            viewer: User object of the viewer (can be None for anonymous)
            profile_owner: User object of the profile being viewed
            
        Returns:
            Boolean indicating if viewer can view activity
        
        **Validates: Requirements 2.5, 10.2, 10.5**
        """
        # Owner can always view their own activity
        if viewer and viewer.id == profile_owner.id:
            return True
        
        # Check activity_visible setting
        if profile_owner.activity_visible:
            return True
        
        # Friends can view activity even if not public
        if viewer:
            return cls.are_friends(viewer, profile_owner)
        
        return False
    
    @classmethod
    def filter_profile_data(cls, viewer, profile_data: Dict) -> Dict:
        """
        Filter profile data based on viewer's permissions.
        
        Removes sensitive information that the viewer is not allowed to see
        based on privacy settings.
        
        Args:
            viewer: User object of the viewer (can be None for anonymous)
            profile_data: Dictionary containing profile information
            
        Returns:
            Filtered dictionary with only allowed information
        
        **Validates: Requirements 10.2, 10.5**
        """
        from core.models import User
        
        # Get profile owner from data
        if 'user' in profile_data:
            profile_owner = profile_data['user']
        elif 'user_id' in profile_data:
            profile_owner = User.objects.get(id=profile_data['user_id'])
        else:
            # Can't determine owner, return minimal data
            return {
                'error': 'Unable to determine profile owner'
            }
        
        # Create filtered data with basic information (always visible)
        filtered_data = {
            'user': profile_owner,
            'username': profile_owner.username,
            'display_name': profile_owner.display_name or profile_owner.username,
            'avatar': profile_owner.avatar.url if profile_owner.avatar else None,
            'bio': profile_owner.bio or '',
        }
        
        # Add statistics if viewer has permission
        if cls.can_view_statistics(viewer, profile_owner):
            if 'statistics' in profile_data:
                filtered_data['statistics'] = profile_data['statistics']
            if 'game_profiles' in profile_data:
                filtered_data['game_profiles'] = profile_data['game_profiles']
            if 'tournament_history' in profile_data:
                filtered_data['tournament_history'] = profile_data['tournament_history']
            if 'win_rate' in profile_data:
                filtered_data['win_rate'] = profile_data['win_rate']
            if 'total_tournaments' in profile_data:
                filtered_data['total_tournaments'] = profile_data['total_tournaments']
        
        # Add activity if viewer has permission
        if cls.can_view_activity(viewer, profile_owner):
            if 'activity_feed' in profile_data:
                filtered_data['activity_feed'] = profile_data['activity_feed']
            if 'recent_activity' in profile_data:
                filtered_data['recent_activity'] = profile_data['recent_activity']
        
        # Add online status if visible
        if profile_owner.online_status_visible or (viewer and viewer.id == profile_owner.id):
            if 'is_online' in profile_data:
                filtered_data['is_online'] = profile_data['is_online']
            if 'last_seen' in profile_data:
                filtered_data['last_seen'] = profile_data['last_seen']
        
        # Always include achievements showcase (public by design)
        if 'achievements' in profile_data:
            filtered_data['achievements'] = profile_data['achievements']
        
        # Always include team memberships (public by design)
        if 'teams' in profile_data:
            filtered_data['teams'] = profile_data['teams']
        
        # Add banner if present
        if profile_owner.banner:
            filtered_data['banner'] = profile_owner.banner.url
        
        return filtered_data
    
    @classmethod
    def get_privacy_settings(cls, user_id: uuid.UUID) -> Dict:
        """
        Get privacy settings for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dictionary containing privacy settings:
                - online_status_visible: Boolean
                - activity_visible: Boolean
                - statistics_visible: Boolean
        
        **Validates: Requirements 9.2**
        """
        from core.models import User
        
        user = User.objects.get(id=user_id)
        
        return {
            'online_status_visible': user.online_status_visible,
            'activity_visible': user.activity_visible,
            'statistics_visible': user.statistics_visible,
        }
    
    @classmethod
    def update_privacy_settings(cls, user_id: uuid.UUID, settings: Dict) -> None:
        """
        Update privacy settings for a user.
        
        Args:
            user_id: UUID of the user
            settings: Dictionary with privacy settings to update:
                - online_status_visible: Boolean (optional)
                - activity_visible: Boolean (optional)
                - statistics_visible: Boolean (optional)
                
        Raises:
            User.DoesNotExist: If user doesn't exist
            ValueError: If invalid settings provided
        
        **Validates: Requirements 9.2**
        """
        from core.models import User
        
        user = User.objects.get(id=user_id)
        
        # Validate and update settings
        update_fields = []
        
        if 'online_status_visible' in settings:
            if not isinstance(settings['online_status_visible'], bool):
                raise ValueError("online_status_visible must be a boolean")
            user.online_status_visible = settings['online_status_visible']
            update_fields.append('online_status_visible')
        
        if 'activity_visible' in settings:
            if not isinstance(settings['activity_visible'], bool):
                raise ValueError("activity_visible must be a boolean")
            user.activity_visible = settings['activity_visible']
            update_fields.append('activity_visible')
        
        if 'statistics_visible' in settings:
            if not isinstance(settings['statistics_visible'], bool):
                raise ValueError("statistics_visible must be a boolean")
            user.statistics_visible = settings['statistics_visible']
            update_fields.append('statistics_visible')
        
        # Save changes
        if update_fields:
            user.save(update_fields=update_fields)
            
            # Record activity
            ActivityService.record_activity(
                user_id=user_id,
                activity_type='profile_updated',
                data={
                    'updated_fields': update_fields,
                    'privacy_settings_changed': True
                }
            )
    
    @classmethod
    def are_friends(cls, user1, user2) -> bool:
        """
        Check if two users are friends.
        
        This is a placeholder method for Phase 2 friend system implementation.
        Currently returns False as the friend system is not yet implemented.
        
        Args:
            user1: First User object
            user2: Second User object
            
        Returns:
            Boolean indicating if users are friends (always False in Phase 1)
        
        **Validates: Requirements 10.5**
        """
        # Placeholder for Phase 2 friend system
        # When friend system is implemented, this should check the friendship table
        return False


class PaymentSummaryService:
    """
    Service for aggregating payment data for dashboard display.
    
    Provides methods for retrieving payment summaries, recent payments,
    and payment method information. This service acts as a facade to the
    payments module, providing dashboard-specific aggregations.
    """
    
    @classmethod
    def get_payment_summary(cls, user_id: uuid.UUID) -> Dict:
        """
        Get payment summary for a user.
        
        Aggregates payment data including total spent, recent payments count,
        and saved payment methods count.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dictionary containing:
                - total_spent: Total amount spent (Decimal)
                - recent_payments_count: Count of payments in last 30 days
                - saved_payment_methods_count: Count of active payment methods
                - has_default_method: Boolean indicating if user has default payment method
                - recent_payments: QuerySet of last 5 payments
        
        **Validates: Requirements 12.1, 12.2, 12.3**
        """
        from payments.models import Payment, PaymentMethod
        
        # Calculate total spent (only succeeded payments)
        total_spent_aggregate = Payment.objects.filter(
            user_id=user_id,
            status='succeeded'
        ).aggregate(
            total=Sum('amount')
        )
        total_spent = total_spent_aggregate['total'] or Decimal('0.00')
        
        # Count recent payments (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_payments_count = Payment.objects.filter(
            user_id=user_id,
            created_at__gte=thirty_days_ago
        ).count()
        
        # Count saved payment methods
        saved_payment_methods_count = PaymentMethod.objects.filter(
            user_id=user_id,
            is_active=True
        ).count()
        
        # Check if user has default payment method
        has_default_method = cls.has_default_payment_method(user_id)
        
        # Get recent payments (last 5)
        recent_payments = cls.get_recent_payments(user_id, limit=5)
        
        return {
            'total_spent': total_spent,
            'recent_payments_count': recent_payments_count,
            'saved_payment_methods_count': saved_payment_methods_count,
            'has_default_method': has_default_method,
            'recent_payments': recent_payments,
        }
    
    @classmethod
    def get_recent_payments(cls, user_id: uuid.UUID, limit: int = 5):
        """
        Get recent payments for a user.
        
        Returns the most recent N payments ordered by creation date.
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of payments to return (default 5)
            
        Returns:
            QuerySet of Payment objects ordered by created_at descending
        
        **Validates: Requirements 12.1, 12.2**
        """
        from payments.models import Payment
        
        return Payment.objects.filter(
            user_id=user_id
        ).select_related('user').order_by('-created_at')[:limit]
    
    @classmethod
    def get_saved_payment_methods_count(cls, user_id: uuid.UUID) -> int:
        """
        Get count of saved payment methods for a user.
        
        Only counts active payment methods.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Integer count of active payment methods
        
        **Validates: Requirements 12.2**
        """
        from payments.models import PaymentMethod
        
        return PaymentMethod.objects.filter(
            user_id=user_id,
            is_active=True
        ).count()
    
    @classmethod
    def has_default_payment_method(cls, user_id: uuid.UUID) -> bool:
        """
        Check if user has a default payment method.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Boolean indicating if user has a default payment method
        
        **Validates: Requirements 12.3**
        """
        from payments.models import PaymentMethod
        
        return PaymentMethod.objects.filter(
            user_id=user_id,
            is_default=True,
            is_active=True
        ).exists()



class ProfileExportService:
    """
    Service for exporting user profile data.
    
    Provides methods for generating comprehensive JSON exports of user data
    for data portability and GDPR compliance. Excludes sensitive information
    like password hashes and payment method details.
    """
    
    @classmethod
    def generate_export(cls, user_id: uuid.UUID) -> Dict:
        """
        Generate a comprehensive export of user data.
        
        Includes:
        - Profile information (name, email, bio, etc.)
        - Game profiles with statistics
        - Tournament history and participations
        - Team memberships (current and past)
        - Payment history (amounts and dates, but not payment method details)
        - Activity history
        - Achievements earned
        
        Excludes:
        - Password hash
        - Payment method details (card numbers, etc.)
        - Internal system IDs (converted to readable format)
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dictionary containing all exportable user data in JSON-serializable format
        
        **Validates: Requirements 17.1, 17.2, 17.5**
        """
        from core.models import User, UserGameProfile
        from tournaments.models import Participant
        from teams.models import TeamMember
        from payments.models import Payment
        from dashboard.models import Activity, UserAchievement
        from security.models import AuditLog
        
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError(f"User with ID {user_id} does not exist")
        
        # Build export data structure
        export_data = {
            'export_metadata': {
                'generated_at': timezone.now().isoformat(),
                'user_id': str(user.id),
                'username': user.username,
                'export_version': '1.0',
            },
            'profile': cls._export_profile_info(user),
            'game_profiles': cls._export_game_profiles(user),
            'tournament_history': cls._export_tournament_history(user),
            'team_memberships': cls._export_team_memberships(user),
            'payment_history': cls._export_payment_history(user),
            'activity_history': cls._export_activity_history(user),
            'achievements': cls._export_achievements(user),
        }
        
        # Log the export request
        AuditLog.log_action(
            user=user,
            action='export',
            model_name='User',
            object_id=str(user.id),
            description='User data export generated',
            severity='medium',
            details={
                'export_sections': list(export_data.keys()),
                'total_size_estimate': len(str(export_data))
            }
        )
        
        return export_data
    
    @classmethod
    def _export_profile_info(cls, user) -> Dict:
        """
        Export basic profile information.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with profile information
        """
        return {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'display_name': user.display_name,
            'bio': user.bio,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'country': user.country,
            'city': user.city,
            'timezone': user.timezone,
            'phone_number': user.phone_number,
            'role': user.role,
            'skill_level': user.skill_level,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            'is_verified': user.is_verified,
            'total_points': user.total_points,
            'level': user.level,
            'connected_accounts': {
                'discord': user.discord_username,
                'steam': user.steam_id,
                'twitch': user.twitch_username,
            },
            'privacy_settings': {
                'online_status_visible': user.online_status_visible,
                'activity_visible': user.activity_visible,
                'statistics_visible': user.statistics_visible,
            },
            'notification_preferences': {
                'email_notifications': user.email_notifications,
            },
            'avatar_url': user.avatar.url if user.avatar else None,
            'banner_url': user.banner.url if user.banner else None,
        }
    
    @classmethod
    def _export_game_profiles(cls, user) -> List[Dict]:
        """
        Export user's game profiles.
        
        Args:
            user: User object
            
        Returns:
            List of dictionaries with game profile information
        """
        from core.models import UserGameProfile
        
        game_profiles = UserGameProfile.objects.filter(
            user=user
        ).select_related('game')
        
        profiles_data = []
        for profile in game_profiles:
            profiles_data.append({
                'game_name': profile.game.name if profile.game else 'Unknown',
                'in_game_name': profile.in_game_name,
                'skill_rating': profile.skill_rating,
                'rank': profile.rank,
                'is_main_game': profile.is_main_game,
                'matches_played': profile.matches_played,
                'matches_won': profile.matches_won,
                'matches_lost': profile.matches_lost,
                'win_rate': profile.win_rate,
                'created_at': profile.created_at.isoformat() if profile.created_at else None,
                'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
            })
        
        return profiles_data
    
    @classmethod
    def _export_tournament_history(cls, user) -> List[Dict]:
        """
        Export user's tournament participation history.
        
        Args:
            user: User object
            
        Returns:
            List of dictionaries with tournament participation information
        """
        from tournaments.models import Participant
        
        participations = Participant.objects.filter(
            user=user
        ).select_related('tournament', 'tournament__game').order_by('-tournament__start_datetime')
        
        history_data = []
        for participation in participations:
            tournament = participation.tournament
            history_data.append({
                'tournament_name': tournament.name,
                'game_name': tournament.game.name if tournament.game else 'Unknown',
                'tournament_type': tournament.tournament_type,
                'format': tournament.format,
                'start_date': tournament.start_datetime.isoformat() if tournament.start_datetime else None,
                'end_date': tournament.end_datetime.isoformat() if tournament.end_datetime else None,
                'status': participation.status,
                'final_placement': participation.final_placement,
                'matches_played': participation.matches_played,
                'matches_won': participation.matches_won,
                'matches_lost': participation.matches_lost,
                'prize_won': str(participation.prize_won) if participation.prize_won else '0.00',
                'registered_at': participation.registered_at.isoformat() if participation.registered_at else None,
            })
        
        return history_data
    
    @classmethod
    def _export_team_memberships(cls, user) -> Dict:
        """
        Export user's team memberships (current and past).
        
        Args:
            user: User object
            
        Returns:
            Dictionary with current and past team memberships
        """
        from teams.models import TeamMember
        
        # Current memberships
        current_memberships = TeamMember.objects.filter(
            user=user,
            status='active'
        ).select_related('team', 'team__game')
        
        current_data = []
        for membership in current_memberships:
            team = membership.team
            current_data.append({
                'team_name': team.name,
                'game_name': team.game.name if team.game else 'Unknown',
                'role': membership.role,
                'joined_at': membership.joined_at.isoformat() if membership.joined_at else None,
                'is_captain': membership.role == 'captain',
            })
        
        # Past memberships
        past_memberships = TeamMember.objects.filter(
            user=user,
            status='left'
        ).select_related('team', 'team__game')
        
        past_data = []
        for membership in past_memberships:
            team = membership.team
            past_data.append({
                'team_name': team.name,
                'game_name': team.game.name if team.game else 'Unknown',
                'role': membership.role,
                'joined_at': membership.joined_at.isoformat() if membership.joined_at else None,
                'left_at': membership.left_at.isoformat() if membership.left_at else None,
                'duration_days': (membership.left_at - membership.joined_at).days if (membership.left_at and membership.joined_at) else None,
            })
        
        return {
            'current_teams': current_data,
            'past_teams': past_data,
            'total_teams_joined': len(current_data) + len(past_data),
        }
    
    @classmethod
    def _export_payment_history(cls, user) -> Dict:
        """
        Export user's payment history.
        
        Includes payment amounts, dates, and descriptions, but excludes
        sensitive payment method details like card numbers.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with payment history and summary
        """
        from payments.models import Payment
        
        payments = Payment.objects.filter(
            user=user
        ).order_by('-created_at')
        
        payments_data = []
        total_spent = Decimal('0.00')
        
        for payment in payments:
            payment_info = {
                'amount': str(payment.amount),
                'currency': payment.currency,
                'status': payment.status,
                'description': payment.description,
                'payment_type': payment.payment_type,
                'created_at': payment.created_at.isoformat() if payment.created_at else None,
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
            }
            payments_data.append(payment_info)
            
            # Sum up successful payments
            if payment.status == 'succeeded':
                total_spent += payment.amount
        
        return {
            'payments': payments_data,
            'summary': {
                'total_payments': len(payments_data),
                'total_spent': str(total_spent),
                'successful_payments': sum(1 for p in payments if p.status == 'succeeded'),
                'failed_payments': sum(1 for p in payments if p.status == 'failed'),
            }
        }
    
    @classmethod
    def _export_activity_history(cls, user) -> List[Dict]:
        """
        Export user's activity history.
        
        Args:
            user: User object
            
        Returns:
            List of dictionaries with activity information
        """
        from dashboard.models import Activity
        
        activities = Activity.objects.filter(
            user=user
        ).order_by('-created_at')[:500]  # Limit to last 500 activities
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'activity_type': activity.activity_type,
                'data': activity.data,
                'created_at': activity.created_at.isoformat() if activity.created_at else None,
            })
        
        return activities_data
    
    @classmethod
    def _export_achievements(cls, user) -> Dict:
        """
        Export user's earned achievements.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with achievements information
        """
        from dashboard.models import UserAchievement
        
        user_achievements = UserAchievement.objects.filter(
            user=user,
            is_completed=True
        ).select_related('achievement').order_by('-earned_at')
        
        achievements_data = []
        total_points_earned = 0
        
        for user_achievement in user_achievements:
            achievement = user_achievement.achievement
            achievement_info = {
                'name': achievement.name,
                'description': achievement.description,
                'type': achievement.achievement_type,
                'rarity': achievement.rarity,
                'points_reward': achievement.points_reward,
                'earned_at': user_achievement.earned_at.isoformat() if user_achievement.earned_at else None,
                'in_showcase': user_achievement.in_showcase,
            }
            achievements_data.append(achievement_info)
            total_points_earned += achievement.points_reward
        
        return {
            'achievements': achievements_data,
            'summary': {
                'total_achievements_earned': len(achievements_data),
                'total_points_from_achievements': total_points_earned,
                'achievements_in_showcase': sum(1 for a in user_achievements if a.in_showcase),
            }
        }


class SocialService:
    """
    Service for social interactions and relationships between users.
    
    Provides methods for finding mutual teams, managing social connections,
    and handling user interactions.
    """
    
    @classmethod
    def get_mutual_teams(cls, user1_id: uuid.UUID, user2_id: uuid.UUID) -> List[Dict]:
        """
        Get teams that both users are members of.
        
        Returns the set intersection of teams where both users have active memberships.
        This is used to display mutual teams on profile pages.
        
        Args:
            user1_id: UUID of the first user
            user2_id: UUID of the second user
            
        Returns:
            List of dictionaries containing mutual team information:
                - team_id: UUID of the team
                - team_name: Name of the team
                - team_tag: Team abbreviation
                - game_name: Name of the game
                - user1_role: Role of user1 in the team
                - user2_role: Role of user2 in the team
                - user1_joined_at: When user1 joined the team
                - user2_joined_at: When user2 joined the team
        
        **Validates: Requirements 10.4**
        """
        from teams.models import TeamMember
        
        # Get active team memberships for user1
        user1_teams = set(TeamMember.objects.filter(
            user_id=user1_id,
            status='active'
        ).values_list('team_id', flat=True))
        
        # Get active team memberships for user2
        user2_teams = set(TeamMember.objects.filter(
            user_id=user2_id,
            status='active'
        ).values_list('team_id', flat=True))
        
        # Find intersection (mutual teams)
        mutual_team_ids = user1_teams.intersection(user2_teams)
        
        if not mutual_team_ids:
            return []
        
        # Get detailed information for mutual teams
        mutual_teams_data = []
        
        # Get team memberships for both users in mutual teams
        user1_memberships = {
            membership.team_id: membership
            for membership in TeamMember.objects.filter(
                user_id=user1_id,
                team_id__in=mutual_team_ids,
                status='active'
            ).select_related('team', 'team__game')
        }
        
        user2_memberships = {
            membership.team_id: membership
            for membership in TeamMember.objects.filter(
                user_id=user2_id,
                team_id__in=mutual_team_ids,
                status='active'
            ).select_related('team', 'team__game')
        }
        
        # Build mutual teams data
        for team_id in mutual_team_ids:
            user1_membership = user1_memberships.get(team_id)
            user2_membership = user2_memberships.get(team_id)
            
            # Both memberships should exist, but check to be safe
            if user1_membership and user2_membership:
                team = user1_membership.team
                mutual_teams_data.append({
                    'team_id': str(team.id),
                    'team_name': team.name,
                    'team_tag': team.tag,
                    'game_name': team.game.name if team.game else 'Unknown',
                    'user1_role': user1_membership.role,
                    'user2_role': user2_membership.role,
                    'user1_joined_at': user1_membership.joined_at.isoformat() if user1_membership.joined_at else None,
                    'user2_joined_at': user2_membership.joined_at.isoformat() if user2_membership.joined_at else None,
                })
        
        # Sort by team name for consistent ordering
        mutual_teams_data.sort(key=lambda x: x['team_name'])
        
        return mutual_teams_data
    
    @classmethod
    def get_user_teams(cls, user_id: uuid.UUID) -> List[uuid.UUID]:
        """
        Get list of team IDs that a user is an active member of.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of team UUIDs where user has active membership
        """
        from teams.models import TeamMember
        
        return list(TeamMember.objects.filter(
            user_id=user_id,
            status='active'
        ).values_list('team_id', flat=True))
    
    @classmethod
    def count_mutual_teams(cls, user1_id: uuid.UUID, user2_id: uuid.UUID) -> int:
        """
        Count the number of mutual teams between two users.
        
        Args:
            user1_id: UUID of the first user
            user2_id: UUID of the second user
            
        Returns:
            Integer count of mutual teams
        """
        user1_teams = set(cls.get_user_teams(user1_id))
        user2_teams = set(cls.get_user_teams(user2_id))
        
        return len(user1_teams.intersection(user2_teams))
