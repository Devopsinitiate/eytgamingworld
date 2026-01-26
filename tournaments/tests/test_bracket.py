# tournaments/tests/test_bracket.py
"""Unit tests for the placeholder bracket generation service.
The service provides a deterministic single‑elimination bracket.
"""

from django.test import SimpleTestCase
from tournaments.services.bracket import generate_bracket


class BracketServiceTest(SimpleTestCase):
    def test_even_number_of_participants(self):
        participants = ["alice", "bob", "carol", "dave"]
        matches = generate_bracket(participants)
        # Expect 2 matches: alice vs dave, bob vs carol (sorted order)
        expected = [("alice", "dave"), ("bob", "carol")]
        self.assertEqual(matches, expected)

    def test_odd_number_of_participants(self):
        participants = ["alice", "bob", "carol"]
        matches = generate_bracket(participants)
        # Expect one match and one bye (None)
        expected = [("alice", "carol"), ("bob", None)]
        self.assertEqual(matches, expected)

    def test_deterministic_order(self):
        participants = ["zeta", "alpha", "gamma", "beta"]
        matches = generate_bracket(participants)
        # Sorted participants: alpha, beta, gamma, zeta
        expected = [("alpha", "zeta"), ("beta", "gamma")]
        self.assertEqual(matches, expected)
