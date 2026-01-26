from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import Game
from .models import Tournament, Participant, Bracket, Match, MatchDispute, Payment, TournamentShare
import json
from unittest.mock import patch
from datetime import timedelta


User = get_user_model()


class ParticipantListViewTests(TestCase):
	def setUp(self):
		# Create a game
		self.game = Game.objects.create(name='Test Game', slug='test-game', genre='other')

		# Organizer user
		self.organizer = User.objects.create_user(
			email='organizer@example.com', password='pass', username='organizer'
		)
		self.organizer.role = 'organizer'
		self.organizer.save()

		# Player user
		self.player = User.objects.create_user(
			email='player@example.com', password='pass', username='player'
		)

		now = timezone.now()
		# Create tournament
		self.tournament = Tournament.objects.create(
			name='Test Tournament',
			slug='test-tournament',
			description='A test tournament',
			game=self.game,
			format='single_elim',
			status='registration',
			organizer=self.organizer,
			registration_start=now - timezone.timedelta(days=1),
			registration_end=now + timezone.timedelta(days=7),
			check_in_start=now + timezone.timedelta(days=8),
			start_datetime=now + timezone.timedelta(days=9),
		)

		# Create a participant
		self.participant = Participant.objects.create(
			tournament=self.tournament,
			user=self.player,
			status='confirmed'
		)

	def test_organizer_can_view_participants_and_see_controls(self):
		# Login as organizer
		logged_in = self.client.login(email='organizer@example.com', password='pass')
		self.assertTrue(logged_in)

		url = reverse('tournaments:participants', kwargs={'slug': self.tournament.slug})
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)

		content = response.content.decode('utf-8')
		# Participant's display name should be present
		self.assertIn(self.participant.display_name, content)
		# Organizer-only actions expected in the template
		self.assertIn('Assign Seed', content)
		self.assertIn('Checked In', content) or True

	def test_organizer_can_assign_seed(self):
		# Login as organizer
		logged_in = self.client.login(email='organizer@example.com', password='pass')
		self.assertTrue(logged_in)

		url = reverse('tournaments:participants', kwargs={'slug': self.tournament.slug})
		post_data = {
			'participant_id': str(self.participant.id),
			'seed': '1',
		}
		response = self.client.post(url, post_data)
		# Expect redirect back to participants page
		self.assertIn(response.status_code, (302, 301))

		# Reload participant and assert seed assigned
		self.participant.refresh_from_db()
		self.assertEqual(self.participant.seed, 1)

	def test_non_organizer_cannot_assign_seed(self):
		# Login as a normal player
		logged_in = self.client.login(email='player@example.com', password='pass')
		self.assertTrue(logged_in)

		url = reverse('tournaments:participants', kwargs={'slug': self.tournament.slug})
		post_data = {
			'participant_id': str(self.participant.id),
			'seed': '2',
		}
		response = self.client.post(url, post_data)
		# Forbidden for non-organizer
		self.assertEqual(response.status_code, 403)

	def test_seed_swap_between_participants(self):
		# Create another participant with a seed
		player_b = User.objects.create_user(email='playerb@example.com', password='pass', username='playerb')
		participant_b = Participant.objects.create(
			tournament=self.tournament,
			user=player_b,
			status='confirmed',
			seed=2
		)

		# Ensure initial seeds
		self.participant.seed = 1
		self.participant.save()
		participant_b.refresh_from_db()
		self.assertEqual(self.participant.seed, 1)
		self.assertEqual(participant_b.seed, 2)

		# Login as organizer and assign seed 2 to participant A (should swap)
		logged_in = self.client.login(email='organizer@example.com', password='pass')
		self.assertTrue(logged_in)

		url = reverse('tournaments:participants', kwargs={'slug': self.tournament.slug})
		post_data = {
			'participant_id': str(self.participant.id),
			'seed': '2',
		}
		response = self.client.post(url, post_data)
		self.assertIn(response.status_code, (302, 301))

		# Reload participants and verify swap
		self.participant.refresh_from_db()
		participant_b.refresh_from_db()
		self.assertEqual(self.participant.seed, 2)
		self.assertEqual(participant_b.seed, 1)


class MatchDisputeViewTests(TestCase):
	def setUp(self):
		# Setup game and users
		self.game = Game.objects.create(name='Test Game', slug='test-game-2', genre='other')
		self.organizer = User.objects.create_user(
			email='org2@example.com', password='pass', username='org2'
		)
		self.organizer.role = 'organizer'
		self.organizer.save()

		self.player1 = User.objects.create_user(email='p1@example.com', password='pass', username='p1')
		self.player2 = User.objects.create_user(email='p2@example.com', password='pass', username='p2')

		now = timezone.now()
		self.tournament = Tournament.objects.create(
			name='Match Test Tournament',
			slug='match-test-tournament',
			description='Tournament for match dispute tests',
			game=self.game,
			format='single_elim',
			status='in_progress',
			organizer=self.organizer,
			registration_start=now - timezone.timedelta(days=10),
			registration_end=now - timezone.timedelta(days=5),
			check_in_start=now - timezone.timedelta(days=4),
			start_datetime=now - timezone.timedelta(days=3),
		)

		# Create participants
		self.p1 = Participant.objects.create(tournament=self.tournament, user=self.player1, status='confirmed')
		self.p2 = Participant.objects.create(tournament=self.tournament, user=self.player2, status='confirmed')

		# Create bracket and match
		self.bracket = Bracket.objects.create(tournament=self.tournament, name='Main')
		self.match = Match.objects.create(
			tournament=self.tournament,
			bracket=self.bracket,
			round_number=1,
			match_number=1,
			participant1=self.p1,
			participant2=self.p2,
			status='completed',
			score_p1=1,
			score_p2=2,
			winner=self.p2
		)

	def test_dispute_get_and_post_creates_dispute(self):
		# Login as player1 (reporter)
		logged_in = self.client.login(email='p1@example.com', password='pass')
		self.assertTrue(logged_in)

		url = reverse('tournaments:match_dispute', kwargs={'pk': self.match.pk})

		# GET the dispute form
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIn('File Match Dispute', response.content.decode('utf-8'))

		# POST a dispute
		post_data = {
			'reason': 'Score was misreported',
		}
		response = self.client.post(url, post_data)

		# After successful post, a redirect to match_detail is expected
		self.assertEqual(response.status_code, 302)

		# Ensure dispute exists
		dispute_qs = MatchDispute.objects.filter(match=self.match, reporter=self.player1)
		self.assertTrue(dispute_qs.exists())


class RegistrationPaymentTests(TestCase):
	def setUp(self):
		self.game = Game.objects.create(name='Pay Game', slug='pay-game', genre='other')
		self.organizer = User.objects.create_user(email='payorg@example.com', password='pass', username='payorg')
		self.organizer.role = 'organizer'
		self.organizer.save()

		self.player = User.objects.create_user(email='payer@example.com', password='pass', username='payer')

		now = timezone.now()
		self.tournament = Tournament.objects.create(
			name='Fee Tournament',
			slug='fee-tournament',
			description='Tournament with fee',
			game=self.game,
			format='single_elim',
			status='registration',
			organizer=self.organizer,
			registration_start=now - timezone.timedelta(days=1),
			registration_end=now + timezone.timedelta(days=7),
			check_in_start=now + timezone.timedelta(days=8),
			start_datetime=now + timezone.timedelta(days=9),
			registration_fee=25.00
		)

	def test_registration_redirects_to_payment_and_marks_paid(self):
		# Login as player and register
		logged_in = self.client.login(email='payer@example.com', password='pass')
		self.assertTrue(logged_in)

		url = reverse('tournaments:register', kwargs={'slug': self.tournament.slug})
		response = self.client.post(url, {'rules_agreement': 'on'})
		# Should redirect to payment page
		self.assertEqual(response.status_code, 302)

		# Find participant created
		participant = Participant.objects.filter(tournament=self.tournament, user=self.player).first()
		self.assertIsNotNone(participant)
		self.assertFalse(participant.has_paid)

		# GET payment page
		pay_url = reverse('tournaments:payment', kwargs={'participant_id': participant.id})
		response = self.client.get(pay_url)
		self.assertEqual(response.status_code, 200)

		# POST to simulate payment
		response = self.client.post(pay_url)
		# Should redirect to tournament detail
		self.assertEqual(response.status_code, 302)

		participant.refresh_from_db()
		self.assertTrue(participant.has_paid)
		self.assertEqual(float(participant.amount_paid), float(self.tournament.registration_fee))


class PaymentWebhookTests(TestCase):
	def setUp(self):
		self.game = Game.objects.create(name='Webhook Game', slug='web-game', genre='other')
		self.organizer = User.objects.create_user(email='weborg@example.com', password='pass', username='weborg')
		self.organizer.role = 'organizer'
		self.organizer.save()

		self.player = User.objects.create_user(email='webpayer@example.com', password='pass', username='webpayer')

		now = timezone.now()
		self.tournament = Tournament.objects.create(
			name='Webhook Tournament',
			slug='webhook-tournament',
			description='Tournament for webhook tests',
			game=self.game,
			format='single_elim',
			status='registration',
			organizer=self.organizer,
			registration_start=now - timezone.timedelta(days=1),
			registration_end=now + timezone.timedelta(days=7),
			check_in_start=now + timezone.timedelta(days=8),
			start_datetime=now + timezone.timedelta(days=9),
			registration_fee=10.00
		)

		self.participant = Participant.objects.create(
			tournament=self.tournament,
			user=self.player,
			status='confirmed'
		)

	def test_paystack_webhook_marks_payment(self):
		payment = Payment.objects.create(
			participant=self.participant,
			amount=self.tournament.registration_fee,
			provider='paystack',
			status='pending'
		)

		payload = {
			'event': 'charge.success',
			'data': {
				'reference': str(payment.id),
			}
		}

		response = self.client.post(reverse('tournaments:paystack_webhook'), data=json.dumps(payload), content_type='application/json')
		self.assertEqual(response.status_code, 200)

		payment.refresh_from_db()
		self.participant.refresh_from_db()
		self.assertEqual(payment.status, 'charged')
		self.assertTrue(self.participant.has_paid)

	def test_stripe_webhook_marks_payment(self):
		payment = Payment.objects.create(
			participant=self.participant,
			amount=self.tournament.registration_fee,
			provider='stripe',
			status='pending'
		)

		# craft fake event
		event = {
			'type': 'checkout.session.completed',
			'data': {
				'object': {
					'client_reference_id': str(payment.id),
					'payment_intent': 'pi_fake_123'
				}
			}
		}

		# Patch the stripe.Webhook.construct_event used in views
		with patch('tournaments.views.stripe.Webhook.construct_event', return_value=event):
			response = self.client.post(reverse('tournaments:stripe_webhook'), data=json.dumps({}), content_type='application/json', HTTP_STRIPE_SIGNATURE='sig')
			self.assertEqual(response.status_code, 200)

		payment.refresh_from_db()
		self.participant.refresh_from_db()
		self.assertEqual(payment.status, 'charged')
		self.assertTrue(self.participant.has_paid)


class TournamentModelEnhancementsTests(TestCase):
	"""Unit tests for tournament model enhancements (Task 18.1)
	
	Tests for:
	- View count increment functionality
	- Share count tracking
	- Timeline phases generation
	- Registration counting methods
	
	Requirements: 2.5, 9.4, 9.5
	"""
	
	def setUp(self):
		"""Set up test data for tournament model enhancement tests"""
		self.game = Game.objects.create(
			name='Test Game',
			slug='test-game-enhancements',
			genre='fps'
		)
		
		self.organizer = User.objects.create_user(
			email='organizer@test.com',
			password='testpass123',
			username='organizer'
		)
		self.organizer.role = 'organizer'
		self.organizer.save()
		
		now = timezone.now()
		self.tournament = Tournament.objects.create(
			name='Enhancement Test Tournament',
			slug='enhancement-test-tournament',
			description='Tournament for testing model enhancements',
			game=self.game,
			format='single_elim',
			status='registration',
			organizer=self.organizer,
			registration_start=now - timedelta(days=2),
			registration_end=now + timedelta(days=5),
			check_in_start=now + timedelta(days=6),
			start_datetime=now + timedelta(days=7),
			estimated_end=now + timedelta(days=8),
			registration_fee=10.00,
			prize_pool=1000.00,
			max_participants=32,
			primary_color='#b91c1c',
			secondary_color='#111827'
		)
	
	def test_view_count_increment(self):
		"""Test that view count can be incremented (Requirement 2.5)"""
		initial_count = self.tournament.view_count
		self.assertEqual(initial_count, 0)
		
		# Increment view count
		self.tournament.view_count += 1
		self.tournament.save()
		
		self.tournament.refresh_from_db()
		self.assertEqual(self.tournament.view_count, 1)
		
		# Increment multiple times
		self.tournament.view_count += 5
		self.tournament.save()
		
		self.tournament.refresh_from_db()
		self.assertEqual(self.tournament.view_count, 6)
	
	def test_share_count_tracking(self):
		"""Test that share count can be tracked (Requirement 9.4, 9.5)"""
		initial_count = self.tournament.share_count
		self.assertEqual(initial_count, 0)
		
		# Increment share count
		self.tournament.share_count += 1
		self.tournament.save()
		
		self.tournament.refresh_from_db()
		self.assertEqual(self.tournament.share_count, 1)
		
		# Increment multiple times
		self.tournament.share_count += 3
		self.tournament.save()
		
		self.tournament.refresh_from_db()
		self.assertEqual(self.tournament.share_count, 4)
	
	def test_tournament_share_model_creation(self):
		"""Test TournamentShare model for tracking social shares (Requirement 9.4, 9.5)"""
		user = User.objects.create_user(
			email='sharer@test.com',
			password='testpass123',
			username='sharer'
		)
		
		# Create a share record
		share = TournamentShare.objects.create(
			tournament=self.tournament,
			platform='twitter',
			shared_by=user,
			ip_address='192.168.1.1',
			user_agent='Mozilla/5.0'
		)
		
		self.assertIsNotNone(share.id)
		self.assertEqual(share.tournament, self.tournament)
		self.assertEqual(share.platform, 'twitter')
		self.assertEqual(share.shared_by, user)
		
		# Test relationship
		self.assertEqual(self.tournament.shares.count(), 1)
		self.assertEqual(self.tournament.shares.first(), share)
	
	def test_tournament_share_platforms(self):
		"""Test different sharing platforms (Requirement 9.4)"""
		platforms = ['twitter', 'discord', 'direct', 'facebook']
		
		for platform in platforms:
			share = TournamentShare.objects.create(
				tournament=self.tournament,
				platform=platform,
				ip_address='192.168.1.1',
				user_agent='Mozilla/5.0'
			)
			self.assertEqual(share.platform, platform)
		
		self.assertEqual(self.tournament.shares.count(), 4)
	
	def test_get_registrations_today(self):
		"""Test get_registrations_today method (Requirement 2.5)"""
		now = timezone.now()
		
		# Create participants registered at different times
		user1 = User.objects.create_user(
			email='user1@test.com',
			password='testpass123',
			username='user1'
		)
		user2 = User.objects.create_user(
			email='user2@test.com',
			password='testpass123',
			username='user2'
		)
		user3 = User.objects.create_user(
			email='user3@test.com',
			password='testpass123',
			username='user3'
		)
		
		# Participant registered today
		p1 = Participant.objects.create(
			tournament=self.tournament,
			user=user1,
			status='confirmed'
		)
		p1.registered_at = now - timedelta(hours=2)
		p1.save()
		
		# Participant registered today
		p2 = Participant.objects.create(
			tournament=self.tournament,
			user=user2,
			status='confirmed'
		)
		p2.registered_at = now - timedelta(hours=12)
		p2.save()
		
		# Participant registered 2 days ago (should not count)
		p3 = Participant.objects.create(
			tournament=self.tournament,
			user=user3,
			status='confirmed'
		)
		p3.registered_at = now - timedelta(days=2)
		p3.save()
		
		# Test the method
		registrations_today = self.tournament.get_registrations_today()
		self.assertEqual(registrations_today, 2)
	
	def test_get_timeline_phases(self):
		"""Test get_timeline_phases method (Requirement 2.5)"""
		phases = self.tournament.get_timeline_phases()
		
		# Should return 3 phases: Registration, Check-in, Tournament
		self.assertEqual(len(phases), 3)
		
		# Check Registration phase
		registration_phase = phases[0]
		self.assertEqual(registration_phase['name'], 'Registration')
		self.assertEqual(registration_phase['start_time'], self.tournament.registration_start)
		self.assertEqual(registration_phase['end_time'], self.tournament.registration_end)
		self.assertEqual(registration_phase['status'], 'active')  # Currently in registration
		self.assertIn('entry fee', registration_phase['description'])
		self.assertEqual(registration_phase['icon'], 'person_add')
		
		# Check Check-in phase
		checkin_phase = phases[1]
		self.assertEqual(checkin_phase['name'], 'Check-in')
		self.assertEqual(checkin_phase['start_time'], self.tournament.check_in_start)
		self.assertEqual(checkin_phase['end_time'], self.tournament.start_datetime)
		self.assertEqual(checkin_phase['status'], 'upcoming')
		self.assertEqual(checkin_phase['description'], 'Confirm participation')
		self.assertEqual(checkin_phase['icon'], 'check_circle')
		
		# Check Tournament phase
		tournament_phase = phases[2]
		self.assertEqual(tournament_phase['name'], 'Tournament')
		self.assertEqual(tournament_phase['start_time'], self.tournament.start_datetime)
		self.assertEqual(tournament_phase['end_time'], self.tournament.estimated_end)
		self.assertEqual(tournament_phase['status'], 'upcoming')
		self.assertIn('format', tournament_phase['description'])
		self.assertEqual(tournament_phase['icon'], 'emoji_events')
	
	def test_timeline_phases_status_transitions(self):
		"""Test timeline phase status changes based on tournament state"""
		now = timezone.now()
		
		# Test completed registration phase
		past_tournament = Tournament.objects.create(
			name='Past Tournament',
			slug='past-tournament',
			description='Tournament with past registration',
			game=self.game,
			format='single_elim',
			status='check_in',
			organizer=self.organizer,
			registration_start=now - timedelta(days=10),
			registration_end=now - timedelta(days=3),
			check_in_start=now - timedelta(hours=2),
			start_datetime=now + timedelta(hours=2),
			estimated_end=now + timedelta(days=1)
		)
		
		phases = past_tournament.get_timeline_phases()
		
		# Registration should be completed
		self.assertEqual(phases[0]['status'], 'completed')
		
		# Check-in should be active
		self.assertEqual(phases[1]['status'], 'active')
		
		# Tournament should be upcoming
		self.assertEqual(phases[2]['status'], 'upcoming')
	
	def test_primary_and_secondary_colors(self):
		"""Test that primary and secondary colors are stored correctly"""
		self.assertEqual(self.tournament.primary_color, '#b91c1c')
		self.assertEqual(self.tournament.secondary_color, '#111827')
		
		# Test updating colors
		self.tournament.primary_color = '#3b82f6'
		self.tournament.secondary_color = '#1e40af'
		self.tournament.save()
		
		self.tournament.refresh_from_db()
		self.assertEqual(self.tournament.primary_color, '#3b82f6')
		self.assertEqual(self.tournament.secondary_color, '#1e40af')
	
	def test_share_count_with_tournament_share_records(self):
		"""Test that share_count can be synchronized with TournamentShare records"""
		# Create multiple share records
		for i in range(5):
			TournamentShare.objects.create(
				tournament=self.tournament,
				platform='twitter',
				ip_address=f'192.168.1.{i}',
				user_agent='Mozilla/5.0'
			)
		
		# Manually update share_count to match
		self.tournament.share_count = self.tournament.shares.count()
		self.tournament.save()
		
		self.assertEqual(self.tournament.share_count, 5)
		self.assertEqual(self.tournament.shares.count(), 5)
	
	def test_get_registrations_today_with_no_registrations(self):
		"""Test get_registrations_today returns 0 when no recent registrations"""
		registrations_today = self.tournament.get_registrations_today()
		self.assertEqual(registrations_today, 0)
	
	def test_timeline_phases_with_completed_tournament(self):
		"""Test timeline phases for a completed tournament"""
		now = timezone.now()
		
		completed_tournament = Tournament.objects.create(
			name='Completed Tournament',
			slug='completed-tournament',
			description='A completed tournament',
			game=self.game,
			format='single_elim',
			status='completed',
			organizer=self.organizer,
			registration_start=now - timedelta(days=20),
			registration_end=now - timedelta(days=15),
			check_in_start=now - timedelta(days=14),
			start_datetime=now - timedelta(days=13),
			estimated_end=now - timedelta(days=12),
			actual_end=now - timedelta(days=12)
		)
		
		phases = completed_tournament.get_timeline_phases()
		
		# All phases should be completed
		self.assertEqual(phases[0]['status'], 'completed')
		self.assertEqual(phases[1]['status'], 'completed')
		self.assertEqual(phases[2]['status'], 'completed')
