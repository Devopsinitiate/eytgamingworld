"""Tests for the integrations app"""
import time
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Game
from tournaments.models import Tournament, Participant, Match

from .models import (
    ExternalProvider, ExternalTournament, ExternalPlayer,
    ExternalMatch, SyncLog,
)
from .services.base import BaseIntegrationService
from .services.bracket_import import build_bracket_from_external_matches, _resolve_participant
from .services.startgg import StartGGService

User = get_user_model()


class IntegrationModelTests(TestCase):
    def setUp(self):
        self.provider = ExternalProvider.objects.create(
            name='test-provider',
            base_url='https://api.test.com',
            api_key='test-key-123',
            rate_limit_per_min=60,
        )

    def test_create_provider(self):
        self.assertEqual(self.provider.name, 'test-provider')
        self.assertTrue(self.provider.is_active)
        self.assertEqual(str(self.provider), 'test-provider')

    def test_create_external_tournament(self):
        et = ExternalTournament.objects.create(
            provider=self.provider,
            external_id='tourney-1',
            title='Test Tournament',
            game='Street Fighter 6',
        )
        self.assertEqual(et.status, 'pending')
        self.assertEqual(str(et), '[test-provider] Test Tournament')
        self.assertEqual(et.raw_data, {})

    def test_external_tournament_unique_per_provider(self):
        ExternalTournament.objects.create(
            provider=self.provider, external_id='t1', title='T1'
        )
        with self.assertRaises(Exception):
            ExternalTournament.objects.create(
                provider=self.provider, external_id='t1', title='T2'
            )

    def test_create_external_player(self):
        user = User.objects.create_user(
            email='player@test.com', password='pass', username='testplayer'
        )
        ep = ExternalPlayer.objects.create(
            provider=self.provider,
            external_id='player-1',
            username='TestPlayer',
            game='Street Fighter 6',
            local_user=user,
        )
        self.assertEqual(str(ep), '[test-provider] TestPlayer')
        self.assertEqual(ep.stats, {})

    def test_create_external_match(self):
        et = ExternalTournament.objects.create(
            provider=self.provider, external_id='t1', title='T1'
        )
        em = ExternalMatch.objects.create(
            provider=self.provider,
            external_id='match-1',
            tournament=et,
            round=1,
            players=['player1', 'player2'],
            scores={'player1': 3, 'player2': 1},
        )
        self.assertEqual(str(em), '[test-provider] Match match-1')
        self.assertEqual(em.raw_data, {})

    def test_create_sync_log(self):
        log = SyncLog.objects.create(
            provider=self.provider,
            sync_type='tournament',
            status='running',
        )
        self.assertEqual(log.status, 'running')
        self.assertIsNone(log.completed_at)
        self.assertIsNotNone(log.started_at)
        self.assertEqual(str(log), 'tournament - test-provider - running')

    def test_sync_log_completion(self):
        log = SyncLog.objects.create(
            provider=self.provider, sync_type='player', status='running'
        )
        log.status = 'completed'
        log.completed_at = timezone.now()
        log.items_processed = 5
        log.save()
        log.refresh_from_db()
        self.assertEqual(log.status, 'completed')
        self.assertEqual(log.items_processed, 5)


class _ConcreteService(BaseIntegrationService):
    """Concrete subclass for testing abstract base."""
    def get_tournament(self, identifier): return {}
    def get_event_standings(self, event_id): return {}
    def get_event_entrants(self, event_id): return {}
    def get_event_sets(self, event_id): return {}


class BaseServiceTests(TestCase):
    def setUp(self):
        self.provider = ExternalProvider.objects.create(
            name='rate-limited',
            base_url='https://api.test.com',
            api_key='key',
            rate_limit_per_min=120,
        )

    def test_rate_limit_enforces_interval(self):
        """Two rapid requests should be spaced by min_interval"""
        service = _ConcreteService(self.provider)
        expected_interval = 60.0 / 120  # 0.5 seconds

        start = time.time()
        service._rate_limit()
        service._rate_limit()
        elapsed = time.time() - start

        self.assertGreaterEqual(elapsed, expected_interval * 0.9)

    def test_min_interval_calculation(self):
        service = _ConcreteService(self.provider)
        expected = 60.0 / 120
        self.assertAlmostEqual(service.min_interval, expected, places=4)

    def test_rate_limit_zero_requests(self):
        """rate_limit_per_min of 0 should not cause division issues"""
        provider = ExternalProvider.objects.create(
            name='zero-rate',
            base_url='https://api.test.com',
            api_key='key',
            rate_limit_per_min=0,
        )
        service = _ConcreteService(provider)
        # Should not raise
        service._rate_limit()

    def test_abstract_methods_raise(self):
        with self.assertRaises(TypeError):
            BaseIntegrationService(self.provider)


class StartGGServiceTests(TestCase):
    def setUp(self):
        self.provider = ExternalProvider.objects.create(
            name='start.gg',
            base_url='https://api.start.gg/gql/alpha',
            api_key='test-token',
            rate_limit_per_min=80,
        )

    @patch('integrations.services.startgg.requests.post')
    def test_get_tournament(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'data': {
                'tournament': {
                    'id': '123',
                    'name': 'Test Tourney',
                    'slug': 'test-tourney',
                    'startAt': 1700000000,
                    'endAt': 1700003600,
                }
            }
        }
        svc = StartGGService(self.provider)
        result = svc.get_tournament('test-tourney')
        self.assertEqual(result['tournament']['name'], 'Test Tourney')
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        self.assertIn('Authorization', call_args['headers'])
        self.assertEqual(call_args['headers']['Authorization'], 'Bearer test-token')

    @patch('integrations.services.startgg.requests.post')
    def test_get_event_sets(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'data': {
                'event': {
                    'sets': {
                        'nodes': [
                            {'id': 'set1', 'round': 1, 'displayScore': '3-1'}
                        ]
                    }
                }
            }
        }
        svc = StartGGService(self.provider)
        result = svc.get_event_sets('event-1')
        self.assertEqual(len(result['event']['sets']['nodes']), 1)

    @patch('integrations.services.startgg.requests.post')
    def test_api_error_raises_exception(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'errors': [{'message': 'Not found'}]
        }
        svc = StartGGService(self.provider)
        with self.assertRaises(Exception) as ctx:
            svc.get_tournament('nonexistent')
        self.assertIn('start.gg API error', str(ctx.exception))

    @patch('integrations.services.startgg.requests.post')
    def test_get_event_standings(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'data': {
                'event': {
                    'standings': {
                        'nodes': [
                            {'placement': 1, 'entrant': {'id': 'e1', 'name': 'Player1'}},
                            {'placement': 2, 'entrant': {'id': 'e2', 'name': 'Player2'}},
                        ]
                    }
                }
            }
        }
        svc = StartGGService(self.provider)
        result = svc.get_event_standings('event-1')
        self.assertEqual(len(result['event']['standings']['nodes']), 2)

    @patch('integrations.services.startgg.requests.post')
    def test_rate_limiting_respected(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'data': {}}
        svc = StartGGService(self.provider)
        start = time.time()
        svc.get_tournament('t1')
        svc.get_tournament('t2')
        elapsed = time.time() - start
        min_interval = 60.0 / 80
        self.assertGreaterEqual(elapsed, min_interval * 0.9)


class BracketImportTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create(
            name='Test Game', slug='test-game', genre='fighting'
        )
        now = timezone.now()
        self.org = User.objects.create_user(
            email='org@test.com', password='pass', username='org'
        )
        self.tournament = Tournament.objects.create(
            name='Import Target', slug='import-target',
            game=self.game, format='double_elim', status='in_progress',
            organizer=self.org, best_of=3,
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=7),
            check_in_start=now - timedelta(hours=1),
            start_datetime=now,
        )
        self.player2_user = User.objects.create_user(
            email='player2@test.com', password='pass', username='Player2'
        )
        self.p1 = Participant.objects.create(
            tournament=self.tournament, user=self.org,
            status='confirmed', checked_in=True,
        )
        self.p2 = Participant.objects.create(
            tournament=self.tournament, user=self.player2_user,
            status='confirmed', checked_in=True,
        )
        self.provider = ExternalProvider.objects.create(
            name='import-provider', base_url='https://api.test.com',
            api_key='key', rate_limit_per_min=60,
        )
        self.et = ExternalTournament.objects.create(
            provider=self.provider, external_id='ext-1',
            title='External Tourney', local_tournament=self.tournament,
        )

    def test_build_bracket_creates_matches(self):
        ExternalMatch.objects.create(
            provider=self.provider, external_id='m1', tournament=self.et,
            round=1, players=['org', 'Player2'],
            scores={'org': 3, 'Player2': 1},
        )
        bracket, count = build_bracket_from_external_matches(self.et)
        self.assertIsNotNone(bracket)
        self.assertEqual(count, 1)
        self.assertEqual(bracket.total_rounds, 1)

    def test_build_bracket_no_local_tournament(self):
        et2 = ExternalTournament.objects.create(
            provider=self.provider, external_id='ext-orphan', title='Orphan'
        )
        bracket, count = build_bracket_from_external_matches(et2)
        self.assertIsNone(bracket)
        self.assertEqual(count, 0)

    def test_build_bracket_no_external_matches(self):
        bracket, count = build_bracket_from_external_matches(self.et)
        self.assertIsNone(bracket)
        self.assertEqual(count, 0)

    def test_build_bracket_dedup(self):
        ExternalMatch.objects.create(
            provider=self.provider, external_id='m1', tournament=self.et,
            round=1, players=['org', 'Player2'],
            scores={'org': 3, 'Player2': 1},
        )
        build_bracket_from_external_matches(self.et, 'DupTest')
        # Second call with same name should be skipped
        bracket, count = build_bracket_from_external_matches(self.et, 'DupTest')
        self.assertIsNone(bracket)
        self.assertEqual(count, 0)

    def test_build_bracket_multiple_rounds(self):
        for i in range(4):
            ExternalMatch.objects.create(
                provider=self.provider, external_id=f'm{i}', tournament=self.et,
                round=(i // 2) + 1,
                players=['org', 'Player2'],
                scores={'org': 3 if i % 2 == 0 else 1, 'Player2': 1 if i % 2 == 0 else 3},
            )
        bracket, count = build_bracket_from_external_matches(self.et, 'MultiRound')
        self.assertIsNotNone(bracket)
        self.assertEqual(count, 4)
        self.assertEqual(bracket.total_rounds, 2)

    def test_resolve_participant_by_username(self):
        result = _resolve_participant(self.tournament, 'org')
        self.assertEqual(result, self.p1)

    def test_resolve_participant_case_insensitive(self):
        result = _resolve_participant(self.tournament, 'ORG')
        self.assertEqual(result, self.p1)

    def test_resolve_participant_not_found(self):
        result = _resolve_participant(self.tournament, 'NonExistent')
        self.assertIsNone(result)

    def test_build_bracket_single_player_match(self):
        """Matches with only 1 player should still create a bracket entry"""
        ExternalMatch.objects.create(
            provider=self.provider, external_id='bye-match', tournament=self.et,
            round=1, players=['org'],
        )
        bracket, count = build_bracket_from_external_matches(self.et, 'ByeTest')
        self.assertIsNotNone(bracket)
        self.assertEqual(count, 1)

    def test_build_bracket_unknown_player(self):
        """Unknown external players should produce None participant slots"""
        ExternalMatch.objects.create(
            provider=self.provider, external_id='unknown-match', tournament=self.et,
            round=1, players=['UnknownPlayer1', 'UnknownPlayer2'],
            scores={'UnknownPlayer1': 2, 'UnknownPlayer2': 0},
        )
        bracket, count = build_bracket_from_external_matches(self.et, 'UnknownTest')
        self.assertIsNotNone(bracket)
        self.assertEqual(count, 1)
        m = Match.objects.filter(bracket=bracket).first()
        self.assertIsNone(m.participant1)
        self.assertIsNone(m.participant2)
