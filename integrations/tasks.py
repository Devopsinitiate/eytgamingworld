import logging
from celery import shared_task
from django.utils import timezone
from .models import ExternalProvider, ExternalTournament, ExternalPlayer, ExternalMatch, SyncLog
from .services import StartGGService

logger = logging.getLogger(__name__)


def _get_service(provider_name):
    provider = ExternalProvider.objects.get(name=provider_name, is_active=True)
    svc_map = {
        'start.gg': StartGGService,
    }
    svc_class = svc_map.get(provider.name)
    if not svc_class:
        raise ValueError(f"No service class for provider: {provider.name}")
    return svc_class(provider), provider


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_tournament_from_startgg(self, tournament_id):
    try:
        ext_tournament = ExternalTournament.objects.get(id=tournament_id)
        svc, provider = _get_service('start.gg')
    except Exception as e:
        logger.error(f"sync_tournament_from_startgg setup failed: {e}")
        return

    log = SyncLog.objects.create(
        provider=provider, sync_type='tournament',
        status='running',
    )
    try:
        data = svc.get_tournament(ext_tournament.external_id)
        tourney_data = data.get('tournament', {})
        ext_tournament.title = tourney_data.get('name', ext_tournament.title)
        ext_tournament.status = _map_status(tourney_data)
        ext_tournament.raw_data = tourney_data
        ext_tournament.save()

        # Sync events/entrants
        events = tourney_data.get('events', [])
        for event in events:
            _sync_event_entrants(svc, provider, event, ext_tournament)

        log.status = 'completed'
        log.items_processed = len(events)
        log.completed_at = timezone.now()
        log.save()
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.completed_at = timezone.now()
        log.save()
        logger.error(f"sync_tournament_from_startgg failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_active_tournament_standings(self):
    try:
        svc, provider = _get_service('start.gg')
    except Exception as e:
        logger.error(f"sync_active_tournament_standings setup failed: {e}")
        return

    active = ExternalTournament.objects.filter(
        provider=provider, status='active'
    )
    log = SyncLog.objects.create(
        provider=provider, sync_type='standings',
        status='running',
    )
    count = 0
    for ext_tournament in active:
        try:
            events = ext_tournament.raw_data.get('events', [])
            for event in events:
                event_id = event.get('id')
                if event_id:
                    data = svc.get_event_standings(event_id)
                    ext_tournament.raw_data['standings'] = data
                    ext_tournament.save(update_fields=['raw_data'])
                    count += 1
        except Exception as e:
            logger.warning(f"Standings sync failed for {ext_tournament}: {e}")

    log.status = 'completed'
    log.items_processed = count
    log.completed_at = timezone.now()
    log.save()


def _sync_event_entrants(svc, provider, event, ext_tournament):
    event_id = event.get('id')
    if not event_id:
        return
    data = svc.get_event_entrants(event_id)
    entrants = data.get('event', {}).get('entrants', {}).get('nodes', [])
    for entrant in entrants:
        ExternalPlayer.objects.get_or_create(
            provider=provider,
            external_id=str(entrant.get('id')),
            defaults={
                'username': entrant.get('name', 'Unknown'),
                'game': ext_tournament.game,
            }
        )


def _map_status(tourney_data):
    now = timezone.now()
    start = tourney_data.get('startAt')
    end = tourney_data.get('endAt')
    if not start or not end:
        return 'pending'
    if now.timestamp() < start:
        return 'pending'
    if start <= now.timestamp() < end:
        return 'active'
    return 'completed'
