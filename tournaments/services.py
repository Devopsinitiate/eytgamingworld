import random
import math
from typing import List
from .models import Tournament, Participant, Bracket, Match


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
        """Get next power of 2 for bracket size (safe against n <= 1)."""
        if n <= 1:
            return 2
        return 2 ** math.ceil(math.log2(n))

    def build_seeded_slot_order(self, bracket_size: int) -> list:
        """Standard FGC/start.gg seeded slot order. See bracket_generator.py for details."""
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
        """Generate single elimination bracket with correct FGC seeding."""
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
        for match_num in range(bracket_size // 2):
            p1 = seed_to_participant.get(slot_order[match_num * 2])
            p2 = seed_to_participant.get(slot_order[match_num * 2 + 1])

            match = Match.objects.create(
                tournament=self.tournament,
                bracket=bracket,
                round_number=1,
                match_number=match_num + 1,
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
                    is_grand_finals=(round_num == total_rounds),
                )
                matches_by_round[round_num].append(match)

        for round_num in range(1, total_rounds):
            for idx, match in enumerate(matches_by_round[round_num]):
                match.next_match_winner = matches_by_round[round_num + 1][idx // 2]
                match.save()

        # Auto-advance bye winners
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
    
    def generate_double_elimination(self):
        """Generate double elimination bracket (winners + losers bracket)"""
        self.seed_participants()
        
        bracket_size = self.next_power_of_two(self.participant_count)
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
        """Helper to generate bracket rounds"""
        matches_by_round = {}
        
        # Round 1
        round_1_matches = bracket_size // 2
        matches_by_round[1] = []
        
        participant_idx = 0
        for match_num in range(round_1_matches):
            match = Match.objects.create(
                tournament=self.tournament,
                bracket=bracket,
                round_number=1,
                match_number=match_num + 1
            )
            
            if participant_idx < self.participant_count:
                match.participant1 = self.participants[participant_idx]
                participant_idx += 1
            
            if participant_idx < self.participant_count:
                match.participant2 = self.participants[participant_idx]
                participant_idx += 1
            
            if match.is_bye:
                match.status = 'completed'
                match.winner = match.participant1 or match.participant2
            elif match.is_ready:
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
                    match_number=match_num + 1
                )
                matches_by_round[round_num].append(match)
        
        # Link matches
        for round_num in range(1, total_rounds):
            for idx, match in enumerate(matches_by_round[round_num]):
                next_match_idx = idx // 2
                match.next_match_winner = matches_by_round[round_num + 1][next_match_idx]
                match.save()
        
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
        self.seed_participants()
        
        # Swiss system: number of rounds = log2(participants) rounded up
        total_rounds = math.ceil(math.log2(self.participant_count))
        
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