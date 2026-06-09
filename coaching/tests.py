"""
Tests for the coaching app: models, forms, and views.
"""
import uuid
from decimal import Decimal
from datetime import time, timedelta
from unittest.mock import patch, MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from core.models import Game
from coaching.models import (
    CoachProfile, CoachGameExpertise, CoachAvailability,
    CoachingSession, SessionReview, CoachingPackage, PackagePurchase,
)
from coaching.forms import (
    CoachProfileForm, CoachGameExpertiseForm, BookingForm,
    SessionReviewForm, PackageForm,
)

User = get_user_model()


@pytest.fixture
def game(db):
    return Game.objects.create(name='Test Game', slug='test-game')


@pytest.fixture
def coach(db, player_user):
    player_user.role = 'coach'
    player_user.save()
    return CoachProfile.objects.create(
        user=player_user,
        bio='Expert coach',
        experience_level='advanced',
        years_experience=5,
        hourly_rate=Decimal('50.00'),
        accepting_students=True,
    )


class TestCoachProfileModel:
    def test_create_coach_profile(self, coach):
        assert coach.bio == 'Expert coach'
        assert coach.experience_level == 'advanced'
        assert coach.status == 'active'

    def test_str_representation(self, coach):
        assert str(coach) == f'{coach.user.username} - {coach.experience_level}'

    def test_average_rating_default_zero(self, coach):
        assert coach.average_rating == Decimal('0.00')

    def test_total_sessions_default_zero(self, coach):
        assert coach.total_sessions == 0


class TestCoachGameExpertiseModel:
    def test_create_expertise(self, coach, game):
        expertise = CoachGameExpertise.objects.create(
            coach=coach,
            game=game,
            rank='diamond',
            is_primary=True,
        )
        assert expertise.rank == 'diamond'
        assert expertise.is_primary
        assert str(expertise) == f'{coach.user.username} - {game.name}'

    def test_unique_together(self, coach, game):
        CoachGameExpertise.objects.create(coach=coach, game=game, rank='gold')
        with pytest.raises(Exception):
            CoachGameExpertise.objects.create(coach=coach, game=game, rank='platinum')


class TestCoachAvailabilityModel:
    def test_create_availability(self, coach):
        avail = CoachAvailability.objects.create(
            coach=coach,
            weekday=1,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        assert avail.weekday == 1
        assert avail.is_active

    def test_unique_together(self, coach):
        CoachAvailability.objects.create(
            coach=coach, weekday=0, start_time=time(9, 0), end_time=time(10, 0),
        )
        with pytest.raises(Exception):
            CoachAvailability.objects.create(
                coach=coach, weekday=0, start_time=time(9, 0), end_time=time(10, 0),
            )


class TestCoachingSessionModel:
    @pytest.fixture
    def session(self, coach, game, player_user):
        return CoachingSession.objects.create(
            coach=coach,
            student=player_user,
            game=game,
            session_type='individual',
            scheduled_start=timezone.now() + timedelta(days=1),
            scheduled_end=timezone.now() + timedelta(days=1, hours=1),
            duration_minutes=60,
            price=Decimal('50.00'),
            status='pending',
        )

    def test_create_session(self, session):
        assert session.status == 'pending'
        assert session.duration_minutes == 60

    def test_session_str(self, session, coach, player_user):
        expected = f'{player_user.username} with {coach.user.username} - Pending'
        assert str(session) == expected


class TestSessionReviewModel:
    @pytest.fixture
    def session(self, coach, game, player_user):
        return CoachingSession.objects.create(
            coach=coach, student=player_user, game=game,
            session_type='individual', duration_minutes=60,
            scheduled_start=timezone.now(), scheduled_end=timezone.now() + timedelta(hours=1),
            price=Decimal('50.00'), status='completed',
        )

    def test_create_review(self, session, coach, player_user):
        review = SessionReview.objects.create(
            session=session, coach=coach, student=player_user,
            rating=5, review='Great session!',
        )
        assert review.rating == 5
        assert review.would_recommend

    def test_review_str(self, session, coach, player_user):
        review = SessionReview.objects.create(
            session=session, coach=coach, student=player_user,
            rating=4, review='Good',
        )
        assert str(review) == f'Review for {session} by {player_user.username}: 4/5'


class TestCoachingPackageModel:
    def test_create_package(self, coach):
        pkg = CoachingPackage.objects.create(
            coach=coach, name='Starter Pack', description='5 sessions',
            number_of_sessions=5, session_duration=60,
            total_price=Decimal('200.00'),
        )
        assert pkg.is_active
        assert pkg.discount_percentage == Decimal('0.00')

    def test_package_str(self, coach):
        pkg = CoachingPackage.objects.create(
            coach=coach, name='Pro Pack', description='10 sessions',
            number_of_sessions=10, session_duration=60,
            total_price=Decimal('400.00'),
        )
        assert str(pkg) == f'Pro Pack by {coach.user.username}'


class TestPackagePurchaseModel:
    @pytest.fixture
    def package(self, coach):
        return CoachingPackage.objects.create(
            coach=coach, name='Starter', description='desc',
            number_of_sessions=5, session_duration=60,
            total_price=Decimal('200.00'), valid_for_days=90,
        )

    def test_create_purchase(self, package, player_user):
        purchase = PackagePurchase.objects.create(
            package=package, student=player_user,
            sessions_remaining=5, amount_paid=Decimal('200.00'),
            expires_at=timezone.now() + timedelta(days=90),
        )
        assert purchase.status == 'active'


class TestCoachingForms:
    def test_coach_profile_form_valid(self):
        form = CoachProfileForm(data={
            'bio': 'I am a good coach',
            'experience_level': 'advanced',
            'years_experience': 3,
            'hourly_rate': 75.00,
            'accepting_students': True,
            'max_students_per_week': 5,
            'min_session_duration': 30,
            'max_session_duration': 120,
            'session_increment': 30,
            'offers_individual': True,
            'max_group_size': 1,
            'preferred_platform': 'Discord',
        })
        assert form.is_valid()

    def test_coach_profile_form_missing_bio(self):
        form = CoachProfileForm(data={
            'experience_level': 'beginner',
            'years_experience': 0,
            'hourly_rate': 25.00,
            'accepting_students': True,
        })
        assert not form.is_valid()

    def test_coach_game_expertise_form_valid(self, game):
        form = CoachGameExpertiseForm(data={
            'game': game.pk,
            'rank': 'platinum',
            'is_primary': True,
        })
        assert form.is_valid()

    def test_booking_form_requires_game(self, coach):
        form = BookingForm(coach=coach, data={
            'session_type': 'individual',
            'duration_minutes': 60,
            'date': '2026-06-15',
            'time': '14:00',
        })
        assert not form.is_valid()

    def test_session_review_form_valid(self):
        form = SessionReviewForm(data={
            'rating': 5,
            'review': 'Excellent coaching!',
            'would_recommend': True,
            'improvement_seen': True,
        })
        assert form.is_valid()

    def test_package_form_valid(self):
        form = PackageForm(data={
            'name': 'Gold Pack',
            'description': '10 premium sessions',
            'number_of_sessions': 10,
            'session_duration': 60,
            'total_price': 500.00,
            'discount_percentage': 10,
            'valid_for_days': 90,
        })
        assert form.is_valid()

    def test_package_form_discount_over_50(self):
        form = PackageForm(data={
            'name': 'Too Discounted',
            'description': 'desc',
            'number_of_sessions': 5,
            'session_duration': 60,
            'total_price': 500.00,
            'discount_percentage': 60,
            'valid_for_days': 90,
        })
        assert not form.is_valid()


class TestCoachingViews:
    @pytest.mark.django_db
    def test_coach_list_view(self, client, coach):
        response = client.get(reverse('coaching:coach_list'))
        assert response.status_code == 200
        assert 'coach' in response.content.decode().lower()

    @pytest.mark.django_db
    def test_coach_detail_view(self, client, coach):
        response = client.get(reverse('coaching:coach_detail', kwargs={'pk': coach.pk}))
        assert response.status_code == 200
        assert coach.bio in response.content.decode()

    @pytest.mark.django_db
    def test_become_coach_login_required(self, client):
        response = client.get(reverse('coaching:become_coach'))
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_session_list_login_required(self, client):
        response = client.get(reverse('coaching:session_list'))
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_package_list_view(self, client, coach):
        response = client.get(reverse('coaching:package_list'))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_get_available_slots_api(self, client, coach):
        url = reverse('coaching:available_slots', kwargs={'coach_pk': coach.pk})
        response = client.get(url, {'date': '2026-06-15'})
        assert response.status_code == 200
        import json
        data = json.loads(response.content)
        assert isinstance(data, list)

    @pytest.mark.django_db
    def test_book_session_login_required(self, client, coach):
        response = client.get(reverse('coaching:book_session', kwargs={'coach_pk': coach.pk}))
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_purchase_package_login_required(self, client, coach):
        pkg = CoachingPackage.objects.create(
            coach=coach, name='Test Pkg', description='desc',
            number_of_sessions=3, session_duration=60,
            total_price=Decimal('150.00'),
        )
        response = client.get(reverse('coaching:purchase_package', kwargs={'pk': pkg.pk}))
        assert response.status_code == 302
