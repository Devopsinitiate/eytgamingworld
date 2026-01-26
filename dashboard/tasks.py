"""
Celery tasks for dashboard functionality.

This module provides background tasks for recommendation refresh,
activity cleanup, and achievement checks.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def refresh_user_recommendations(user_id):
    """
    Refresh recommendations for a specific user.
    
    This task regenerates tournament and team recommendations
    for a user, clearing expired recommendations and creating
    new ones based on current data.
    
    Args:
        user_id: UUID string of the user
        
    Returns:
        Dictionary with recommendation counts
    
    **Validates: Requirements 13.5**
    """
    from dashboard.services import RecommendationService
    import uuid
    
    try:
        # Convert string to UUID
        user_uuid = uuid.UUID(str(user_id))
        
        # Refresh recommendations
        result = RecommendationService.refresh_recommendations(user_uuid)
        
        logger.info(
            f"Refreshed recommendations for user {user_id}: "
            f"{result['total_count']} recommendations generated"
        )
        
        return {
            'user_id': str(user_id),
            'tournament_count': result['tournament_recommendations'].count(),
            'team_count': result['team_recommendations'].count(),
            'total_count': result['total_count'],
        }
    
    except Exception as e:
        logger.error(f"Error refreshing recommendations for user {user_id}: {str(e)}")
        raise


@shared_task
def refresh_all_user_recommendations():
    """
    Refresh recommendations for all active users.
    
    This task is scheduled to run daily and refreshes recommendations
    for all users who have game profiles and are active.
    
    Returns:
        Dictionary with statistics about the refresh operation
    
    **Validates: Requirements 13.5**
    """
    from core.models import User
    from dashboard.services import RecommendationService
    
    try:
        # Get all active users with game profiles
        users = User.objects.filter(
            is_active=True,
            game_profiles__isnull=False
        ).distinct()
        
        success_count = 0
        error_count = 0
        total_recommendations = 0
        
        for user in users:
            try:
                result = RecommendationService.refresh_recommendations(user.id)
                success_count += 1
                total_recommendations += result['total_count']
            except Exception as e:
                logger.error(f"Error refreshing recommendations for user {user.id}: {str(e)}")
                error_count += 1
        
        logger.info(
            f"Daily recommendation refresh complete: "
            f"{success_count} users processed, "
            f"{error_count} errors, "
            f"{total_recommendations} total recommendations generated"
        )
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'total_recommendations': total_recommendations,
        }
    
    except Exception as e:
        logger.error(f"Error in daily recommendation refresh: {str(e)}")
        raise


@shared_task
def cleanup_old_activities():
    """
    Delete Activity records older than 90 days.
    
    This task is scheduled to run weekly to maintain database size
    and comply with data retention policies. Activities older than
    90 days are automatically removed.
    
    Returns:
        Dictionary with cleanup statistics
    
    **Validates: Requirements Data privacy**
    """
    from dashboard.services import ActivityService
    
    try:
        # Delete activities older than 90 days
        deleted_count = ActivityService.delete_old_activities(days=90)
        
        logger.info(
            f"Activity cleanup complete: {deleted_count} activities deleted"
        )
        
        return {
            'deleted_count': deleted_count,
            'retention_days': 90,
        }
    
    except Exception as e:
        logger.error(f"Error in activity cleanup: {str(e)}")
        raise


@shared_task
def check_user_achievements(user_id, event_type):
    """
    Check and award achievements for a user based on an event.
    
    This task is called from signals when events occur that may
    trigger achievement awards (e.g., tournament completion,
    profile updates, team joins).
    
    Args:
        user_id: UUID string of the user
        event_type: Type of event that triggered the check
            - 'tournament_completed': Check tournament-related achievements
            - 'team_joined': Check team-related achievements
            - 'profile_completed': Check profile completion achievement
            
    Returns:
        Dictionary with achievement check results
    
    **Validates: Requirements 7.1**
    """
    from dashboard.services import AchievementService
    import uuid
    
    try:
        # Convert string to UUID
        user_uuid = uuid.UUID(str(user_id))
        
        # Check and award achievements
        awarded_achievements = AchievementService.check_achievements(user_uuid, event_type)
        
        logger.info(
            f"Achievement check for user {user_id} (event: {event_type}): "
            f"{len(awarded_achievements)} achievements awarded"
        )
        
        return {
            'user_id': str(user_id),
            'event_type': event_type,
            'achievements_awarded': len(awarded_achievements),
            'achievement_ids': [str(a.achievement_id) for a in awarded_achievements],
        }
    
    except Exception as e:
        logger.error(f"Error checking achievements for user {user_id}: {str(e)}")
        raise
