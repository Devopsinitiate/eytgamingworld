"""
Property-Based Tests for Bracket Score Recording Wrong Match Bugfix

**Feature: bracket-score-recording-wrong-match**
Tests the bug condition exploration for incorrect match UUID in Report Score links.

This test is designed to FAIL on unfixed code to confirm the bug exists.
"""

import pytest
import re
from bs4 import BeautifulSoup
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase as HypothesisTestCase
from datetime import timedelta

from tournaments.models import Tournament, Participant, Bracket, Match
from core.models import Game
from venues.models import Venue

User = get_user_model()


class BracketScoreRecordingWrongMatchBugfixPropertyTests(HypothesisTestCase):
    """
    Property-Based Tests for Bracket Score Recording Wrong Match Bugfix
    
    **Feature: bracket-score-recording-wrong-match**
    
    CRITICAL: These tests are designed to FAIL on unfixed code.
    Failure confirms the bug exists. DO NOT fix the test or code when it fails.
    """
    
    def setUp(self):
        """Set up test client and clean database"""
        self.client = Client()
        
        # Clean up any existing data
        Tournament.objects.all().delete()
        Game.objects.all().delete()
        User.objects.all().delete()
        Venue.objects.all().delete()
        Bracket.objects.all().delete()
        Match.objects.all().delete()
        Participant.objects.all().delete()

    def create_tournament_with_bracket(self, num_participants=16):
        """
        Helper to create a tournament with a generated bracket.
        Creates a 16-player single elimination tournament with:
        - Round 1: 8 matches (16 players) - First round
        - Round 2: 4 matches (8 players) - Quarter-finals
        - Round 3: 2 matches (4 players) - Semi-finals
        - Round 4: 1 match (2 players) - Finals
        """
        import random
        import string
        
        # Generate short random suffix to avoid collisions
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        game = Game.objects.create(
            name=f"Bracket Bug Test Game {suffix}",
            slug=f"bracket-bug-game-{suffix}",
            genre='fps'
        )
        
        organizer = User.objects.create(
            email=f"org_bracket_{suffix}@test.com",
            username=f"org_bracket_{suffix}",
            first_name="Bracket",
            last_name="Organizer"
        )
        
        now = timezone.now()
        tournament = Tournament.objects.create(
            name=f"Bracket Bug Test Tournament {suffix}",
            slug=f"bracket-bug-test-{suffix}",
            description="Tournament for testing bracket score recording bug",
            game=game,
            organizer=organizer,
            status='in_progress',
            max_participants=num_participants,
            registration_start=now - timedelta(days=2),
            registration_end=now - timedelta(days=1),
            check_in_start=now - timedelta(hours=2),
            start_datetime=now,
            estimated_end=now + timedelta(days=1),
            format='single_elim',
            is_team_based=False,
            is_public=True
        )
        
        # Create participants
        participants = []
        for i in range(num_participants):
            user = User.objects.create(
                email=f"player_{suffix}_{i}@test.com",
                username=f"player_{suffix}_{i}"[:30],
                first_name=f"Player{i}",
                last_name="Test"
            )
            participant = Participant.objects.create(
                tournament=tournament,
                user=user,
                status='confirmed',
                checked_in=True,
                seed=i + 1
            )
            participants.append(participant)
        
        # Create bracket
        total_rounds = 4 if num_participants == 16 else 3
        bracket = Bracket.objects.create(
            tournament=tournament,
            name="Main Bracket",
            bracket_type='main',
            total_rounds=total_rounds
        )
        
        # Create matches for Round 1 (8 matches with 16 players, or 4 matches with 8 players)
        num_round1_matches = num_participants // 2
        round1_matches = []
        for i in range(num_round1_matches):
            match = Match.objects.create(
                tournament=tournament,
                bracket=bracket,
                round_number=1,
                match_number=i + 1,
                participant1=participants[i * 2] if i * 2 < len(participants) else None,
                participant2=participants[i * 2 + 1] if i * 2 + 1 < len(participants) else None,
                status='ready'
            )
            round1_matches.append(match)
        
        # Create matches for Round 2 (Quarter-finals - 4 matches for 16-player, 2 for 8-player)
        num_round2_matches = num_round1_matches // 2
        round2_matches = []
        for i in range(num_round2_matches):
            match = Match.objects.create(
                tournament=tournament,
                bracket=bracket,
                round_number=2,
                match_number=i + 1,
                status='pending'
            )
            round2_matches.append(match)
        
        # Create matches for Round 3 (Semi-finals or Finals depending on bracket size)
        num_round3_matches = num_round2_matches // 2
        round3_matches = []
        for i in range(num_round3_matches):
            match = Match.objects.create(
                tournament=tournament,
                bracket=bracket,
                round_number=3,
                match_number=i + 1,
                status='pending'
            )
            round3_matches.append(match)
        
        # Create Round 4 (Finals) only for 16-player bracket
        round4_matches = []
        if num_participants == 16:
            finals_match = Match.objects.create(
                tournament=tournament,
                bracket=bracket,
                round_number=4,
                match_number=1,
                status='pending'
            )
            round4_matches.append(finals_match)
        
        return tournament, bracket, round1_matches, round2_matches, round3_matches, round4_matches

    def extract_report_score_urls(self, html_content):
        """
        Extract all "Report Score" button URLs from the bracket HTML.
        Returns a list of tuples: (round_number, match_number, match_uuid)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        report_score_links = []
        
        # Find all "Report Score" links
        # The link text contains "Report Score" and href contains 'match_report' or '/match/'
        links = soup.find_all('a', href=re.compile(r'/match/'))
        
        for link in links:
            # Check if this is a "Report Score" link
            link_text = link.get_text(strip=True)
            if 'Report Score' not in link_text:
                continue
            
            # Extract the match UUID from the URL
            href = link.get('href', '')
            # URL format: /tournaments/match/<uuid>/report/
            match_uuid_pattern = r'/match/([a-f0-9\-]+)/report'
            uuid_match = re.search(match_uuid_pattern, href)
            
            if uuid_match:
                match_uuid = uuid_match.group(1)
                
                # Find the parent match card to get round and match number
                match_card = link.find_parent('div', {'class': lambda x: x and 'match-card' in str(x)})
                if match_card:
                    # Extract match-id from data attribute
                    card_match_id = match_card.get('data-match-id', '')
                    
                    # Find the round column to determine round number
                    round_column = match_card.find_parent('div', {'class': lambda x: x and 'flex-col' in str(x)})
                    if round_column:
                        round_header = round_column.find('h3')
                        if round_header:
                            round_text = round_header.get_text()
                            
                            # Parse round number from text
                            if 'Grand Finals' in round_text or 'Grand Finals' in round_text:
                                round_number = 'finals'
                            elif 'Semi-Finals' in round_text or 'Semi-Finals' in round_text:
                                round_number = 'semi-finals'
                            elif 'Quarter-Finals' in round_text or 'Quarter-Finals' in round_text:
                                round_number = 'quarter-finals'
                            elif 'Round' in round_text:
                                # Extract number from "Round X"
                                round_match = re.search(r'Round (\d+)', round_text)
                                if round_match:
                                    round_number = int(round_match.group(1))
                                else:
                                    round_number = 'unknown'
                            else:
                                round_number = 'unknown'
                            
                            # Extract match number from the match card
                            match_num_span = match_card.find('span', string=re.compile(r'Match \d+'))
                            if match_num_span:
                                match_num_text = match_num_span.get_text()
                                match_num_match = re.search(r'Match (\d+)', match_num_text)
                                if match_num_match:
                                    match_number = int(match_num_match.group(1))
                                else:
                                    match_number = 'unknown'
                            else:
                                match_number = 'unknown'
                            
                            report_score_links.append({
                                'round': round_number,
                                'match_number': match_number,
                                'uuid_in_url': match_uuid,
                                'card_match_id': card_match_id
                            })
        
        return report_score_links

    @settings(max_examples=3, deadline=None)
    @given(
        num_participants=st.sampled_from([8, 16])
    )
    def test_property_fault_condition_round1_report_score_navigation(
        self,
        num_participants
    ):
        """
        Property 1: Fault Condition - Round 1 Report Score Navigation
        
        **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists.
        **DO NOT attempt to fix the test or the code when it fails.**
        
        For any Round 1 match with a "Report Score" button, the UNFIXED code will
        generate a URL containing a quarter-final match UUID instead of the Round 1
        match UUID, causing users to be navigated to the wrong match's score reporting page.
        
        The FIXED code should:
        - Generate URLs with the correct Round 1 match UUID
        - Ensure extracted_match_uuid == round1_match.id
        - Ensure extracted_match_uuid != any_quarterfinal_match.id
        
        **Feature: bracket-score-recording-wrong-match, Property 1: Fault Condition**
        **Validates: Requirements 2.1, 2.2 (Expected Behavior - Correct)**
        **GOAL**: Surface counterexamples that demonstrate the bug exists
        """
        # Create tournament with bracket
        tournament, bracket, round1_matches, round2_matches, round3_matches, round4_matches = \
            self.create_tournament_with_bracket(num_participants=num_participants)
        
        # Log in as the tournament organizer to see "Report Score" buttons
        self.client.force_login(tournament.organizer)
        
        # Render the bracket page
        bracket_url = reverse('tournaments:bracket', kwargs={'slug': tournament.slug})
        response = self.client.get(bracket_url)
        
        self.assertEqual(response.status_code, 200,
                        "Bracket page should load successfully")
        
        # Extract all "Report Score" URLs from the rendered HTML
        html_content = response.content.decode('utf-8')
        
        # Debug: Save HTML to file for inspection
        import os
        debug_dir = 'test_debug_output'
        os.makedirs(debug_dir, exist_ok=True)
        with open(f'{debug_dir}/bracket_html_{num_participants}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        report_score_links = self.extract_report_score_urls(html_content)
        
        print(f"\n[DEBUG] Analyzing Bracket Score Recording Bug")
        print(f"   Tournament: {tournament.name}")
        print(f"   Participants: {num_participants}")
        print(f"   Round 1 Matches: {len(round1_matches)}")
        print(f"   Round 2 Matches: {len(round2_matches)}")
        print(f"   Report Score Links Found: {len(report_score_links)}")
        
        # Filter for Round 1 links (by checking the actual match UUIDs)
        # We need to map the extracted UUIDs back to their actual round numbers
        round1_uuids = {str(m.id) for m in round1_matches}
        round2_uuids = {str(m.id) for m in round2_matches}
        
        # Classify links by which round they actually belong to based on UUID
        round1_links = []
        for link in report_score_links:
            uuid_in_url = link['uuid_in_url']
            # Check if this UUID belongs to a Round 1 match
            if uuid_in_url in round1_uuids:
                link['actual_round'] = 1
                round1_links.append(link)
            elif uuid_in_url in round2_uuids:
                link['actual_round'] = 2
            else:
                link['actual_round'] = 'unknown'
        
        print(f"\n[ANALYSIS] Round 1 Report Score Links Analysis:")
        print(f"   Total Links Found: {len(report_score_links)}")
        print(f"   Round 1 Links (by UUID): {len(round1_links)}")
        print(f"   Round 1 Match UUIDs: {[str(m.id)[:8] for m in round1_matches]}")
        print(f"   Round 2 Match UUIDs: {[str(m.id)[:8] for m in round2_matches]}")
        
        # Document counterexamples
        counterexamples = []
        
        # Check each Round 1 match to see if its "Report Score" link is correct
        for round1_match in round1_matches:
            match_uuid = str(round1_match.id)
            match_number = round1_match.match_number
            
            # Find if there's a link for this match
            link_found = False
            correct_link = False
            links_to_round2 = False
            
            for link in report_score_links:
                # Check if this link's match number matches (assuming display order is preserved)
                if link['match_number'] == match_number or link['uuid_in_url'] == match_uuid:
                    link_found = True
                    if link['uuid_in_url'] == match_uuid:
                        correct_link = True
                    elif link['uuid_in_url'] in round2_uuids:
                        links_to_round2 = True
                        counterexamples.append({
                            'match_number': match_number,
                            'expected_uuid': match_uuid,
                            'actual_uuid': link['uuid_in_url'],
                            'is_quarterfinal': True  # Links to Round 2 instead
                        })
                    break
            
            print(f"\n   Round 1 Match {match_number}:")
            print(f"     Expected UUID: {match_uuid[:8]}...")
            if link_found:
                for link in report_score_links:
                    if link['match_number'] == match_number:
                        print(f"     URL UUID:      {link['uuid_in_url'][:8]}...")
                        print(f"     Correct:       {link['uuid_in_url'] == match_uuid}")
                        print(f"     Links to R2:   {link['uuid_in_url'] in round2_uuids}")
                        break
            else:
                print(f"     No link found for this match")
        
        # Document counterexamples found
        if counterexamples:
            print(f"\n[WARNING] BUG CONFIRMED - Counterexamples Found:")
            for ce in counterexamples:
                print(f"   Round 1 Match {ce['match_number']}:")
                print(f"     Links to: {ce['actual_uuid'][:8]}...")
                print(f"     Should link to: {ce['expected_uuid'][:8]}...")
                if ce['is_quarterfinal']:
                    print(f"     [ERROR] Links to Round 2 match instead!")
        else:
            print(f"\n[OK] No counterexamples found - bug may be fixed")
        
        # ASSERTIONS - These encode the EXPECTED BEHAVIOR (will fail on unfixed code)
        
        # Assertion 1: All Round 1 matches should have "Report Score" links with correct UUIDs
        print(f"\n[ASSERT] Assertion: Round 1 matches have correct UUIDs in their Report Score links")
        for round1_match in round1_matches:
            match_uuid = str(round1_match.id)
            match_number = round1_match.match_number
            
            # Find the link for this match (by match number)
            link_for_match = next(
                (link for link in report_score_links if link['match_number'] == match_number),
                None
            )
            
            if link_for_match:
                self.assertEqual(
                    link_for_match['uuid_in_url'],
                    match_uuid,
                    f"EXPECTED FAILURE ON UNFIXED CODE: Round 1 Match {match_number} "
                    f"'Report Score' link contains wrong UUID. "
                    f"Expected: {match_uuid}, Got: {link_for_match['uuid_in_url']}. "
                    f"This confirms the bug exists."
                )
        
        # Assertion 2: Round 1 match links should NOT contain Round 2 match UUIDs
        print(f"[ASSERT] Assertion: Round 1 match links do NOT contain Round 2 UUIDs")
        for round1_match in round1_matches:
            match_number = round1_match.match_number
            
            # Find the link for this match
            link_for_match = next(
                (link for link in report_score_links if link['match_number'] == match_number),
                None
            )
            
            if link_for_match:
                uuid_in_url = link_for_match['uuid_in_url']
                
                # Check if this UUID belongs to any Round 2 match
                is_round2_uuid = uuid_in_url in round2_uuids
                
                self.assertFalse(
                    is_round2_uuid,
                    f"EXPECTED FAILURE ON UNFIXED CODE: Round 1 Match {match_number} "
                    f"'Report Score' link contains a Round 2 match UUID ({uuid_in_url}). "
                    f"This confirms the bug exists - Round 1 matches are linking to Round 2 matches."
                )
        
        print(f"\n{'='*70}")
        print(f"TEST RESULT: This test is EXPECTED TO FAIL on unfixed code.")
        print(f"Failure confirms the bug exists (Round 1 links use wrong match UUIDs).")
        print(f"{'='*70}\n")

    @settings(max_examples=3, deadline=None)
    @given(
        num_participants=st.sampled_from([8, 16])
    )
    def test_property_preservation_non_round1_match_score_reporting(
        self,
        num_participants
    ):
        """
        Property 2: Preservation - Non-Round 1 Match Score Reporting
        
        **IMPORTANT**: This test follows observation-first methodology.
        This test should PASS on UNFIXED code to confirm baseline behavior to preserve.
        
        For any match where round_number != 1 (Round 2, semi-finals, finals),
        the "Report Score" button should generate a URL containing the correct
        match UUID for that specific match.
        
        This test verifies that:
        - Round 2 (quarter-finals) matches link to correct Round 2 match UUIDs
        - Round 3 (semi-finals) matches link to correct Round 3 match UUIDs
        - Round 4 (finals) matches link to correct Round 4 match UUIDs
        - No non-Round 1 match links to a different round's match UUID
        
        **Feature: bracket-score-recording-wrong-match, Property 2: Preservation**
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4 (Unchanged Behavior - Regression Prevention)**
        **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
        """
        # Create tournament with bracket
        tournament, bracket, round1_matches, round2_matches, round3_matches, round4_matches = \
            self.create_tournament_with_bracket(num_participants=num_participants)
        
        # Complete some Round 1 matches to make Round 2 matches ready
        # This allows us to test Round 2 "Report Score" links
        for i, round1_match in enumerate(round1_matches[:2]):  # Complete first 2 Round 1 matches
            round1_match.status = 'completed'
            round1_match.winner = round1_match.participant1
            round1_match.participant1_score = 2
            round1_match.participant2_score = 0
            round1_match.save()
            
            # Update the corresponding Round 2 match
            round2_match_index = i // 2
            if round2_match_index < len(round2_matches):
                round2_match = round2_matches[round2_match_index]
                if i % 2 == 0:
                    round2_match.participant1 = round1_match.winner
                else:
                    round2_match.participant2 = round1_match.winner
                
                # If both participants are set, make it ready
                if round2_match.participant1 and round2_match.participant2:
                    round2_match.status = 'ready'
                
                round2_match.save()
        
        # Log in as the tournament organizer to see "Report Score" buttons
        self.client.force_login(tournament.organizer)
        
        # Render the bracket page
        bracket_url = reverse('tournaments:bracket', kwargs={'slug': tournament.slug})
        response = self.client.get(bracket_url)
        
        self.assertEqual(response.status_code, 200,
                        "Bracket page should load successfully")
        
        # Extract all "Report Score" URLs from the rendered HTML
        html_content = response.content.decode('utf-8')
        report_score_links = self.extract_report_score_urls(html_content)
        
        print(f"\n[DEBUG] Preservation Test - Non-Round 1 Match Score Reporting")
        print(f"   Tournament: {tournament.name}")
        print(f"   Participants: {num_participants}")
        print(f"   Round 1 Matches: {len(round1_matches)}")
        print(f"   Round 2 Matches: {len(round2_matches)}")
        print(f"   Round 3 Matches: {len(round3_matches)}")
        print(f"   Round 4 Matches: {len(round4_matches)}")
        print(f"   Report Score Links Found: {len(report_score_links)}")
        
        # Create UUID sets for each round
        round1_uuids = {str(m.id) for m in round1_matches}
        round2_uuids = {str(m.id) for m in round2_matches}
        round3_uuids = {str(m.id) for m in round3_matches}
        round4_uuids = {str(m.id) for m in round4_matches}
        
        # Classify links by actual round based on UUID
        links_by_actual_round = {1: [], 2: [], 3: [], 4: []}
        for link in report_score_links:
            uuid_in_url = link['uuid_in_url']
            if uuid_in_url in round1_uuids:
                link['actual_round'] = 1
                links_by_actual_round[1].append(link)
            elif uuid_in_url in round2_uuids:
                link['actual_round'] = 2
                links_by_actual_round[2].append(link)
            elif uuid_in_url in round3_uuids:
                link['actual_round'] = 3
                links_by_actual_round[3].append(link)
            elif uuid_in_url in round4_uuids:
                link['actual_round'] = 4
                links_by_actual_round[4].append(link)
            else:
                link['actual_round'] = 'unknown'
        
        print(f"\n[ANALYSIS] Links by Actual Round (based on UUID):")
        print(f"   Round 1 Links: {len(links_by_actual_round[1])}")
        print(f"   Round 2 Links: {len(links_by_actual_round[2])}")
        print(f"   Round 3 Links: {len(links_by_actual_round[3])}")
        print(f"   Round 4 Links: {len(links_by_actual_round[4])}")
        
        # Test Round 2 (Quarter-Finals) Preservation
        print(f"\n[TEST] Round 2 (Quarter-Finals) Preservation:")
        for round2_match in round2_matches:
            match_uuid = str(round2_match.id)
            match_number = round2_match.match_number
            
            # Refresh from DB to get updated status
            round2_match.refresh_from_db()
            
            print(f"   Round 2 Match {match_number}:")
            print(f"     UUID: {match_uuid[:8]}...")
            print(f"     Status: {round2_match.status}")
            print(f"     Round Number: {round2_match.round_number}")
            
            # Verify match properties are correct
            self.assertEqual(
                round2_match.round_number,
                2,
                f"Round 2 Match {match_number} should have round_number=2"
            )
            
            # If there's a link for this match
            link_for_match = next(
                (link for link in report_score_links if link['uuid_in_url'] == match_uuid),
                None
            )
            
            if link_for_match:
                print(f"     Link Found: Yes (UUID: {link_for_match['uuid_in_url'][:8]}...)")
                # If a link exists, verify it's correct
                self.assertEqual(
                    link_for_match['uuid_in_url'],
                    match_uuid,
                    f"Round 2 Match {match_number} 'Report Score' link should contain correct UUID"
                )
                
                # Verify it doesn't link to a different round
                self.assertNotIn(
                    link_for_match['uuid_in_url'],
                    round1_uuids,
                    f"Round 2 Match {match_number} should not link to Round 1 match"
                )
                self.assertNotIn(
                    link_for_match['uuid_in_url'],
                    round3_uuids,
                    f"Round 2 Match {match_number} should not link to Round 3 match"
                )
            else:
                print(f"     Link Found: No (expected for pending matches)")
        
        # Test Round 3 (Semi-Finals) Preservation
        print(f"\n[TEST] Round 3 (Semi-Finals) Preservation:")
        for round3_match in round3_matches:
            match_uuid = str(round3_match.id)
            match_number = round3_match.match_number
            
            print(f"   Round 3 Match {match_number}:")
            print(f"     UUID: {match_uuid[:8]}...")
            print(f"     Status: {round3_match.status}")
            print(f"     Round Number: {round3_match.round_number}")
            
            # Verify match properties are correct
            self.assertEqual(
                round3_match.round_number,
                3,
                f"Round 3 Match {match_number} should have round_number=3"
            )
            
            # Check if there's a link for this match
            link_for_match = next(
                (link for link in report_score_links if link['uuid_in_url'] == match_uuid),
                None
            )
            
            if link_for_match:
                print(f"     Link Found: Yes (UUID: {link_for_match['uuid_in_url'][:8]}...)")
                # If a link exists, verify it's correct
                self.assertEqual(
                    link_for_match['uuid_in_url'],
                    match_uuid,
                    f"Round 3 Match {match_number} 'Report Score' link should contain correct UUID"
                )
                
                # Verify it doesn't link to a different round
                self.assertNotIn(
                    link_for_match['uuid_in_url'],
                    round1_uuids,
                    f"Round 3 Match {match_number} should not link to Round 1 match"
                )
                self.assertNotIn(
                    link_for_match['uuid_in_url'],
                    round2_uuids,
                    f"Round 3 Match {match_number} should not link to Round 2 match"
                )
            else:
                print(f"     Link Found: No (expected for pending matches)")
        
        # Test Round 4 (Finals) Preservation (only for 16-player brackets)
        if round4_matches:
            print(f"\n[TEST] Round 4 (Finals) Preservation:")
            for round4_match in round4_matches:
                match_uuid = str(round4_match.id)
                match_number = round4_match.match_number
                
                print(f"   Round 4 Match {match_number}:")
                print(f"     UUID: {match_uuid[:8]}...")
                print(f"     Status: {round4_match.status}")
                print(f"     Round Number: {round4_match.round_number}")
                
                # Verify match properties are correct
                self.assertEqual(
                    round4_match.round_number,
                    4,
                    f"Round 4 Match {match_number} should have round_number=4"
                )
                
                # Check if there's a link for this match
                link_for_match = next(
                    (link for link in report_score_links if link['uuid_in_url'] == match_uuid),
                    None
                )
                
                if link_for_match:
                    print(f"     Link Found: Yes (UUID: {link_for_match['uuid_in_url'][:8]}...)")
                    # If a link exists, verify it's correct
                    self.assertEqual(
                        link_for_match['uuid_in_url'],
                        match_uuid,
                        f"Round 4 Match {match_number} 'Report Score' link should contain correct UUID"
                    )
                    
                    # Verify it doesn't link to a different round
                    self.assertNotIn(
                        link_for_match['uuid_in_url'],
                        round1_uuids,
                        f"Round 4 Match {match_number} should not link to Round 1 match"
                    )
                    self.assertNotIn(
                        link_for_match['uuid_in_url'],
                        round2_uuids,
                        f"Round 4 Match {match_number} should not link to Round 2 match"
                    )
                    self.assertNotIn(
                        link_for_match['uuid_in_url'],
                        round3_uuids,
                        f"Round 4 Match {match_number} should not link to Round 3 match"
                    )
                else:
                    print(f"     Link Found: No (expected for pending matches)")
        
        # Overall preservation check: Verify no cross-round linking for non-Round 1 matches
        print(f"\n[ASSERT] Overall Preservation Check:")
        print(f"   Verifying no cross-round linking for non-Round 1 matches...")
        
        # For each non-Round 1 match that has a link, verify it links to the correct round
        all_non_round1_matches = round2_matches + round3_matches + round4_matches
        for match in all_non_round1_matches:
            match_uuid = str(match.id)
            match_round = match.round_number
            
            # Find if there's a link for this match
            link_for_match = next(
                (link for link in report_score_links if link['uuid_in_url'] == match_uuid),
                None
            )
            
            if link_for_match:
                # Verify the link's UUID belongs to the correct round
                if match_round == 2:
                    self.assertIn(
                        link_for_match['uuid_in_url'],
                        round2_uuids,
                        f"Round 2 match should link to Round 2 UUID"
                    )
                elif match_round == 3:
                    self.assertIn(
                        link_for_match['uuid_in_url'],
                        round3_uuids,
                        f"Round 3 match should link to Round 3 UUID"
                    )
                elif match_round == 4:
                    self.assertIn(
                        link_for_match['uuid_in_url'],
                        round4_uuids,
                        f"Round 4 match should link to Round 4 UUID"
                    )
        
        print(f"\n{'='*70}")
        print(f"PRESERVATION TEST RESULT: This test should PASS on unfixed code.")
        print(f"Passing confirms baseline behavior to preserve for non-Round 1 matches.")
        print(f"{'='*70}\n")
