import random
import math
from typing import List
from ..models import Tournament, Participant, Bracket, Match


class BracketGenerator:
    """Generate tournament brackets based on format"""
    
    def __init__(self, tournament: Tournament, participants: List[Participant]):
        self.tournament = tournament
        self.participants = participants
        self.participant_count = len(participants)
    
    def seed_participants(self):
        """Apply seeding based on tournament settings"""
        if self.tournament.seeding_method == 'random':
            random.shuffle(self.participants)
        elif self.tournament.seeding_method == 'skill':
            # Sort by skill rating (from UserGameProfile)
            self.participants.sort(
                key=lambda p: p.user.game_profiles.filter(
                    game=self.tournament.game
                ).first().skill_rating if p.user else 0,
                reverse=True
            )
        elif self.tournament.seeding_method == 'registration':
            self.participants.sort(key=lambda p: p.registered_at)
        
        # Assign seeds
        for idx, participant in enumerate(self.participants, start=1):
            participant.seed = idx
            participant.save()
    
    def next_power_of_two(self, n: int) -> int:
        """Get next power of 2 for bracket size"""
        if n <= 1:
            return 2  # Minimum bracket size is 2 slots
        return 2 ** math.ceil(math.log2(n))

    def build_seeded_slot_order(self, bracket_size: int) -> list:
        """
        Build the standard FGC/start.gg seeded slot order for a bracket.

        For an 8-slot bracket the slot order is [1, 8, 5, 4, 3, 6, 7, 2],
        ensuring seed 1 and seed 2 can only meet in the Grand Final, and
        top seeds receive byes when the field is not a perfect power of 2.

        The algorithm works recursively:
          - Start with [1, 2]
          - Each expansion doubles the list by interleaving the complement:
            [1, 2] → [1, 4, 3, 2] → [1, 8, 5, 4, 3, 6, 7, 2]
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
    
    def generate_single_elimination(self):
        """
        Generate a single-elimination bracket using standard FGC/start.gg seeding.

        Fixes applied vs the old implementation:
          1. Standard seeded slot placement (seed 1 vs seed N, not seed 1 vs seed 2).
          2. Byes are awarded to the TOP seeds (lowest seed numbers), matching
             Capcom Cup / start.gg behaviour.
          3. Bye winners are automatically advanced into Round 2 immediately after
             generation so the bracket is playable without manual intervention.
          4. A next-round match whose both participants are now known is automatically
             set to 'ready' so players and organisers see the correct status.
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

        # ── Standard seeded slot order (FGC / start.gg) ──────────────────────
        # slot_order[i] is the seed number that belongs in bracket slot i+1.
        # For 8 slots: [1, 8, 5, 4, 3, 6, 7, 2]
        # Byes fill the LAST slots in this order, so top seeds (1, 2, …) get byes.
        slot_order = self.build_seeded_slot_order(bracket_size)

        # Build a seed→participant lookup (seed is 1-based after seed_participants)
        seed_to_participant = {p.seed: p for p in self.participants}

        # ── Round 1 matches ───────────────────────────────────────────────────
        matches_by_round = {1: []}
        round_1_match_count = bracket_size // 2

        for match_num in range(round_1_match_count):
            slot_a = slot_order[match_num * 2]       # e.g. slot 1 → seed 1
            slot_b = slot_order[match_num * 2 + 1]   # e.g. slot 2 → seed 8

            p1 = seed_to_participant.get(slot_a)  # None if this is a bye slot
            p2 = seed_to_participant.get(slot_b)  # None if this is a bye slot

            match = Match.objects.create(
                tournament=self.tournament,
                bracket=bracket,
                round_number=1,
                match_number=match_num + 1,
                participant1=p1,
                participant2=p2,
            )

            # Auto-complete byes immediately
            if p1 is None and p2 is None:
                # Both slots empty — shouldn't happen, but guard anyway
                pass
            elif p1 is None or p2 is None:
                # One participant → bye
                match.status = 'completed'
                match.winner = p1 or p2
                match.score_p1 = 1 if p1 else 0
                match.score_p2 = 1 if p2 else 0
            else:
                match.status = 'ready'

            match.save()
            matches_by_round[1].append(match)

        # ── Subsequent round shells ───────────────────────────────────────────
        for round_num in range(2, total_rounds + 1):
            matches_in_round = bracket_size // (2 ** round_num)
            matches_by_round[round_num] = []
            for match_num in range(matches_in_round):
                match = Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_num,
                    match_number=match_num + 1,
                    is_grand_finals=(round_num == total_rounds),
                )
                matches_by_round[round_num].append(match)

        # ── Link matches (winner path) ────────────────────────────────────────
        for round_num in range(1, total_rounds):
            for idx, match in enumerate(matches_by_round[round_num]):
                next_match = matches_by_round[round_num + 1][idx // 2]
                match.next_match_winner = next_match
                match.save()

        # ── Auto-advance bye winners into Round 2 ────────────────────────────
        # Fix #3: bye matches are already completed but their winner was never
        # placed into the next-round match.  Do it now so Round 2 is populated.
        for match in matches_by_round[1]:
            if match.status == 'completed' and match.winner and match.next_match_winner:
                next_m = match.next_match_winner
                if next_m.participant1 is None:
                    next_m.participant1 = match.winner
                elif next_m.participant2 is None:
                    next_m.participant2 = match.winner
                # Fix #4: mark next match ready if both slots are now filled
                if next_m.participant1 and next_m.participant2:
                    next_m.status = 'ready'
                next_m.save()

        return bracket
    
    def generate_double_elimination(self):
        """Generate double elimination bracket (winners + losers bracket)"""
        # Validate minimum participants
        if self.participant_count < 2:
            raise ValueError("Double elimination requires at least 2 participants")
        
        self.seed_participants()
        
        # Ensure we have at least 2 participants for bracket calculation
        bracket_size = self.next_power_of_two(max(2, self.participant_count))
        winners_rounds = int(math.log2(bracket_size))
        losers_rounds = (winners_rounds - 1) * 2
        
        # Create winners bracket
        winners_bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='main',
            name='Winners Bracket',
            total_rounds=winners_rounds
        )
        
        # Create losers bracket
        losers_bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='losers',
            name='Losers Bracket',
            total_rounds=losers_rounds
        )
        
        # Generate winners bracket (same as single elim)
        winners_matches = self._generate_bracket_rounds(
            winners_bracket, bracket_size, winners_rounds
        )
        
        # Generate losers bracket
        losers_matches = self._generate_losers_bracket(
            losers_bracket, bracket_size, losers_rounds
        )
        
        # Link winners to losers bracket
        self._link_double_elimination(winners_matches, losers_matches)
        
        # Create grand finals
        grand_finals = Match.objects.create(
            tournament=self.tournament,
            bracket=winners_bracket,
            round_number=winners_rounds + 1,
            match_number=1,
            is_grand_finals=True
        )
        
        # Link final matches to grand finals
        winners_matches[winners_rounds][-1].next_match_winner = grand_finals
        losers_matches[losers_rounds][-1].next_match_winner = grand_finals
        
        winners_matches[winners_rounds][-1].save()
        losers_matches[losers_rounds][-1].save()
        
        return winners_bracket, losers_bracket
    
    def _generate_bracket_rounds(self, bracket, bracket_size, total_rounds):
        """
        Helper to generate bracket rounds for double-elimination winners bracket.
        Uses the same standard seeded slot order as generate_single_elimination.
        """
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
                participant1=p1,
                participant2=p2,
            )

            if (p1 is None) != (p2 is None):  # exactly one is None → bye
                match.status = 'completed'
                match.winner = p1 or p2
                match.score_p1 = 1 if p1 else 0
                match.score_p2 = 1 if p2 else 0
            elif p1 and p2:
                match.status = 'ready'

            match.save()
            matches_by_round[1].append(match)

        # Subsequent rounds
        for round_num in range(2, total_rounds + 1):
            matches_in_round = bracket_size // (2 ** round_num)
            matches_by_round[round_num] = []
            for match_num in range(matches_in_round):
                match = Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_num,
                    match_number=match_num + 1,
                )
                matches_by_round[round_num].append(match)

        # Link matches
        for round_num in range(1, total_rounds):
            for idx, match in enumerate(matches_by_round[round_num]):
                match.next_match_winner = matches_by_round[round_num + 1][idx // 2]
                match.save()

        # Auto-advance bye winners into Round 2
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
        """Generate losers bracket structure"""
        matches_by_round = {}
        
        for round_num in range(1, total_rounds + 1):
            # Losers bracket has alternating round sizes
            if round_num % 2 == 1:  # Odd rounds
                matches_in_round = bracket_size // (2 ** ((round_num + 3) // 2))
            else:  # Even rounds
                matches_in_round = bracket_size // (2 ** ((round_num + 2) // 2))
            
            matches_by_round[round_num] = []
            
            for match_num in range(matches_in_round):
                match = Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_num,
                    match_number=match_num + 1
                )
                matches_by_round[round_num].append(match)
        
        # Link losers bracket matches
        for round_num in range(1, total_rounds):
            for idx, match in enumerate(matches_by_round[round_num]):
                if round_num + 1 in matches_by_round:
                    next_idx = idx // 2 if round_num % 2 == 0 else idx
                    if next_idx < len(matches_by_round[round_num + 1]):
                        match.next_match_winner = matches_by_round[round_num + 1][next_idx]
                        match.save()
        
        return matches_by_round
    
    def _link_double_elimination(self, winners_matches, losers_matches):
        """Link winners bracket losers to losers bracket"""
        for round_num in winners_matches:
            if round_num == 1:
                # R1 winners losers go to L1
                for idx, match in enumerate(winners_matches[1]):
                    if idx < len(losers_matches.get(1, [])):
                        match.next_match_loser = losers_matches[1][idx]
                        match.save()
            else:
                # Subsequent rounds feed into losers bracket
                losers_round = (round_num - 1) * 2
                if losers_round in losers_matches:
                    for idx, match in enumerate(winners_matches[round_num]):
                        if idx < len(losers_matches[losers_round]):
                            match.next_match_loser = losers_matches[losers_round][idx]
                            match.save()
    
    def generate_swiss_rounds(self):
        """Generate Swiss system rounds"""
        # Validate minimum participants
        if self.participant_count < 2:
            raise ValueError("Swiss system requires at least 2 participants")
        
        self.seed_participants()
        
        # Swiss system: number of rounds = log2(participants) rounded up
        # Ensure we have at least 2 participants for log calculation
        participant_count_for_calc = max(2, self.participant_count)
        total_rounds = math.ceil(math.log2(participant_count_for_calc)) if participant_count_for_calc > 1 else 1
        
        bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='main',
            name='Swiss Rounds',
            total_rounds=total_rounds
        )
        
        # Generate initial round pairings (top vs bottom)
        self._generate_swiss_round(bracket, 1)
        
        return bracket
    
    def _generate_swiss_round(self, bracket, round_number):
        """Generate pairings for a Swiss round"""
        # Get participants sorted by current score
        participants = sorted(
            self.participants,
            key=lambda p: (p.matches_won, p.games_won),
            reverse=True
        )
        
        # Pair adjacent participants
        matches_created = []
        used_participants = set()
        
        for i in range(0, len(participants) - 1, 2):
            if participants[i] not in used_participants and participants[i + 1] not in used_participants:
                match = Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_number,
                    match_number=len(matches_created) + 1,
                    participant1=participants[i],
                    participant2=participants[i + 1],
                    status='ready'
                )
                matches_created.append(match)
                used_participants.add(participants[i])
                used_participants.add(participants[i + 1])
        
        # Handle odd participant (bye)
        if len(participants) % 2 == 1:
            bye_participant = [p for p in participants if p not in used_participants][0]
            match = Match.objects.create(
                tournament=self.tournament,
                bracket=bracket,
                round_number=round_number,
                match_number=len(matches_created) + 1,
                participant1=bye_participant,
                status='completed',
                winner=bye_participant,
                score_p1=1
            )
            matches_created.append(match)
        
        return matches_created
    
    def generate_round_robin(self):
        """Generate round robin all-vs-all matches"""
        # Validate minimum participants
        if self.participant_count < 2:
            raise ValueError("Round robin requires at least 2 participants")
        
        self.seed_participants()
        
        n = self.participant_count
        total_rounds = n - 1 if n % 2 == 0 else n
        
        bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='main',
            name='Round Robin',
            total_rounds=total_rounds
        )
        
        # Generate all matchups
        for i, p1 in enumerate(self.participants):
            for j, p2 in enumerate(self.participants[i + 1:], start=i + 1):
                round_num = (i + j) % total_rounds + 1
                
                Match.objects.create(
                    tournament=self.tournament,
                    bracket=bracket,
                    round_number=round_num,
                    match_number=Match.objects.filter(
                        bracket=bracket, round_number=round_num
                    ).count() + 1,
                    participant1=p1,
                    participant2=p2,
                    status='ready'
                )
        
        return bracket