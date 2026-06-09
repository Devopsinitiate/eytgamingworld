from django.utils import timezone
from django.core.cache import cache


def check_and_advance_tournament_statuses():
    """
    Check for tournaments that should advance status and update them.
    Used by Celery task (primary) and fallback endpoint/view (secondary).

    Returns a dict with counts + lists of tournament IDs per transition.
    """
    from .models import Tournament

    now = timezone.now()
    result = {
        'draft_to_registration': 0,
        'registration_to_checkin': 0,
        'checkin_to_inprogress': 0,
        'draft_ids': [],
        'checkin_ids': [],
        'inprogress_ids': [],
    }

    # Draft -> Registration
    to_open = Tournament.objects.filter(
        status='draft',
        registration_start__lte=now,
        registration_end__gt=now,
    )
    for t in to_open:
        t.status = 'registration'
        t.published_at = now
        t.save()
        result['draft_to_registration'] += 1
        result['draft_ids'].append(str(t.id))

    # Registration -> Check-in
    to_checkin = Tournament.objects.filter(
        status='registration',
        registration_end__lte=now,
        check_in_start__lte=now,
    )
    for t in to_checkin:
        t.status = 'check_in'
        t.save()
        result['registration_to_checkin'] += 1
        result['checkin_ids'].append(str(t.id))

    # Check-in -> In Progress
    to_start = Tournament.objects.filter(
        status='check_in',
        start_datetime__lte=now,
    )
    for t in to_start:
        for p in t.participants.filter(status='confirmed', checked_in=False):
            p.check_in_participant(force=True)
        t.refresh_from_db()

        if t.total_checked_in >= t.min_participants:
            t.status = 'in_progress'
            t.save()
            try:
                t.create_bracket()
            except Exception:
                pass
            result['checkin_to_inprogress'] += 1
            result['inprogress_ids'].append(str(t.id))

    return result


def should_attempt_fallback(tournament_id):
    """
    Check if enough time has passed since last fallback attempt.
    Prevents running the full status check on every page load.
    """
    cache_key = f'tournament_fallback_{tournament_id}'
    if cache.get(cache_key):
        return False
    cache.set(cache_key, True, 300)
    return True
