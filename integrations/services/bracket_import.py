from django.db import transaction
from tournaments.models import Bracket, Match, Participant
from integrations.models import ExternalMatch as ExternalMatchModel


def build_bracket_from_external_matches(external_tournament, bracket_name="Imported Bracket"):
    """
    Build a local Bracket + Match objects from stored ExternalMatch records.
    Returns (Bracket, created_count) or (None, 0) on failure.
    """
    local_tournament = external_tournament.local_tournament
    if not local_tournament:
        return None, 0
    if local_tournament.brackets.filter(name=bracket_name).exists():
        return None, 0

    ext_matches = ExternalMatchModel.objects.filter(
        tournament=external_tournament,
    ).order_by('round', 'external_id')

    if not ext_matches.exists():
        return None, 0

    max_round = ext_matches.last().round or 0

    with transaction.atomic():
        bracket = Bracket.objects.create(
            tournament=local_tournament,
            bracket_type='main',
            name=bracket_name,
            total_rounds=max_round,
            current_round=1,
        )

        created = 0
        for idx, em in enumerate(ext_matches):
            p1 = None
            p2 = None
            players = em.players or []
            if len(players) >= 1:
                p1 = _resolve_participant(local_tournament, players[0])
            if len(players) >= 2:
                p2 = _resolve_participant(local_tournament, players[1])

            scores = em.scores or {}
            score_p1 = scores.get(str(players[0])) if players else 0
            score_p2 = scores.get(str(players[1])) if len(players) > 1 else 0

            winner = None
            if p1 and p2 and score_p1 is not None and score_p2 is not None:
                if score_p1 > score_p2:
                    winner = p1
                elif score_p2 > score_p1:
                    winner = p2

            Match.objects.create(
                tournament=local_tournament,
                bracket=bracket,
                round_number=em.round or 1,
                match_number=idx + 1,
                match_letter=chr(65 + idx) if idx < 26 else f"M{idx+1}",
                participant1=p1,
                participant2=p2,
                score_p1=score_p1 or 0,
                score_p2=score_p2 or 0,
                winner=winner,
                status='completed' if winner else 'pending',
            )
            created += 1

    return bracket, created


def _resolve_participant(tournament, external_username):
    """Try to find a local Participant by username or team name."""
    name = str(external_username).strip()
    try:
        return (
            Participant.objects.filter(
                tournament=tournament, team__name__iexact=name
            ).first()
            or Participant.objects.filter(
                tournament=tournament, user__username__iexact=name
            ).first()
        )
    except Exception:
        return None
