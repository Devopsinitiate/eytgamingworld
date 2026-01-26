"""
Tournament caching utilities for performance optimization.
Implements Redis caching for tournament statistics and data.
"""

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)


class TournamentCache:
    """
    Centralized caching utilities for tournament data.
    Provides consistent cache key generation and TTL management.
    """
    
    # Cache TTL settings (in seconds)
    STATS_TTL = 300  # 5 minutes for statistics
    PARTICIPANTS_TTL = 600  # 10 minutes for participant lists
    MATCHES_TTL = 180  # 3 minutes for match data
    TIMELINE_TTL = 1800  # 30 minutes for timeline phases
    BRACKET_TTL = 900  # 15 minutes for bracket data
    
    @classmethod
    def get_tournament_stats(cls, tournament_id):
        """
        Get cached tournament statistics.
        Returns None if not cached.
        """
        cache_key = f"tournament_stats:{tournament_id}"
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache get failed for {cache_key}: {e}")
            return None
    
    @classmethod
    def set_tournament_stats(cls, tournament_id, stats_data):
        """
        Cache tournament statistics with TTL.
        """
        cache_key = f"tournament_stats:{tournament_id}"
        try:
            cache.set(cache_key, stats_data, cls.STATS_TTL)
            logger.debug(f"Cached tournament stats for {tournament_id}")
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")
    
    @classmethod
    def get_participant_list(cls, tournament_id, page=1):
        """
        Get cached participant list for a specific page.
        """
        cache_key = f"tournament_participants:{tournament_id}:page_{page}"
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache get failed for {cache_key}: {e}")
            return None
    
    @classmethod
    def set_participant_list(cls, tournament_id, participants_data, page=1):
        """
        Cache participant list with pagination support.
        """
        cache_key = f"tournament_participants:{tournament_id}:page_{page}"
        try:
            cache.set(cache_key, participants_data, cls.PARTICIPANTS_TTL)
            logger.debug(f"Cached participants for tournament {tournament_id}, page {page}")
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")
    
    @classmethod
    def get_match_data(cls, tournament_id, match_type='recent'):
        """
        Get cached match data (recent, upcoming, live).
        """
        cache_key = f"tournament_matches:{tournament_id}:{match_type}"
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache get failed for {cache_key}: {e}")
            return None
    
    @classmethod
    def set_match_data(cls, tournament_id, match_data, match_type='recent'):
        """
        Cache match data with type-specific keys.
        """
        cache_key = f"tournament_matches:{tournament_id}:{match_type}"
        try:
            cache.set(cache_key, match_data, cls.MATCHES_TTL)
            logger.debug(f"Cached {match_type} matches for tournament {tournament_id}")
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")
    
    @classmethod
    def get_timeline_phases(cls, tournament_id):
        """
        Get cached timeline phases.
        """
        cache_key = f"tournament_timeline:{tournament_id}"
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache get failed for {cache_key}: {e}")
            return None
    
    @classmethod
    def set_timeline_phases(cls, tournament_id, timeline_data):
        """
        Cache timeline phases data.
        """
        cache_key = f"tournament_timeline:{tournament_id}"
        try:
            cache.set(cache_key, timeline_data, cls.TIMELINE_TTL)
            logger.debug(f"Cached timeline for tournament {tournament_id}")
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")
    
    @classmethod
    def get_bracket_preview(cls, tournament_id):
        """
        Get cached bracket preview data.
        """
        cache_key = f"tournament_bracket_preview:{tournament_id}"
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache get failed for {cache_key}: {e}")
            return None
    
    @classmethod
    def set_bracket_preview(cls, tournament_id, bracket_data):
        """
        Cache bracket preview data.
        """
        cache_key = f"tournament_bracket_preview:{tournament_id}"
        try:
            cache.set(cache_key, bracket_data, cls.BRACKET_TTL)
            logger.debug(f"Cached bracket preview for tournament {tournament_id}")
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")
    
    @classmethod
    def invalidate_tournament_cache(cls, tournament_id):
        """
        Invalidate all cached data for a tournament.
        Call this when tournament data changes.
        """
        cache_keys = [
            f"tournament_stats:{tournament_id}",
            f"tournament_timeline:{tournament_id}",
            f"tournament_bracket_preview:{tournament_id}",
        ]
        
        # Invalidate participant pages (we don't know how many pages exist)
        for page in range(1, 11):  # Assume max 10 pages
            cache_keys.append(f"tournament_participants:{tournament_id}:page_{page}")
        
        # Invalidate match data
        for match_type in ['recent', 'upcoming', 'live']:
            cache_keys.append(f"tournament_matches:{tournament_id}:{match_type}")
        
        try:
            cache.delete_many(cache_keys)
            logger.info(f"Invalidated cache for tournament {tournament_id}")
        except Exception as e:
            logger.warning(f"Cache invalidation failed for tournament {tournament_id}: {e}")
    
    @classmethod
    def warm_tournament_cache(cls, tournament):
        """
        Pre-populate cache with tournament data.
        Useful for high-traffic tournaments.
        """
        from .models import Tournament
        
        try:
            # Warm up statistics
            stats_data = cls._generate_tournament_stats(tournament)
            cls.set_tournament_stats(tournament.id, stats_data)
            
            # Warm up timeline
            timeline_data = tournament.get_timeline_phases()
            cls.set_timeline_phases(tournament.id, timeline_data)
            
            # Warm up first page of participants
            participants = tournament.participants.select_related(
                'user', 'team'
            ).order_by('seed', 'registered_at')[:20]
            
            participants_data = [
                {
                    'id': str(p.id),
                    'display_name': p.display_name,
                    'seed': p.seed,
                    'checked_in': p.checked_in,
                    'team_name': p.team.name if p.team else None,
                    'avatar_url': p.user.avatar.url if p.user and p.user.avatar else None,
                }
                for p in participants
            ]
            cls.set_participant_list(tournament.id, participants_data, page=1)
            
            logger.info(f"Warmed cache for tournament {tournament.id}")
            
        except Exception as e:
            logger.error(f"Cache warming failed for tournament {tournament.id}: {e}")
    
    @classmethod
    def _generate_tournament_stats(cls, tournament):
        """
        Generate tournament statistics data for caching.
        """
        return {
            'participants': {
                'registered': tournament.total_registered,
                'checked_in': tournament.total_checked_in,
                'capacity': tournament.max_participants,
                'percentage_full': (tournament.total_registered / tournament.max_participants) * 100 if tournament.max_participants > 0 else 0
            },
            'engagement': {
                'views': tournament.view_count,
                'shares': getattr(tournament, 'share_count', 0),
                'registrations_today': tournament.get_registrations_today()
            },
            'matches': {
                'total': tournament.matches.count(),
                'completed': tournament.matches.filter(status='completed').count(),
                'in_progress': tournament.matches.filter(status='in_progress').count(),
            },
            'cached_at': timezone.now().isoformat()
        }


class CacheInvalidationMixin:
    """
    Mixin to automatically invalidate tournament cache when models change.
    Add this to tournament-related models that should trigger cache invalidation.
    """
    
    def save(self, *args, **kwargs):
        """Override save to invalidate cache."""
        super().save(*args, **kwargs)
        
        # Get tournament ID from the model
        tournament_id = self._get_tournament_id()
        if tournament_id:
            TournamentCache.invalidate_tournament_cache(tournament_id)
    
    def delete(self, *args, **kwargs):
        """Override delete to invalidate cache."""
        tournament_id = self._get_tournament_id()
        super().delete(*args, **kwargs)
        
        if tournament_id:
            TournamentCache.invalidate_tournament_cache(tournament_id)
    
    def _get_tournament_id(self):
        """
        Get tournament ID from the model.
        Override this method in subclasses.
        """
        if hasattr(self, 'tournament'):
            return self.tournament.id
        elif hasattr(self, 'tournament_id'):
            return self.tournament_id
        return None


def cache_tournament_view(cache_key_func, timeout=300):
    """
    Decorator for caching tournament view responses.
    
    Args:
        cache_key_func: Function that takes request and returns cache key
        timeout: Cache timeout in seconds
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            cache_key = cache_key_func(request, *args, **kwargs)
            
            # Try to get from cache
            try:
                cached_response = cache.get(cache_key)
                if cached_response is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_response
            except Exception as e:
                logger.warning(f"Cache get failed for {cache_key}: {e}")
            
            # Generate response
            response = view_func(request, *args, **kwargs)
            
            # Cache the response
            try:
                cache.set(cache_key, response, timeout)
                logger.debug(f"Cached response for {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set failed for {cache_key}: {e}")
            
            return response
        return wrapper
    return decorator