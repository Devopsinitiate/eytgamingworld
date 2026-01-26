"""
API views for tournament data with caching and pagination.
Provides JSON endpoints for AJAX requests and real-time updates.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.utils import timezone
from .models import Tournament, Participant, Match
from .cache_utils import TournamentCache
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@cache_page(60 * 5)  # Cache for 5 minutes
def tournament_stats_api(request, slug):
    """
    API endpoint for tournament statistics.
    Returns cached statistics data in JSON format.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    
    # Try to get from cache first
    cached_stats = TournamentCache.get_tournament_stats(tournament.id)
    
    if cached_stats:
        return JsonResponse(cached_stats)
    
    # Generate fresh statistics
    stats = {
        'participants': {
            'registered': tournament.total_registered,
            'checked_in': tournament.total_checked_in,
            'capacity': tournament.max_participants,
            'percentage_full': (tournament.total_registered / tournament.max_participants) * 100 if tournament.max_participants > 0 else 0,
            'spots_remaining': tournament.spots_remaining
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
            'pending': tournament.matches.filter(status='pending').count()
        },
        'status': tournament.status,
        'is_registration_open': tournament.is_registration_open,
        'is_full': tournament.is_full
    }
    
    # Cache the statistics
    TournamentCache.set_tournament_stats(tournament.id, stats)
    
    return JsonResponse(stats)


@require_http_methods(["GET"])
def tournament_participants_api(request, slug):
    """
    API endpoint for paginated participant list.
    Supports filtering, sorting, and search.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    
    # Get pagination parameters
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    per_page = min(per_page, 100)  # Max 100 per page
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    checked_in_filter = request.GET.get('checked_in', '')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'seed')
    
    # Try to get from cache if no filters applied
    cache_key_suffix = f"{page}_{per_page}_{status_filter}_{checked_in_filter}_{search_query}_{sort_by}"
    if not any([status_filter, checked_in_filter, search_query]) and sort_by == 'seed':
        cached_participants = TournamentCache.get_participant_list(tournament.id, page)
        if cached_participants:
            return JsonResponse({
                'participants': cached_participants,
                'page': page,
                'has_next': False,  # Would need to calculate this
                'total': len(cached_participants)
            })
    
    # Build optimized queryset
    participants_queryset = tournament.participants.select_related(
        'user', 'team'
    )
    
    # Apply filters
    if status_filter:
        participants_queryset = participants_queryset.filter(status=status_filter)
    
    if checked_in_filter:
        checked_in_bool = checked_in_filter.lower() == 'true'
        participants_queryset = participants_queryset.filter(checked_in=checked_in_bool)
    
    if search_query:
        participants_queryset = participants_queryset.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(team__name__icontains=search_query)
        )
    
    # Apply sorting
    sort_fields = {
        'seed': 'seed',
        'name': 'user__username',
        'registered': 'registered_at',
        'wins': '-matches_won',
        'losses': 'matches_lost'
    }
    order_by = sort_fields.get(sort_by, 'seed')
    participants_queryset = participants_queryset.order_by(order_by, 'registered_at')
    
    # Paginate
    paginator = Paginator(participants_queryset, per_page)
    
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        return JsonResponse({
            'participants': [],
            'page': page,
            'has_next': False,
            'has_previous': False,
            'total': 0,
            'total_pages': 0
        })
    
    # Serialize participants
    participants_data = []
    for participant in page_obj:
        participant_data = {
            'id': str(participant.id),
            'display_name': participant.display_name,
            'seed': participant.seed,
            'checked_in': participant.checked_in,
            'status': participant.status,
            'registered_at': participant.registered_at.isoformat(),
            'matches_won': participant.matches_won,
            'matches_lost': participant.matches_lost,
            'win_rate': participant.win_rate,
            'final_placement': participant.final_placement,
            'team': {
                'name': participant.team.name,
                'id': str(participant.team.id),
                'logo_url': participant.team.logo.url if participant.team and participant.team.logo else None
            } if participant.team else None,
            'user': {
                'avatar_url': participant.user.avatar.url if participant.user and participant.user.avatar else None,
                'username': participant.user.username if participant.user else None,
                'display_name': participant.user.get_display_name() if participant.user else None
            } if participant.user else None
        }
        participants_data.append(participant_data)
    
    # Cache first page with default settings
    if page == 1 and not any([status_filter, checked_in_filter, search_query]) and sort_by == 'seed':
        TournamentCache.set_participant_list(tournament.id, participants_data, page)
    
    return JsonResponse({
        'participants': participants_data,
        'page': page,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total': paginator.count,
        'total_pages': paginator.num_pages,
        'per_page': per_page
    })


@require_http_methods(["GET"])
def tournament_matches_api(request, slug):
    """
    API endpoint for tournament matches.
    Supports filtering by status and pagination.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    
    # Get parameters
    match_type = request.GET.get('type', 'recent')  # recent, upcoming, live, all
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))
    per_page = min(per_page, 50)  # Max 50 per page
    
    # Try to get from cache for common queries
    if page == 1 and per_page == 10 and match_type in ['recent', 'upcoming', 'live']:
        cached_matches = TournamentCache.get_match_data(tournament.id, match_type)
        if cached_matches:
            return JsonResponse({
                'matches': cached_matches,
                'type': match_type,
                'page': page,
                'has_next': False
            })
    
    # Build optimized queryset
    matches_queryset = tournament.matches.select_related(
        'participant1', 'participant2', 'winner', 'bracket',
        'participant1__user', 'participant1__team',
        'participant2__user', 'participant2__team'
    )
    
    # Filter by type
    if match_type == 'recent':
        matches_queryset = matches_queryset.filter(
            status='completed'
        ).order_by('-completed_at')
    elif match_type == 'upcoming':
        matches_queryset = matches_queryset.filter(
            status__in=['ready', 'pending']
        ).order_by('round_number', 'match_number')
    elif match_type == 'live':
        matches_queryset = matches_queryset.filter(
            status='in_progress'
        ).order_by('round_number', 'match_number')
    else:
        matches_queryset = matches_queryset.order_by('round_number', 'match_number')
    
    # Paginate
    paginator = Paginator(matches_queryset, per_page)
    
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        return JsonResponse({
            'matches': [],
            'type': match_type,
            'page': page,
            'has_next': False,
            'total': 0
        })
    
    # Serialize matches
    matches_data = []
    for match in page_obj:
        match_data = {
            'id': str(match.id),
            'round_number': match.round_number,
            'match_number': match.match_number,
            'status': match.status,
            'score_p1': match.score_p1,
            'score_p2': match.score_p2,
            'bracket_name': match.bracket.name if match.bracket else None,
            'participant1': {
                'display_name': match.participant1.display_name,
                'id': str(match.participant1.id),
                'seed': match.participant1.seed
            } if match.participant1 else None,
            'participant2': {
                'display_name': match.participant2.display_name,
                'id': str(match.participant2.id),
                'seed': match.participant2.seed
            } if match.participant2 else None,
            'winner': {
                'display_name': match.winner.display_name,
                'id': str(match.winner.id)
            } if match.winner else None,
            'completed_at': match.completed_at.isoformat() if match.completed_at else None,
            'started_at': match.started_at.isoformat() if match.started_at else None,
            'scheduled_time': match.scheduled_time.isoformat() if match.scheduled_time else None
        }
        matches_data.append(match_data)
    
    # Cache first page for common queries
    if page == 1 and per_page == 10 and match_type in ['recent', 'upcoming', 'live']:
        TournamentCache.set_match_data(tournament.id, matches_data, match_type)
    
    return JsonResponse({
        'matches': matches_data,
        'type': match_type,
        'page': page,
        'has_next': page_obj.has_next(),
        'total': paginator.count
    })


@require_http_methods(["POST"])
def invalidate_tournament_cache(request, slug):
    """
    API endpoint to manually invalidate tournament cache.
    Requires organizer permissions.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    
    # Check permissions
    if not request.user.is_authenticated or request.user != tournament.organizer:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Invalidate cache
    TournamentCache.invalidate_tournament_cache(tournament.id)
    
    return JsonResponse({
        'success': True,
        'message': 'Tournament cache invalidated successfully'
    })

@require_http_methods(["GET"])
def tournament_updates_api(request, slug):
    """
    API endpoint for real-time tournament updates.
    Returns current tournament state for live updates with enhanced match statistics.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    
    try:
        # Get fresh statistics with enhanced match data
        stats = {
            'participants': {
                'registered': tournament.total_registered,
                'checked_in': tournament.total_checked_in,
                'capacity': tournament.max_participants,
                'percentage_full': (tournament.total_registered / tournament.max_participants) * 100 if tournament.max_participants > 0 else 0,
                'spots_remaining': tournament.max_participants - tournament.total_registered if tournament.max_participants > tournament.total_registered else 0
            },
            'engagement': {
                'views': tournament.view_count,
                'shares': getattr(tournament, 'share_count', 0)
            },
            'matches': {
                'total': tournament.matches.count(),
                'completed': tournament.matches.filter(status='completed').count(),
                'in_progress': tournament.matches.filter(status='in_progress').count(),
                'pending': tournament.matches.filter(status__in=['pending', 'ready']).count()
            }
        }
        
        # Get recent matches if tournament is active
        recent_matches = []
        if tournament.status in ['in_progress', 'completed']:
            matches = tournament.matches.filter(
                status='completed'
            ).select_related(
                'participant1', 'participant2', 'winner'
            ).order_by('-completed_at')[:5]
            
            recent_matches = [{
                'id': str(match.id),
                'participant1': match.participant1.display_name if match.participant1 else 'TBD',
                'participant2': match.participant2.display_name if match.participant2 else 'TBD',
                'score': f"{match.score_p1} - {match.score_p2}" if match.score_p1 is not None and match.score_p2 is not None else 'vs',
                'winner': match.winner.display_name if match.winner else None,
                'completed_at': match.completed_at.isoformat() if match.completed_at else None,
                'status': match.status
            } for match in matches]
        
        # Get live matches for in-progress tournaments
        live_matches = []
        if tournament.status == 'in_progress':
            live_matches_qs = tournament.matches.filter(
                status='in_progress'
            ).select_related(
                'participant1', 'participant2'
            ).order_by('round_number', 'match_number')[:10]
            
            live_matches = [{
                'id': str(match.id),
                'participant1': match.participant1.display_name if match.participant1 else 'TBD',
                'participant2': match.participant2.display_name if match.participant2 else 'TBD',
                'score': f"{match.score_p1 or 0} - {match.score_p2 or 0}",
                'round_number': match.round_number,
                'match_number': match.match_number,
                'started_at': match.started_at.isoformat() if match.started_at else None,
                'status': match.status
            } for match in live_matches_qs]
        
        # Get participant updates with check-in status
        participants_summary = {
            'count': tournament.participants.count(),
            'checked_in_count': tournament.participants.filter(checked_in=True).count(),
            'last_registration': None,
            'last_updated': tournament.updated_at.isoformat() if hasattr(tournament, 'updated_at') else timezone.now().isoformat()
        }
        
        # Get most recent registration
        latest_participant = tournament.participants.order_by('-registered_at').first()
        if latest_participant:
            participants_summary['last_registration'] = {
                'name': latest_participant.display_name,
                'registered_at': latest_participant.registered_at.isoformat()
            }
        
        # Calculate timeline progress
        timeline_progress = {
            'current_phase': tournament.status,
            'progress_percentage': {
                'draft': 0,
                'registration': 25,
                'check_in': 50,
                'in_progress': 75,
                'completed': 100,
                'cancelled': 0
            }.get(tournament.status, 0)
        }
        
        return JsonResponse({
            'status': tournament.status,
            'stats': stats,
            'matches': recent_matches,
            'live_matches': live_matches,
            'participants': participants_summary,
            'timeline': timeline_progress,
            'timestamp': timezone.now().isoformat(),
            'connection_status': 'connected'
        })
        
    except Exception as e:
        logger.error(f"Error fetching tournament updates for {slug}: {e}")
        return JsonResponse({
            'error': 'Failed to fetch updates',
            'connection_status': 'error',
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def tournament_bracket_api(request, slug):
    """
    API endpoint for tournament bracket data.
    Returns bracket structure and match data.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    
    try:
        # Check if tournament has brackets
        if not tournament.brackets.exists():
            return JsonResponse({
                'has_bracket': False,
                'message': 'Bracket not yet generated'
            })
        
        # Get bracket data
        bracket = tournament.brackets.filter(bracket_type='main').first()
        if not bracket:
            return JsonResponse({
                'has_bracket': False,
                'message': 'Main bracket not found'
            })
        
        # Get matches for bracket
        matches = tournament.matches.select_related(
            'participant1', 'participant2', 'winner'
        ).order_by('round_number', 'match_number')
        
        bracket_data = {
            'has_bracket': True,
            'format': tournament.format,
            'current_round': bracket.current_round,
            'total_rounds': bracket.total_rounds,
            'matches': [{
                'id': str(match.id),
                'round_number': match.round_number,
                'match_number': match.match_number,
                'participant1': match.participant1.display_name if match.participant1 else 'TBD',
                'participant2': match.participant2.display_name if match.participant2 else 'TBD',
                'score': f"{match.score_p1} - {match.score_p2}" if match.score_p1 is not None else 'vs',
                'winner': match.winner.display_name if match.winner else None,
                'status': match.status,
                'started_at': match.started_at.isoformat() if match.started_at else None,
                'completed_at': match.completed_at.isoformat() if match.completed_at else None
            } for match in matches]
        }
        
        return JsonResponse(bracket_data)
        
    except Exception as e:
        logger.error(f"Error fetching bracket data for {slug}: {e}")
        return JsonResponse({'error': 'Failed to fetch bracket data'}, status=500)