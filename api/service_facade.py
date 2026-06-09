"""
Service layer facade for EYTGaming.

Provides a unified interface for cross-app business operations,
reducing tight coupling between views and models/services directly.
"""
from decimal import Decimal
from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from core.models import Game, UserGameProfile
from tournaments.models import Tournament, TournamentRegistration
from coaching.models import CoachProfile, CoachingSession, CoachingPackage, PackagePurchase
from payments.models import Payment, PaymentMethod
from notifications.models import Notification

User = get_user_model()


class UserService:
    """Facade for user-related operations."""

    @staticmethod
    def get_profile_data(user: User) -> dict:
        return {
            'user': user,
            'game_profiles': UserGameProfile.objects.filter(user=user).select_related('game'),
            'recent_notifications': Notification.objects.filter(user=user, read=False)[:5],
            'stats': {
                'total_points': user.total_points,
                'level': user.level,
                'date_joined': user.date_joined,
            },
        }

    @staticmethod
    def complete_profile(user: User, first_name: str, last_name: str, country: str, dob) -> bool:
        user.first_name = first_name
        user.last_name = last_name
        user.country = country
        user.date_of_birth = dob
        user.save(update_fields=['first_name', 'last_name', 'country', 'date_of_birth'])
        return user.check_profile_completeness()


class TournamentService:
    """Facade for tournament-related business logic."""

    @staticmethod
    def register_user(tournament: Tournament, user: User) -> Optional[Payment]:
        with transaction.atomic():
            registration, created = TournamentRegistration.objects.get_or_create(
                tournament=tournament, user=user,
            )
            if not created:
                return None
            if tournament.registration_fee > Decimal('0.00'):
                payment = Payment.objects.create(
                    user=user,
                    amount=tournament.registration_fee,
                    payment_type='tournament_fee',
                    status='pending',
                )
                return payment
            registration.confirmed = True
            registration.save()
            return None

    @staticmethod
    def get_open_tournaments(game_id: Optional[int] = None):
        qs = Tournament.objects.filter(status='open')
        if game_id:
            qs = qs.filter(game_id=game_id)
        return qs.select_related('game')[:20]


class CoachingService:
    """Facade for coaching-related business logic."""

    @staticmethod
    def book_session(
        coach: CoachProfile, student: User, game: Game,
        scheduled_start, duration_minutes: int,
        session_type: str = 'individual', topics: Optional[list] = None,
    ) -> CoachingSession:
        scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)
        price = (coach.hourly_rate * Decimal(str(duration_minutes))) / Decimal('60')

        session = CoachingSession.objects.create(
            coach=coach,
            student=student,
            game=game,
            session_type=session_type,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=duration_minutes,
            price=price,
            status='pending',
            topics=topics or [],
        )
        Payment.objects.create(
            user=student,
            amount=price,
            payment_type='coaching_session',
            status='pending',
        )
        return session

    @staticmethod
    def purchase_package(package: CoachingPackage, student: User) -> PackagePurchase:
        purchase = PackagePurchase.objects.create(
            package=package,
            student=student,
            sessions_remaining=package.number_of_sessions,
            amount_paid=package.total_price,
            expires_at=timezone.now() + timedelta(days=package.valid_for_days),
        )
        Payment.objects.create(
            user=student,
            amount=package.total_price,
            payment_type='package_purchase',
            status='pending',
        )
        return purchase


class PaymentService:
    """Facade for payment-related operations."""

    @staticmethod
    def get_user_payment_history(user: User, limit: int = 25):
        return Payment.objects.filter(user=user).order_by('-created_at')[:limit]

    @staticmethod
    def get_default_payment_method(user: User) -> Optional[PaymentMethod]:
        return PaymentMethod.objects.filter(user=user, is_default=True, is_active=True).first()
