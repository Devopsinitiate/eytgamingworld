# tournaments/services/bracket.py
"""Placeholder bracket generation service.
This module provides a very simple deterministic bracket generator used as a
starting point for the tournament engine. It can be expanded later with more
advanced seeding, double‑elimination, etc.
"""

from typing import List, Tuple


def generate_bracket(participants: List[str]) -> List[Tuple[str, str]]:
    """Generate a simple single‑elimination bracket.

    Args:
        participants: A list of participant identifiers (e.g., usernames or IDs).

    Returns:
        A list of match tuples. Each tuple contains two participants. If the
        number of participants is odd, the last participant receives a *bye*
        and is paired with ``None``.
    """
    # Ensure deterministic ordering
    participants = sorted(participants)
    matches: List[Tuple[str, str]] = []
    # Pair first with last, second with second‑last, etc.
    while len(participants) > 1:
        p1 = participants.pop(0)
        p2 = participants.pop(-1)
        matches.append((p1, p2))
    # Handle odd participant count
    if participants:
        matches.append((participants[0], None))
    return matches
