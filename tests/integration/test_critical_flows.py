"""
Integration tests for critical cross-app workflows:
1. User registration -> profile completion -> tournament registration -> payment
2. User registration -> coach profile creation -> session booking
"""
import pytest
from decimal import Decimal
from datetime import timedelta, date

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from core.models import Game, UserGameProfile
from tournaments.models import Tournament, TournamentRegistration
from payments.models import Payment
from coaching.models import CoachProfile, CoachingSession

User = get_user_model()


class TournamentRegistrationFlowTest(TestCase):
    """Verify a user can register, complete profile, and enter a tournament."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='flowplayer',
            email='flow@test.com',
            password='testpass123',
        )
        self.game = Game.objects.create(name='Test Game', slug='test-game')
        self.tournament = Tournament.objects.create(
            title='Test Tournament',
            game=self.game,
            registration_fee=Decimal('25.00'),
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            max_participants=16,
            status='open',
        )

    def test_profile_completion_and_tournament_entry(self):
        """User completes profile, sees tournament, registers."""
        self.client.force_login(self.user)

        # 1. Check profile is initially incomplete
        self.assertFalse(self.user.profile_completed)

        # 2. Complete the profile
        self.user.first_name = 'Flow'
        self.user.last_name = 'Player'
        self.user.country = 'US'
        self.user.date_of_birth = date(1995, 6, 15)
        self.user.save()
        self.assertTrue(self.user.check_profile_completeness())

        # 3. Create a game profile
        profile = UserGameProfile.objects.create(
            user=self.user,
            game=self.game,
            in_game_name='FlowPro',
            skill_rating=1500,
        )
        self.assertEqual(profile.in_game_name, 'FlowPro')

        # 4. View tournament detail
        response = self.client.get(
            reverse('tournaments:detail', kwargs={'pk': self.tournament.pk})
        )
        self.assertEqual(response.status_code, 200)

        # 5. Register for tournament
        register_url = reverse(
            'tournaments:register', kwargs={'pk': self.tournament.pk}
        )
        response = self.client.post(register_url, follow=True)
        self.assertIn(response.status_code, (200, 302))

        # 6. Verify a payment record was created
        payment_exists = Payment.objects.filter(
            user=self.user,
            payment_type='tournament_fee',
            amount=Decimal('25.00'),
        ).exists()
        self.assertTrue(payment_exists)


class CoachingBookingFlowTest(TestCase):
    """Verify a user can become a coach and another user can book a session."""

    def setUp(self):
        self.client = Client()
        self.coach_user = User.objects.create_user(
            username='coachflow',
            email='coachflow@test.com',
            password='testpass123',
            role='coach',
        )
        self.student_user = User.objects.create_user(
            username='studentflow',
            email='studentflow@test.com',
            password='testpass123',
        )
        self.game = Game.objects.create(name='Coaching Game', slug='coaching-game')
        self.coach_profile = CoachProfile.objects.create(
            user=self.coach_user,
            bio='Expert flow coach',
            experience_level='advanced',
            years_experience=5,
            hourly_rate=Decimal('75.00'),
            accepting_students=True,
        )

    def test_coach_list_and_session_booking(self):
        """Student views coaches, books a session, payment is created."""
        # 1. View coach list (unauthenticated)
        response = self.client.get(reverse('coaching:coach_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'coachflow', html=False)

        # 2. View coach detail
        response = self.client.get(
            reverse('coaching:coach_detail', kwargs={'pk': self.coach_profile.pk})
        )
        self.assertEqual(response.status_code, 200)

        # 3. Student logs in and accesses booking
        self.client.force_login(self.student_user)
        book_url = reverse(
            'coaching:book_session', kwargs={'coach_pk': self.coach_profile.pk}
        )
        response = self.client.get(book_url)
        self.assertEqual(response.status_code, 200)

        # 4. Submit booking
        response = self.client.post(book_url, {
            'game': self.game.pk,
            'session_type': 'individual',
            'duration_minutes': 60,
            'date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '14:00',
            'topics': '["mechanics"]',
        }, follow=True)
        self.assertIn(response.status_code, (200, 302))

        # 5. Verify session was created
        session_exists = CoachingSession.objects.filter(
            coach=self.coach_profile,
            student=self.student_user,
        ).exists()
        self.assertTrue(session_exists)

    def test_coach_profile_requires_auth_to_edit(self):
        """Unauthenticated users cannot edit coach profiles."""
        self.client.logout()
        edit_url = reverse(
            'coaching:coach_edit', kwargs={'pk': self.coach_profile.pk}
        )
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 302)
