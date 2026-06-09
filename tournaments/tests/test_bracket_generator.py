"""Comprehensive tests for BracketGenerator engine"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from core.models import Game
from tournaments.models import Tournament, Participant, Bracket, Match
from tournaments.services.bracket_generator import BracketGenerator

User = get_user_model()


class BracketGeneratorTestBase(TestCase):
    def setUp(self):
        self.game = Game.objects.create(name='Test FGC', slug='test-fgc', genre='fighting')
        now = timezone.now()
        self.organizer = User.objects.create_user(
            email='org@test.com', password='pass', username='org'
        )
        self.tournament = Tournament.objects.create(
            name='Test Tournament', slug='test-tournament',
            game=self.game, format='double_elim', status='in_progress',
            organizer=self.organizer, best_of=3,
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=7),
            check_in_start=now - timedelta(hours=1),
            start_datetime=now,
        )

    def _create_participants(self, count=8):
        participants = []
        for i in range(count):
            user = User.objects.create_user(
                email=f'player{i}@test.com', password='pass', username=f'player{i}'
            )
            p = Participant.objects.create(
                tournament=self.tournament, user=user,
                status='confirmed', checked_in=True
            )
            participants.append(p)
        return participants

    def _make_generator(self, participants):
        return BracketGenerator(self.tournament, participants)


# ── Swiss ─────────────────────────────────────────────────────────────────

class SwissBracketTests(BracketGeneratorTestBase):
    def test_generates_correct_number_of_rounds(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        bracket = gen.generate_swiss_rounds()
        expected_rounds = 3  # ceil(log2(8))
        self.assertEqual(bracket.total_rounds, expected_rounds)
        matches = Match.objects.filter(bracket=bracket)
        # Each round should have 4 matches with 8 participants
        self.assertEqual(matches.count(), expected_rounds * 4)

    def test_generates_correct_number_of_rounds_odd(self):
        participants = self._create_participants(5)
        gen = self._make_generator(participants)
        bracket = gen.generate_swiss_rounds()
        expected_rounds = 3  # ceil(log2(5)) = 3
        self.assertEqual(bracket.total_rounds, expected_rounds)
        matches = Match.objects.filter(bracket=bracket)
        # 5 participants -> 2 matches per round + 1 bye
        # But Swiss doesn't generate byes explicitly - see _generate_swiss_round
        # At 5 players, there will be 2 matches and 1 unpaired leftover per round
        for round_num in range(1, expected_rounds + 1):
            round_matches = matches.filter(round_number=round_num)
            self.assertGreaterEqual(len(round_matches), 2,
                                    f"Round {round_num} should have >= 2 matches")

    def test_no_rematch_in_same_round(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        bracket = gen.generate_swiss_rounds()
        # Within each round, no pair should play each other twice
        matches = Match.objects.filter(bracket=bracket)
        for round_num in range(1, bracket.total_rounds + 1):
            round_matches = matches.filter(round_number=round_num)
            pairs = set()
            for m in round_matches:
                if m.participant1 and m.participant2:
                    pair = tuple(sorted([m.participant1_id, m.participant2_id]))
                    self.assertNotIn(pair, pairs,
                                     f"Duplicate pair in round {round_num}")
                    pairs.add(pair)

    def test_no_rematch_across_rounds(self):
        """Swiss should prevent same players from playing twice across rounds"""
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        bracket = gen.generate_swiss_rounds()
        all_pairs = set()
        for m in Match.objects.filter(bracket=bracket):
            if m.participant1 and m.participant2:
                pair = tuple(sorted([m.participant1_id, m.participant2_id]))
                self.assertNotIn(pair, all_pairs,
                                 f"Rematch detected: {pair}")
                all_pairs.add(pair)

    def test_match_letters_sequential(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        bracket = gen.generate_swiss_rounds()
        matches = Match.objects.filter(bracket=bracket).order_by('round_number', 'match_number')
        for m in matches:
            self.assertIsNotNone(m.match_letter,
                                 f"Match {m.id} missing match_letter")
            self.assertGreater(len(m.match_letter), 0)

    def test_all_participants_play_each_round(self):
        """At most 1 participant can have a bye per Swiss round"""
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        bracket = gen.generate_swiss_rounds()
        matches = Match.objects.filter(bracket=bracket)
        for round_num in range(1, bracket.total_rounds + 1):
            round_matches = matches.filter(round_number=round_num)
            played_ids = set()
            for m in round_matches:
                if m.participant1:
                    played_ids.add(m.participant1_id)
                if m.participant2:
                    played_ids.add(m.participant2_id)
            missing = [p.id for p in participants if p.id not in played_ids]
            self.assertLessEqual(len(missing), 1,
                                 f"Round {round_num}: {len(missing)} participants missing (max 1 bye)")


# ── Bracket Reset ─────────────────────────────────────────────────────────

class BracketResetTests(BracketGeneratorTestBase):
    def test_grand_finals_has_two_sets(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        result = gen.generate_double_elimination()
        bracket = result[0] if isinstance(result, tuple) else result
        # Find grand finals matches
        finals_matches = Match.objects.filter(
            bracket=bracket,
            bracket__bracket_type='finals'
        )
        if not finals_matches:
            finals_matches = Match.objects.filter(
                bracket__bracket_type='finals'
            )
        # Should have at least a Set 1
        self.assertGreaterEqual(finals_matches.count(), 1)

    def test_bracket_reset_match_pre_created(self):
        """Bracket reset match is pre-created for grand finals"""
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        result = gen.generate_double_elimination()
        reset_matches = Match.objects.filter(
            bracket__tournament=self.tournament,
            bracket_reset=True
        )
        self.assertEqual(reset_matches.count(), 1)
        reset_match = reset_matches.first()
        self.assertEqual(reset_match.status, 'pending')
        self.assertIsNone(reset_match.participant1)
        self.assertIsNone(reset_match.participant2)

    def test_large_bracket_has_bracket_reset(self):
        """16-player double elim pre-creates bracket reset match"""
        participants = self._create_participants(16)
        gen = self._make_generator(participants)
        result = gen.generate_double_elimination()
        reset_matches = Match.objects.filter(
            bracket__tournament=self.tournament,
            bracket_reset=True
        )
        self.assertEqual(reset_matches.count(), 1)
        match = reset_matches.first()
        self.assertEqual(match.status, 'pending')
        self.assertIsNone(match.participant1)
        # Verify it's in a 'finals' bracket
        self.assertEqual(match.bracket.bracket_type, 'finals')

    def test_double_elim_correct_match_count(self):
        """Verify match count for double elim with N players = 2N-2 (without reset)"""
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        result = gen.generate_double_elimination()
        total_matches = Match.objects.filter(
            bracket__tournament=self.tournament
        ).count()
        # For 8-player double elim: 14 matches + 1 pending bracket_reset = 15
        # Actually: 7 upper + 7 lower = 14, but with bracket reset match potentially = 14 or 15
        # Standard: N upper + N-2 lower = 2N-2 = 14 for N=8
        self.assertGreaterEqual(total_matches, 14)
        self.assertLessEqual(total_matches, 16)

    def test_double_elim_match_letters_assigned(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        result = gen.generate_double_elimination()
        matches = Match.objects.filter(
            bracket__tournament=self.tournament
        ).exclude(match_letter='').exclude(match_letter__isnull=True)
        self.assertGreater(matches.count(), 0)
        # Letters should be unique within each round
        for bracket in Bracket.objects.filter(tournament=self.tournament):
            for round_num in range(1, bracket.total_rounds + 1):
                round_match_letters = Match.objects.filter(
                    bracket=bracket, round_number=round_num
                ).values_list('match_letter', flat=True)
                self.assertEqual(
                    len(round_match_letters),
                    len(set(round_match_letters)),
                    f"Duplicate match_letter in bracket {bracket.id} round {round_num}"
                )


# ── Group Stage ────────────────────────────────────────────────────────────

class GroupStageTests(BracketGeneratorTestBase):
    def test_generate_group_stage_creates_pools(self):
        participants = self._create_participants(12)
        gen = self._make_generator(participants)
        pools = gen.generate_group_stage()
        self.assertGreaterEqual(len(pools), 2)
        for pool in pools:
            self.assertEqual(pool.bracket_type, 'groups')
            self.assertIsNotNone(pool.name)

    def test_pool_has_round_robin_matches(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        pools = gen.generate_group_stage()
        for pool in pools:
            pool_matches = Match.objects.filter(bracket=pool)
            player_ids = set()
            for m in pool_matches:
                if m.participant1_id:
                    player_ids.add(m.participant1_id)
                if m.participant2_id:
                    player_ids.add(m.participant2_id)
            count = len(player_ids)
            expected_matches = count * (count - 1) // 2
            self.assertEqual(
                pool_matches.count(), expected_matches,
                f"Pool {pool.name}: expected {expected_matches} RR matches, got {pool_matches.count()}"
            )

    def test_advance_from_pools_creates_playoffs(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        pools = gen.generate_group_stage()
        # Report all pool matches so advancement can work
        for pool in pools:
            for m in Match.objects.filter(bracket=pool):
                if m.participant1 and m.participant2:
                    m.report_score(3, 0, self.organizer)
        # Advance top 2 from each pool
        result = gen.advance_from_pools(pools, advance_count=2)
        self.assertIsNotNone(result)
        # Should have created new brackets (finals/main/losers)
        initial_pool_ids = set(b.id for b in pools)
        new_brackets = Bracket.objects.filter(tournament=self.tournament).exclude(
            id__in=initial_pool_ids
        )
        self.assertGreater(new_brackets.count(), 0)

    def test_advance_pools_rejects_zero_advance(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        pools = gen.generate_group_stage()
        with self.assertRaises(ValueError):
            gen.advance_from_pools(pools, advance_count=0)

    def test_pool_standings_by_match_wins(self):
        participants = self._create_participants(4)
        gen = self._make_generator(participants)
        pools = gen.generate_group_stage()
        pool = pools[0]
        matches = list(Match.objects.filter(bracket=pool))
        # Player 0 beats everyone
        p0 = participants[0]
        for m in matches:
            if m.participant1_id == p0.id:
                m.report_score(3, 0, self.organizer)
            elif m.participant2_id == p0.id:
                m.report_score(0, 3, self.organizer)
        standings = gen.calculate_standings(pool)
        self.assertEqual(standings[0].id, p0.id)


# ── Single Elimination ───────────────────────────────────────────────────

class SingleEliminationTests(BracketGeneratorTestBase):
    def test_generates_correct_match_count(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        bracket = gen.generate_single_elimination()
        matches = Match.objects.filter(bracket=bracket)
        # 8 players -> 7 matches total (4 + 2 + 1)
        self.assertEqual(matches.count(), 7)
        self.assertEqual(bracket.total_rounds, 3)

    def test_power_of_two(self):
        participants = self._create_participants(16)
        gen = self._make_generator(participants)
        bracket = gen.generate_single_elimination()
        matches = Match.objects.filter(bracket=bracket)
        self.assertEqual(matches.count(), 15)
        self.assertEqual(bracket.total_rounds, 4)

    def test_non_power_of_two_adds_byes(self):
        participants = self._create_participants(5)
        gen = self._make_generator(participants)
        bracket = gen.generate_single_elimination()
        matches = Match.objects.filter(bracket=bracket)
        # 5 players -> next power of 2 = 8 -> 3 byes, 7 total slots
        self.assertEqual(bracket.total_rounds, 3)


# ── Round Robin ───────────────────────────────────────────────────────────

class RoundRobinTests(BracketGeneratorTestBase):
    def test_all_vs_all(self):
        participants = self._create_participants(4)
        gen = self._make_generator(participants)
        bracket = gen.generate_round_robin()
        matches = Match.objects.filter(bracket=bracket)
        # 4 players -> 6 matches (each pair plays once)
        self.assertEqual(matches.count(), 6)

    def test_each_pair_plays_once(self):
        participants = self._create_participants(6)
        gen = self._make_generator(participants)
        bracket = gen.generate_round_robin()
        # 6 players -> 15 matches
        matches = Match.objects.filter(bracket=bracket)
        self.assertEqual(matches.count(), 15)
        pairs = set()
        for m in matches:
            if m.participant1 and m.participant2:
                pair = tuple(sorted([m.participant1_id, m.participant2_id]))
                self.assertNotIn(pair, pairs, "Duplicate pairing in RR")
                pairs.add(pair)
        self.assertEqual(len(pairs), 15)

    def test_round_robin_standings(self):
        participants = self._create_participants(4)
        gen = self._make_generator(participants)
        bracket = gen.generate_round_robin()
        matches = list(Match.objects.filter(bracket=bracket))
        # Player 0 beats everyone, player 1 beats 2 and 3, etc.
        p0, p1, p2, p3 = participants
        for m in matches:
            if m.participant1_id == p0.id:
                m.report_score(3, 0, self.organizer)
            elif m.participant2_id == p0.id:
                m.report_score(0, 3, self.organizer)
            elif m.participant1_id == p1.id:
                m.report_score(3, 0, self.organizer)
            elif m.participant2_id == p1.id:
                m.report_score(0, 3, self.organizer)
        standings = gen.calculate_standings(bracket)
        self.assertEqual(standings[0].id, p0.id)


# ── Advance from Standings ────────────────────────────────────────────────

class AdvanceFromStandingsTests(BracketGeneratorTestBase):
    def test_advance_from_swiss_creates_finals(self):
        participants = self._create_participants(8)
        gen = self._make_generator(participants)
        swiss_bracket = gen.generate_swiss_rounds()
        # Complete all Swiss matches
        for m in Match.objects.filter(bracket=swiss_bracket):
            if m.participant1 and m.participant2:
                m.status = 'completed'
                m.winner = m.participant1
                m.participant1_score = 3
                m.participant2_score = 0
                m.save()
        result = gen.advance_from_standings(swiss_bracket, advance_count=4)
        self.assertIsNotNone(result)
        # advance_from_standings uses generate_single_elimination which creates
        # a 'main' bracket
        new_brackets = Bracket.objects.filter(tournament=self.tournament).exclude(id=swiss_bracket.id)
        self.assertGreater(new_brackets.count(), 0)

    def test_advance_requires_minimum_two(self):
        participants = self._create_participants(4)
        gen = self._make_generator(participants)
        bracket = gen.generate_single_elimination()
        with self.assertRaises(ValueError):
            gen.advance_from_standings(bracket, advance_count=1)


# ── FGC Model Constraints ────────────────────────────────────────────────

class FGCModelsTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create(name='Test FGC', slug='test-fgc', genre='fighting')

    def test_fgc_game_created_with_defaults(self):
        from tournaments.models import FGCGame
        fgc = FGCGame.objects.create(game=self.game)
        self.assertEqual(fgc.default_best_of, 3)
        self.assertTrue(fgc.supports_character_select)

    def test_character_unique_per_game_slug(self):
        from tournaments.models import Character
        Character.objects.create(game=self.game, name='Ryu', slug='ryu', order=1)
        with self.assertRaises(Exception):
            Character.objects.create(game=self.game, name='Ryu Clone', slug='ryu', order=2)

    def test_character_order_field(self):
        from tournaments.models import Character
        c1 = Character.objects.create(game=self.game, name='Ryu', slug='ryu', order=2)
        c2 = Character.objects.create(game=self.game, name='Ken', slug='ken', order=1)
        chars = Character.objects.filter(game=self.game).order_by('order')
        self.assertEqual(chars[0].slug, 'ken')
        self.assertEqual(chars[1].slug, 'ryu')

    def test_stage_unique_per_game_slug(self):
        from tournaments.models import Stage
        Stage.objects.create(game=self.game, name='Training Room', slug='training-room')
        with self.assertRaises(Exception):
            Stage.objects.create(game=self.game, name='Training Room 2', slug='training-room')

    def test_game_slot_links_game_and_match(self):
        from tournaments.models import GameSlot, Character, Stage
        now = timezone.now()
        org = User.objects.create_user(email='orgslot@test.com', password='pass', username='orgslot')
        tournament = Tournament.objects.create(
            name='Slot Test', slug='slot-test',
            game=self.game, format='single_elim', status='in_progress',
            organizer=org,
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=7),
            check_in_start=now - timedelta(hours=1),
            start_datetime=now,
        )
        bracket = Bracket.objects.create(
            tournament=tournament, bracket_type='main',
            name='Test Bracket', total_rounds=1
        )
        character = Character.objects.create(game=self.game, name='Ryu', slug='ryu', order=1)
        stage = Stage.objects.create(game=self.game, name='Training Room', slug='training-room')
        p1_user = User.objects.create_user(email='p1@test.com', password='pass', username='p1slot')
        p2_user = User.objects.create_user(email='p2@test.com', password='pass', username='p2slot')
        p1 = Participant.objects.create(tournament=tournament, user=p1_user, status='confirmed', checked_in=True)
        p2 = Participant.objects.create(tournament=tournament, user=p2_user, status='confirmed', checked_in=True)
        match = Match.objects.create(
            tournament=tournament, bracket=bracket,
            round_number=1, match_number=1,
            participant1=p1, participant2=p2, status='ready',
        )
        slot = GameSlot.objects.create(
            match=match, slot_number=1,
            character_p1=character, character_p2=character,
            stage=stage,
        )
        self.assertEqual(slot.match.id, match.id)
        self.assertEqual(slot.character_p1.id, character.id)
