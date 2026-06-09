import random
import math
import string
from collections import defaultdict
from typing import List, Optional, Dict, Tuple

from django.db.models import Q
from django.utils import timezone

from ..models import Tournament, Participant, Bracket, Match


class BracketGenerator:
    """Generate tournament brackets based on format"""

    MATCH_LETTERS = string.ascii_uppercase  # A, B, C, ... Z

    def __init__(self, tournament: Tournament, participants: List[Participant]):
        self.tournament = tournament
        self.participants = participants
        self.participant_count = len(participants)

    # ── Seeding ─────────────────────────────────────────────────────────────

    def seed_participants(self):
        """Apply seeding based on tournament settings"""
        if self.tournament.seeding_method == 'random':
            random.shuffle(self.participants)
        elif self.tournament.seeding_method == 'skill':
            self.participants.sort(
                key=lambda p: p.user.game_profiles.filter(
                    game=self.tournament.game
                ).first().skill_rating if p.user else 0,
                reverse=True
            )
        elif self.tournament.seeding_method == 'registration':
            self.participants.sort(key=lambda p: p.registered_at)

        if self.tournament.seeding_method != 'manual':
            for idx, participant in enumerate(self.participants, start=1):
                participant.seed = idx
                participant.save()

    def next_power_of_two(self, n: int) -> int:
        if n <= 1:
            return 2
        return 2 ** math.ceil(math.log2(n))

    def build_seeded_slot_order(self, bracket_size: int) -> list:
        """
        Standard FGC/start.gg seeded slot order.
        8-slot: [1, 8, 5, 4, 3, 6, 7, 2]
        """
        slots = [1, 2]
        size = 2
        while size < bracket_size:
            size *= 2
            new_slots = []
            for s in slots:
                new_slots.append(s)
                new_slots.append(size + 1 - s)
            slots = new_slots
        return slots

    def _next_match_letter(self, bracket, round_number):
        """Generate next match letter ID (A, B, C...) for a bracket."""
        existing = Match.objects.filter(
            bracket=bracket, round_number=round_number
        ).count()
        idx = existing
        if idx < 26:
            return self.MATCH_LETTERS[idx]
        # Beyond Z, use AA, AB, etc.
        return self.MATCH_LETTERS[idx // 26 - 1] + self.MATCH_LETTERS[idx % 26]

    # ── Single Elimination ──────────────────────────────────────────────────

    def generate_single_elimination(self):
        """
        Generate a single-elimination bracket using standard FGC/start.gg seeding.
        """
        if self.participant_count < 1:
            raise ValueError("Cannot generate bracket with no participants")

        self.seed_participants()

        bracket_size = self.next_power_of_two(max(2, self.participant_count))
        total_rounds = int(math.log2(bracket_size))

        bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='main',
            name='Main Bracket',
            total_rounds=total_rounds,
        )

        slot_order = self.build_seeded_slot_order(bracket_size)
        seed_to_participant = {p.seed: p for p in self.participants}

        matches_by_round = {1: []}
        round_1_match_count = bracket_size // 2

        for match_num in range(round_1_match_count):
            slot_a = slot_order[match_num * 2]
            slot_b = slot_order[match_num * 2 + 1]
            p1 = seed_to_participant.get(slot_a)
            p2 = seed_to_participant.get(slot_b)

            match = Match.objects.create(
                tournament=self.tournament,
                bracket=bracket,
                round_number=1,
                match_number=match_num + 1,
                match_letter=self._next_match_letter(bracket, 1),
                participant1=p1,
                participant2=p2,
            )

            if p1 is None and p2 is None:
                pass
            elif p1 is None or p2 is None:
                match.status = 'completed'
                match.winner = p1 or p2
                match.score_p1 = 1 if p1 else 0
                match.score_p2 = 1 if p2 else 0
            else:
                match.status = 'ready'

            match.save()
            matches_by_round[1].append(match)

        for round_num in range(2, total_rounds + 1):
            matches_in_round = bracket_size // (2 ** round_num)
            matches_by_round[round_num] = []
            for match_num in range(matches_in_round):
                match = Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_num,
                    match_number=match_num + 1,
                    match_letter=self._next_match_letter(bracket, round_num),
                    is_grand_finals=(round_num == total_rounds),
                )
                matches_by_round[round_num].append(match)

        for round_num in range(1, total_rounds):
            for idx, match in enumerate(matches_by_round[round_num]):
                match.next_match_winner = matches_by_round[round_num + 1][idx // 2]
                match.save()

        for match in matches_by_round[1]:
            if match.status == 'completed' and match.winner and match.next_match_winner:
                next_m = match.next_match_winner
                if next_m.participant1 is None:
                    next_m.participant1 = match.winner
                elif next_m.participant2 is None:
                    next_m.participant2 = match.winner
                if next_m.participant1 and next_m.participant2:
                    next_m.status = 'ready'
                next_m.save()

        return bracket

    # ── Double Elimination ──────────────────────────────────────────────────

    def generate_double_elimination(self):
        """Generate double elimination bracket (winners + losers + grand finals)."""
        if self.participant_count < 2:
            raise ValueError("Double elimination requires at least 2 participants")

        self.seed_participants()

        bracket_size = self.next_power_of_two(max(2, self.participant_count))
        winners_rounds = int(math.log2(bracket_size))
        losers_rounds = (winners_rounds - 1) * 2

        winners_bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='main',
            name='Winners Bracket',
            total_rounds=winners_rounds
        )

        losers_bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='losers',
            name='Losers Bracket',
            total_rounds=losers_rounds
        )

        # Create separate finals bracket for grand finals + reset match
        finals_bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='finals',
            name='Grand Finals',
            total_rounds=2  # Round 1 = GF Set 1, Round 2 = GF Reset (if needed)
        )

        winners_matches = self._generate_bracket_rounds(
            winners_bracket, bracket_size, winners_rounds, is_winners=True
        )
        losers_matches = self._generate_losers_bracket(
            losers_bracket, bracket_size, losers_rounds
        )
        self._link_double_elimination(winners_matches, losers_matches)

        self._cleanup_losers_bracket(winners_matches, losers_matches)

        # Create grand finals Set 1 in the finals bracket
        gf_set_1 = Match.objects.create(
            tournament=self.tournament,
            bracket=finals_bracket,
            round_number=1,
            match_number=1,
            match_letter='GF',
            is_grand_finals=True,
            bracket_reset=False,
        )

        # Link winners final and losers final to grand finals
        winners_matches[winners_rounds][-1].next_match_winner = gf_set_1
        losers_matches[losers_rounds][-1].next_match_winner = gf_set_1
        winners_matches[winners_rounds][-1].save()
        losers_matches[losers_rounds][-1].save()

        # Create grand finals Set 2 (bracket reset) — starts hidden, activated by report_score
        gf_set_2 = Match.objects.create(
            tournament=self.tournament,
            bracket=finals_bracket,
            round_number=2,
            match_number=1,
            match_letter='GF2',
            is_grand_finals=True,
            bracket_reset=True,
            status='pending',
        )
        gf_set_1.next_match_winner = gf_set_2
        gf_set_1.save()

        return winners_bracket, losers_bracket

    def _generate_bracket_rounds(self, bracket, bracket_size, total_rounds, is_winners=False):
        """Generate single-elimination rounds within a bracket."""
        matches_by_round = {1: []}

        slot_order = self.build_seeded_slot_order(bracket_size)
        seed_to_participant = {p.seed: p for p in self.participants}

        round_1_match_count = bracket_size // 2
        for match_num in range(round_1_match_count):
            slot_a = slot_order[match_num * 2]
            slot_b = slot_order[match_num * 2 + 1]
            p1 = seed_to_participant.get(slot_a)
            p2 = seed_to_participant.get(slot_b)

            match = Match.objects.create(
                tournament=self.tournament,
                bracket=bracket,
                round_number=1,
                match_number=match_num + 1,
                match_letter=self._next_match_letter(bracket, 1),
                participant1=p1,
                participant2=p2,
            )

            if (p1 is None) != (p2 is None):
                match.status = 'completed'
                match.winner = p1 or p2
                match.score_p1 = 1 if p1 else 0
                match.score_p2 = 1 if p2 else 0
            elif p1 and p2:
                match.status = 'ready'

            match.save()
            matches_by_round[1].append(match)

        for round_num in range(2, total_rounds + 1):
            matches_in_round = bracket_size // (2 ** round_num)
            matches_by_round[round_num] = []
            for match_num in range(matches_in_round):
                match = Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_num,
                    match_number=match_num + 1,
                    match_letter=self._next_match_letter(bracket, round_num),
                )
                matches_by_round[round_num].append(match)

        for round_num in range(1, total_rounds):
            for idx, match in enumerate(matches_by_round[round_num]):
                match.next_match_winner = matches_by_round[round_num + 1][idx // 2]
                match.save()

        for match in matches_by_round[1]:
            if match.status == 'completed' and match.winner and match.next_match_winner:
                next_m = match.next_match_winner
                if next_m.participant1 is None:
                    next_m.participant1 = match.winner
                elif next_m.participant2 is None:
                    next_m.participant2 = match.winner
                if next_m.participant1 and next_m.participant2:
                    next_m.status = 'ready'
                next_m.save()

        return matches_by_round

    def _generate_losers_bracket(self, bracket, bracket_size, total_rounds):
        """Generate losers bracket structure."""
        matches_by_round = {}

        for round_num in range(1, total_rounds + 1):
            if round_num % 2 == 1:
                matches_in_round = bracket_size // (2 ** ((round_num + 3) // 2))
            else:
                matches_in_round = bracket_size // (2 ** ((round_num + 2) // 2))

            matches_by_round[round_num] = []
            for match_num in range(matches_in_round):
                match = Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_num,
                    match_number=match_num + 1,
                    match_letter=self._next_match_letter(bracket, round_num),
                )
                matches_by_round[round_num].append(match)

        for round_num in range(1, total_rounds):
            for idx, match in enumerate(matches_by_round[round_num]):
                if round_num + 1 in matches_by_round:
                    next_idx = idx // 2 if round_num % 2 == 0 else idx
                    if next_idx < len(matches_by_round[round_num + 1]):
                        match.next_match_winner = matches_by_round[round_num + 1][next_idx]
                        match.save()

        return matches_by_round

    def _link_double_elimination(self, winners_matches, losers_matches):
        """Link winners bracket losers to losers bracket.

        Standard start.gg double-elim pairing (8-player example):
          WR1[0] loser + WR1[2] loser → LR1[0]
          WR1[1] loser + WR1[3] loser → LR1[1]
          WR2[0] loser → LR2[0],  WR2[1] loser → LR2[1]
          WR3[0] (Winners Final) loser → LR_last[0]
        """
        for round_num in winners_matches:
            if round_num == 1:
                lr1 = losers_matches.get(1, [])
                if not lr1:
                    continue
                for idx, match in enumerate(winners_matches[1]):
                    lr_idx = idx % len(lr1)
                    match.next_match_loser = lr1[lr_idx]
                    match.save()
            else:
                losers_round = (round_num - 1) * 2
                if losers_round in losers_matches:
                    for idx, match in enumerate(winners_matches[round_num]):
                        if idx < len(losers_matches[losers_round]):
                            match.next_match_loser = losers_matches[losers_round][idx]
                            match.save()

    def _cleanup_losers_bracket(self, winners_matches, losers_matches):
        """
        Post-generation cleanup for losers bracket with byes.

        Cancels fully orphaned LR matches where ALL upstream WR1 feeders
        are byes (no losers expected). Partial matches (1 expected participant)
        are handled at runtime by Match._advance_walkover.
        """
        if 1 not in losers_matches:
            return

        for lr_idx, lr_match in enumerate(losers_matches[1]):
            viable = sum(
                1 for fm in lr_match.previous_loser_matches.all()
                if fm.participant1 is not None and fm.participant2 is not None
            )
            if viable == 0:
                lr_match.status = 'cancelled'
                lr_match.save()

    # ── Swiss System (Fixed) ────────────────────────────────────────────────

    def generate_swiss_rounds(self):
        """Generate ALL Swiss system rounds with score-bucket matching."""
        if self.participant_count < 2:
            raise ValueError("Swiss system requires at least 2 participants")

        self.seed_participants()

        total_rounds = math.ceil(math.log2(max(2, self.participant_count)))

        bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='main',
            name='Swiss Rounds',
            total_rounds=total_rounds,
        )

        # Track which participants have received a bye across rounds
        bye_receivers = set()

        for round_num in range(1, total_rounds + 1):
            self._generate_swiss_round(bracket, round_num, bye_receivers)

        return bracket

    def _generate_swiss_round(self, bracket, round_number, bye_receivers):
        """Generate ONE Swiss round using score-bucket matching with rematch prevention."""
        participants = list(self.participants)

        # 1. Score-bucket grouping: sort by (matches_won DESC, games_won DESC)
        participants.sort(
            key=lambda p: (p.matches_won, p.games_won),
            reverse=True
        )

        # 2. Group participants into score buckets
        buckets = defaultdict(list)
        for p in participants:
            buckets[(p.matches_won, p.games_won)].append(p)

        # 3. Build a set of already-played opponent pairs for rematch prevention
        played_pairs = self._get_played_pairs(bracket)

        # 4. Pair within each bucket with rematch prevention
        matches_created = []
        used = set()
        unmatched = []

        for score_key in sorted(buckets.keys(), reverse=True):
            pool = [p for p in buckets[score_key] if p.id not in used]
            paired_in_this_bucket = set()
            random.shuffle(pool)

            i = 0
            while i < len(pool) - 1:
                p1 = pool[i]
                # Find a partner for p1 that they haven't played yet
                partner = None
                for j in range(i + 1, len(pool)):
                    p2 = pool[j]
                    pair_key = tuple(sorted([p1.id, p2.id]))
                    if pair_key not in played_pairs and p2.id not in paired_in_this_bucket:
                        partner = p2
                        break

                if partner:
                    match = Match.objects.create(
                        tournament=self.tournament,
                        bracket=bracket,
                        round_number=round_number,
                        match_number=len(matches_created) + 1,
                        match_letter=self._next_match_letter(bracket, round_number),
                        participant1=p1,
                        participant2=partner,
                        status='ready',
                    )
                    matches_created.append(match)
                    used.add(p1.id)
                    used.add(partner.id)
                    paired_in_this_bucket.add(p1.id)
                    paired_in_this_bucket.add(partner.id)
                    played_pairs.add(tuple(sorted([p1.id, partner.id])))
                    pool = [p for p in pool if p.id not in used]
                    i = 0  # restart search
                else:
                    i += 1

            # Any unpaired from this bucket go to the unmatched pool
            for p in pool:
                if p.id not in used:
                    unmatched.append(p)

        # 5. Cross-bucket pairing for unmatched participants
        random.shuffle(unmatched)
        i = 0
        while i < len(unmatched) - 1:
            p1 = unmatched[i]
            p2 = unmatched[i + 1]
            pair_key = tuple(sorted([p1.id, p2.id]))
            if pair_key not in played_pairs:
                match = Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_number,
                    match_number=len(matches_created) + 1,
                    match_letter=self._next_match_letter(bracket, round_number),
                    participant1=p1,
                    participant2=p2,
                    status='ready',
                )
                matches_created.append(match)
                used.add(p1.id)
                used.add(p2.id)
                played_pairs.add(pair_key)
                i += 2
            else:
                i += 1

        # 6. Handle odd participant out (bye) — rotate who gets it
        remaining = [p for p in participants if p.id not in used]
        if remaining:
            # Give the bye to the participant who has received it least recently
            remaining.sort(key=lambda p: (
                p.id in bye_receivers,
                -(p.matches_won),
            ))
            bye_p = remaining[0]
            match = Match.objects.create(
                tournament=self.tournament,
                bracket=bracket,
                round_number=round_number,
                match_number=len(matches_created) + 1,
                match_letter='BYE',
                participant1=bye_p,
                status='completed',
                winner=bye_p,
                score_p1=1,
            )
            matches_created.append(match)
            bye_receivers.add(bye_p.id)

        return matches_created

    def _get_played_pairs(self, bracket):
        """Return set of frozensets of participant IDs that have already played in this bracket."""
        pairs = set()
        matches = Match.objects.filter(bracket=bracket).exclude(
            Q(participant1__isnull=True) | Q(participant2__isnull=True)
        )
        for m in matches:
            pair = tuple(sorted([m.participant1_id, m.participant2_id]))
            pairs.add(pair)
        return pairs

    # ── Round Robin ─────────────────────────────────────────────────────────

    def generate_round_robin(self):
        """Generate round robin all-vs-all matches with letter IDs."""
        if self.participant_count < 2:
            raise ValueError("Round robin requires at least 2 participants")

        self.seed_participants()

        n = self.participant_count
        total_rounds = n - 1 if n % 2 == 0 else n

        bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='main',
            name='Round Robin',
            total_rounds=total_rounds,
            current_round=1,
        )

        for i, p1 in enumerate(self.participants):
            for j, p2 in enumerate(self.participants[i + 1:], start=i + 1):
                round_num = (i + j) % total_rounds + 1
                letter = self._next_match_letter(bracket, round_num)

                Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_num,
                    match_number=Match.objects.filter(
                        bracket=bracket, round_number=round_num
                    ).count() + 1,
                    match_letter=letter,
                    participant1=p1,
                    participant2=p2,
                    status='ready',
                )

        return bracket

    def calculate_standings(self, bracket) -> List[Participant]:
        """
        Calculate standings for Round Robin or Swiss.
        Priority chain: Set Wins → Head-to-Head → Game Differential → Set Win %.
        Returns participants sorted by standing.
        """
        participants = list(
            self.tournament.participants.filter(
                Q(matches_as_p1__bracket=bracket) | Q(matches_as_p2__bracket=bracket)
            ).distinct()
        )

        # Get all completed matches for this bracket
        matches = Match.objects.filter(
            bracket=bracket,
            status='completed',
        ).exclude(
            Q(participant1__isnull=True) | Q(participant2__isnull=True)
        )

        # Build head-to-head lookup: { (p1_id, p2_id): winner_id }
        h2h = {}
        for m in matches:
            key = (m.participant1_id, m.participant2_id)
            rev_key = (m.participant2_id, m.participant1_id)
            h2h[key] = m.winner_id
            h2h[rev_key] = m.winner_id

        def sort_key(p):
            total_matches = p.matches_won + p.matches_lost
            game_diff = (p.games_won - p.games_lost)
            set_win_pct = (p.matches_won / total_matches) if total_matches > 0 else 0
            return (p.matches_won, game_diff, set_win_pct)

        # Sort by primary criteria
        participants.sort(key=sort_key, reverse=True)

        # Resolve ties by head-to-head (bubble sort by H2H within tied groups)
        i = 0
        while i < len(participants):
            j = i
            while j < len(participants) - 1 and sort_key(participants[j]) == sort_key(participants[j + 1]):
                j += 1
            if j > i:
                # Tied group from i to j
                for a in range(i, j):
                    for b in range(a + 1, j + 1):
                        p_a = participants[a]
                        p_b = participants[b]
                        key = (p_a.id, p_b.id)
                        if key in h2h and h2h[key] == p_b.id:
                            participants[a], participants[b] = participants[b], participants[a]
            i = j + 1

        # Assign final placements
        for idx, p in enumerate(participants, start=1):
            p.final_placement = idx
            p.save(update_fields=['final_placement'])

        # Update bracket current_round
        total_rounds = bracket.total_rounds
        completed_rounds = Match.objects.filter(
            bracket=bracket, status='completed'
        ).values_list('round_number', flat=True).distinct().count()
        bracket.current_round = min(completed_rounds + 1, total_rounds)
        if bracket.current_round > total_rounds:
            bracket.completed = True
            bracket.completed_at = timezone.now()
        bracket.save()

        return participants

    # ── Group Stage + Playoffs ──────────────────────────────────────────────

    def generate_group_stage(self):
        """
        Generate group stage with round-robin pools + top-X advancement to
        a double-elimination bracket.

        Pool size: 4-6 players per pool (auto-calculated).
        Top 2 from each pool advance (configurable via tournament settings).
        """
        if self.participant_count < 4:
            raise ValueError("Group stage requires at least 4 participants")

        self.seed_participants()

        # Determine pool count and size
        pool_count = max(2, self.participant_count // 4)
        pool_size = math.ceil(self.participant_count / pool_count)

        # Create pool brackets
        pool_brackets = []
        pool_participants = list(self.participants)

        for pool_num in range(pool_count):
            start = pool_num * pool_size
            end = min(start + pool_size, self.participant_count)
            pool_ps = pool_participants[start:end]
            if len(pool_ps) < 2:
                break

            pool_bracket = Bracket.objects.create(
                tournament=self.tournament,
                bracket_type='groups',
                name=f'Pool {self.MATCH_LETTERS[pool_num]}',
                total_rounds=len(pool_ps) - 1 if len(pool_ps) % 2 == 0 else len(pool_ps),
            )

            # Generate round-robin within pool
            n = len(pool_ps)
            pool_rounds = n - 1 if n % 2 == 0 else n
            for i, p1 in enumerate(pool_ps):
                for j, p2 in enumerate(pool_ps[i + 1:], start=i + 1):
                    round_num = (i + j) % pool_rounds + 1
                    Match.objects.create(
                        tournament=self.tournament,
                        bracket=pool_bracket,
                        round_number=round_num,
                        match_number=Match.objects.filter(
                            bracket=pool_bracket, round_number=round_num
                        ).count() + 1,
                        match_letter=self._next_match_letter(pool_bracket, round_num),
                        participant1=p1,
                        participant2=p2,
                        status='ready',
                    )

            pool_brackets.append(pool_bracket)

        if not pool_brackets:
            raise ValueError("Could not create any pools")

        # Return pool brackets; the advancement to playoffs happens after pools complete
        return pool_brackets

    def advance_from_pools(self, pool_brackets, advance_count=2):
        """
        Advance top N participants from each pool into a double-elimination
        playoffs bracket. Must be called after all pool matches are completed.
        """
        advancing = []
        seed = 1

        for pool_bracket in pool_brackets:
            standings = self.calculate_standings(pool_bracket)
            top = standings[:advance_count]
            for p in top:
                p.seed = seed
                p.save(update_fields=['seed'])
                advancing.append(p)
                seed += 1

        if len(advancing) < 2:
            raise ValueError("Not enough advancing participants for playoffs bracket")

        # Temporarily replace self.participants with advancing participants
        original_participants = self.participants
        self.participants = advancing
        self.participant_count = len(advancing)

        playoffs_bracket_type = 'double_elim'
        if 'playoffs_format' in self.tournament.__dict__:
            playoffs_bracket_type = getattr(self.tournament, 'playoffs_format', 'double_elim')

        if playoffs_bracket_type == 'double_elim':
            result = self.generate_double_elimination()
        else:
            result = (self.generate_single_elimination(),)

        self.participants = original_participants
        self.participant_count = len(original_participants)

        return result

    def advance_from_standings(self, source_bracket, advance_count=8):
        """
        Advance top N participants from a completed Swiss/RR bracket into
        a single-elimination playoffs bracket.
        """
        standings = self.calculate_standings(source_bracket)
        advancing = standings[:advance_count]

        if len(advancing) < 2:
            raise ValueError(
                "Not enough advancing participants for playoffs bracket "
                f"(need 2+, got {len(advancing)})"
            )

        seed = 1
        for p in advancing:
            p.seed = seed
            p.save(update_fields=['seed'])
            seed += 1

        original_participants = self.participants
        self.participants = advancing
        self.participant_count = len(advancing)

        result = self.generate_single_elimination()

        self.participants = original_participants
        self.participant_count = len(original_participants)

        return result