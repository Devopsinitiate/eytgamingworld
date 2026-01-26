"""
Real-time updates system for tournament detail pages.
Implements Server-Sent Events (SSE) for live match updates and participant status changes.
"""

import json
import time
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from .models import Tournament, Match, Participant
import logging

logger = logging.getLogger(__name__)


class TournamentLiveUpdater:
    """
    Manages live updates for tournament data using Server-Sent Events.
    Handles match updates, participant status changes, and statistics updates.
    """
    
    def __init__(self, tournament):
        self.tournament = tournament
        self.last_update = timezone.now()
        
    def get_current_state(self):
        """Get current tournament state for initial load"""
        try:
            # Get live matches
            live_matches = self.tournament.matches.filter(
                status='in_progress'
            ).select_related('participant1', 'participant2', 'bracket')
            
            # Get recent completed matches
            recent_matches = self.tournament.matches.filter(
                status='completed'
            ).select_related(
                'participant1', 'participant2', 'winner', 'bracket'
            ).order_by('-completed_at')[:5]
            
            # Get upcoming matches
            upcoming_matches = self.tournament.matches.filter(
                status__in=['ready', 'pending']
            ).select_related(
                'participant1', 'participant2', 'bracket'
            ).order_by('round_number', 'match_number')[:5]
            
            # Get updated statistics
            stats = self._get_tournament_stats()
            
            # Get participant updates
            participants = self._get_participant_updates()
            
            return {
                'type': 'full_update',
                'timestamp': timezone.now().isoformat(),
                'tournament_id': str(self.tournament.id),
                'tournament_slug': self.tournament.slug,
                'live_matches': [self._serialize_match(match) for match in live_matches],
                'recent_matches': [self._serialize_match(match) for match in recent_matches],
                'upcoming_matches': [self._serialize_match(match) for match in upcoming_matches],
                'statistics': stats,
                'participants': participants,
                'tournament_status': self.tournament.status
            }
        except Exception as e:
            logger.error(f"Error getting tournament state: {e}")
            return {
                'type': 'error',
                'message': 'Failed to get tournament state',
                'timestamp': timezone.now().isoformat()
            }
    
    def get_updates_since(self, last_update):
        """Get updates since the last timestamp"""
        try:
            updates = []
            
            # Check for match updates - use completed_at or started_at as fallback if updated_at doesn't exist
            try:
                updated_matches = self.tournament.matches.filter(
                    updated_at__gt=last_update
                ).select_related('participant1', 'participant2', 'winner', 'bracket')
            except Exception:
                # Fallback: use completed_at and started_at for tracking changes
                updated_matches = self.tournament.matches.filter(
                    models.Q(completed_at__gt=last_update) | models.Q(started_at__gt=last_update)
                ).select_related('participant1', 'participant2', 'winner', 'bracket')
            
            for match in updated_matches:
                timestamp = getattr(match, 'updated_at', match.completed_at or match.started_at or timezone.now())
                updates.append({
                    'type': 'match_update',
                    'match': self._serialize_match(match),
                    'timestamp': timestamp.isoformat() if timestamp else timezone.now().isoformat()
                })
            
            # Check for participant updates
            updated_participants = self.tournament.participants.filter(
                updated_at__gt=last_update
            ).select_related('user', 'team')
            
            for participant in updated_participants:
                updates.append({
                    'type': 'participant_update',
                    'participant': self._serialize_participant(participant),
                    'timestamp': participant.updated_at.isoformat()
                })
            
            # Check for tournament status changes
            if self.tournament.updated_at > last_update:
                updates.append({
                    'type': 'tournament_update',
                    'status': self.tournament.status,
                    'statistics': self._get_tournament_stats(),
                    'timestamp': self.tournament.updated_at.isoformat()
                })
            
            return updates
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return [{
                'type': 'error',
                'message': 'Failed to get updates',
                'timestamp': timezone.now().isoformat()
            }]
    
    def _serialize_match(self, match):
        """Serialize match data for JSON response"""
        return {
            'id': str(match.id),
            'round_number': match.round_number,
            'match_number': match.match_number,
            'status': match.status,
            'bracket_name': match.bracket.name if match.bracket else None,
            'participant1': {
                'id': str(match.participant1.id) if match.participant1 else None,
                'display_name': match.participant1.display_name if match.participant1 else 'TBD',
                'seed': match.participant1.seed if match.participant1 else None,
                'is_winner': match.winner == match.participant1 if match.winner else False
            },
            'participant2': {
                'id': str(match.participant2.id) if match.participant2 else None,
                'display_name': match.participant2.display_name if match.participant2 else 'TBD',
                'seed': match.participant2.seed if match.participant2 else None,
                'is_winner': match.winner == match.participant2 if match.winner else False
            },
            'score_p1': match.score_p1,
            'score_p2': match.score_p2,
            'started_at': match.started_at.isoformat() if match.started_at else None,
            'completed_at': match.completed_at.isoformat() if match.completed_at else None,
            'is_grand_finals': match.is_grand_finals,
            'scheduled_time': match.scheduled_time.isoformat() if match.scheduled_time else None
        }
    
    def _serialize_participant(self, participant):
        """Serialize participant data for JSON response"""
        return {
            'id': str(participant.id),
            'display_name': participant.display_name,
            'seed': participant.seed,
            'status': participant.status,
            'checked_in': participant.checked_in,
            'check_in_time': participant.check_in_time.isoformat() if participant.check_in_time else None,
            'matches_won': participant.matches_won,
            'matches_lost': participant.matches_lost,
            'win_rate': participant.win_rate,
            'final_placement': participant.final_placement,
            'has_team': bool(participant.team),
            'team_name': participant.team.name if participant.team else None
        }
    
    def _get_tournament_stats(self):
        """Get current tournament statistics"""
        # Calculate actual participant counts
        participant_count = self.tournament.participants.count()
        checked_in_count = self.tournament.participants.filter(checked_in=True).count()
        
        return {
            'participants': {
                'registered': participant_count,
                'checked_in': checked_in_count,
                'capacity': self.tournament.max_participants,
                'percentage_full': (participant_count / self.tournament.max_participants) * 100 if self.tournament.max_participants > 0 else 0
            },
            'matches': {
                'total': self.tournament.matches.count(),
                'completed': self.tournament.matches.filter(status='completed').count(),
                'in_progress': self.tournament.matches.filter(status='in_progress').count(),
                'upcoming': self.tournament.matches.filter(status__in=['ready', 'pending']).count()
            },
            'engagement': {
                'views': self.tournament.view_count,
                'shares': getattr(self.tournament, 'share_count', 0),
                'registrations_today': self.tournament.get_registrations_today()
            },
            'current_round': self._get_current_round()
        }
    
    def _get_participant_updates(self):
        """Get participant list with current status"""
        participants = self.tournament.participants.select_related(
            'user', 'team'
        ).order_by('seed', 'registered_at')
        
        return [self._serialize_participant(p) for p in participants]
    
    def _get_current_round(self):
        """Get current tournament round"""
        if self.tournament.brackets.exists():
            main_bracket = self.tournament.brackets.filter(bracket_type='main').first()
            return main_bracket.current_round if main_bracket else 1
        return 1


@never_cache
def tournament_live_updates(request, slug):
    """
    Server-Sent Events endpoint for tournament live updates.
    Streams real-time updates for matches, participants, and statistics.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    
    # Check if tournament supports live updates (in progress or check-in)
    if tournament.status not in ['check_in', 'in_progress']:
        return StreamingHttpResponse(
            "data: " + json.dumps({
                'type': 'error',
                'message': 'Live updates not available for this tournament status'
            }) + "\n\n",
            content_type='text/event-stream'
        )
    
    def event_stream():
        """Generator function for Server-Sent Events"""
        updater = TournamentLiveUpdater(tournament)
        
        # Send initial state
        initial_state = updater.get_current_state()
        yield f"data: {json.dumps(initial_state, cls=DjangoJSONEncoder)}\n\n"
        
        last_update = timezone.now()
        
        # Keep connection alive and send updates
        while True:
            try:
                # Check for updates every 5 seconds
                time.sleep(5)
                
                # Get updates since last check
                updates = updater.get_updates_since(last_update)
                
                if updates:
                    for update in updates:
                        yield f"data: {json.dumps(update, cls=DjangoJSONEncoder)}\n\n"
                    
                    last_update = timezone.now()
                else:
                    # Send heartbeat to keep connection alive
                    heartbeat = {
                        'type': 'heartbeat',
                        'timestamp': timezone.now().isoformat()
                    }
                    yield f"data: {json.dumps(heartbeat, cls=DjangoJSONEncoder)}\n\n"
                
                # Refresh tournament object periodically to get latest data
                tournament.refresh_from_db()
                
                # Stop streaming if tournament is completed or cancelled
                if tournament.status in ['completed', 'cancelled']:
                    final_update = {
                        'type': 'tournament_ended',
                        'status': tournament.status,
                        'timestamp': timezone.now().isoformat()
                    }
                    yield f"data: {json.dumps(final_update, cls=DjangoJSONEncoder)}\n\n"
                    break
                    
            except Exception as e:
                logger.error(f"Error in live updates stream: {e}")
                error_update = {
                    'type': 'error',
                    'message': 'Connection error occurred',
                    'timestamp': timezone.now().isoformat()
                }
                yield f"data: {json.dumps(error_update, cls=DjangoJSONEncoder)}\n\n"
                break
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    
    # Set headers for SSE
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Cache-Control'
    
    return response


@csrf_exempt
def tournament_stats_api(request, slug):
    """
    API endpoint for tournament statistics (fallback for polling).
    Used when SSE is not available or as a backup.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    tournament = get_object_or_404(Tournament, slug=slug)
    updater = TournamentLiveUpdater(tournament)
    
    try:
        stats = updater._get_tournament_stats()
        
        # Add additional data for API response
        response_data = {
            'success': True,
            'tournament_id': str(tournament.id),
            'tournament_slug': tournament.slug,
            'status': tournament.status,
            'statistics': stats,
            'timestamp': timezone.now().isoformat(),
            'last_updated': tournament.updated_at.isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error getting tournament stats: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get tournament statistics'
        }, status=500)


def trigger_match_update(match_id):
    """
    Utility function to trigger match update notifications.
    Called when match data changes (score updates, status changes).
    """
    try:
        from .models import Match
        match = Match.objects.select_related(
            'tournament', 'participant1', 'participant2', 'winner', 'bracket'
        ).get(id=match_id)
        
        # Update the match's updated_at timestamp to trigger live updates
        # Handle case where updated_at field might not exist yet
        try:
            match.save(update_fields=['updated_at'])
        except Exception:
            # Fallback: just save the match to update any timestamp
            match.save()
        
        logger.info(f"Triggered live update for match {match_id}")
        
    except Match.DoesNotExist:
        logger.error(f"Match {match_id} not found for live update")
    except Exception as e:
        logger.error(f"Error triggering match update: {e}")


def trigger_participant_update(participant_id):
    """
    Utility function to trigger participant update notifications.
    Called when participant status changes (check-in, registration status).
    """
    try:
        from .models import Participant
        participant = Participant.objects.select_related(
            'tournament', 'user', 'team'
        ).get(id=participant_id)
        
        # Update the participant's updated_at timestamp to trigger live updates
        participant.save(update_fields=['updated_at'])
        
        # Also update tournament stats
        tournament = participant.tournament
        tournament.save(update_fields=['updated_at'])
        
        logger.info(f"Triggered live update for participant {participant_id}")
        
    except Participant.DoesNotExist:
        logger.error(f"Participant {participant_id} not found for live update")
    except Exception as e:
        logger.error(f"Error triggering participant update: {e}")


def trigger_tournament_update(tournament_id):
    """
    Utility function to trigger tournament-wide update notifications.
    Called when tournament status or major data changes.
    """
    try:
        from .models import Tournament
        tournament = Tournament.objects.get(id=tournament_id)
        
        # Update the tournament's updated_at timestamp to trigger live updates
        tournament.save(update_fields=['updated_at'])
        
        logger.info(f"Triggered live update for tournament {tournament_id}")
        
    except Tournament.DoesNotExist:
        logger.error(f"Tournament {tournament_id} not found for live update")
    except Exception as e:
        logger.error(f"Error triggering tournament update: {e}")