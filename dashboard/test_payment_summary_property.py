"""
Property-based tests for payment summary accuracy.

This module tests the payment summary accuracy property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from core.models import User
from payments.models import Payment, PaymentMethod
from dashboard.services import PaymentSummaryService
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid


@pytest.mark.django_db
class TestPaymentSummaryAccuracy:
    """
    **Feature: user-profile-dashboard, Property 31: Payment summary accuracy**
    
    For any user, the payment summary total spent must equal the sum of all completed 
    payment amounts, and recent payments count must match the count of payments in 
    the last 30 days.
    
    **Validates: Requirements 12.1, 12.2**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_succeeded_payments=st.integers(min_value=0, max_value=20),
        num_failed_payments=st.integers(min_value=0, max_value=10),
        num_pending_payments=st.integers(min_value=0, max_value=5)
    )
    def test_total_spent_equals_sum_of_succeeded_payments(
        self, 
        num_succeeded_payments, 
        num_failed_payments, 
        num_pending_payments
    ):
        """Property: Total spent equals sum of all succeeded payment amounts"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Track expected total
        expected_total = Decimal('0.00')
        
        # Create succeeded payments with random amounts
        for i in range(num_succeeded_payments):
            amount = Decimal(str(round((i + 1) * 10.50, 2)))  # Varying amounts
            Payment.objects.create(
                user=user,
                amount=amount,
                currency='USD',
                payment_type='tournament_fee',
                status='succeeded',
                completed_at=timezone.now()
            )
            expected_total += amount
        
        # Create failed payments (should not count)
        for i in range(num_failed_payments):
            amount = Decimal(str(round((i + 1) * 15.75, 2)))
            Payment.objects.create(
                user=user,
                amount=amount,
                currency='USD',
                payment_type='tournament_fee',
                status='failed'
            )
        
        # Create pending payments (should not count)
        for i in range(num_pending_payments):
            amount = Decimal(str(round((i + 1) * 20.00, 2)))
            Payment.objects.create(
                user=user,
                amount=amount,
                currency='USD',
                payment_type='tournament_fee',
                status='pending'
            )
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify total spent equals sum of succeeded payments only
        assert summary['total_spent'] == expected_total, \
            f"Total spent should be {expected_total}, got {summary['total_spent']}"
        
        # Cleanup - delete payments first due to PROTECT constraint
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_recent_payments=st.integers(min_value=0, max_value=15),
        num_old_payments=st.integers(min_value=0, max_value=10)
    )
    def test_recent_payments_count_matches_last_30_days(
        self, 
        num_recent_payments, 
        num_old_payments
    ):
        """Property: Recent payments count matches payments in last 30 days"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create recent payments (within last 30 days)
        now = timezone.now()
        for i in range(num_recent_payments):
            # Spread payments across the last 30 days
            days_ago = i % 30
            created_at = now - timedelta(days=days_ago)
            
            payment = Payment(
                user=user,
                amount=Decimal('25.00'),
                currency='USD',
                payment_type='tournament_fee',
                status='succeeded'
            )
            payment.save()
            # Update created_at after save
            Payment.objects.filter(id=payment.id).update(created_at=created_at)
        
        # Create old payments (more than 30 days ago)
        for i in range(num_old_payments):
            days_ago = 31 + i  # At least 31 days ago
            created_at = now - timedelta(days=days_ago)
            
            payment = Payment(
                user=user,
                amount=Decimal('30.00'),
                currency='USD',
                payment_type='tournament_fee',
                status='succeeded'
            )
            payment.save()
            # Update created_at after save
            Payment.objects.filter(id=payment.id).update(created_at=created_at)
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify recent payments count matches expected
        assert summary['recent_payments_count'] == num_recent_payments, \
            f"Recent payments count should be {num_recent_payments}, got {summary['recent_payments_count']}"
        
        # Cleanup - delete payments first due to PROTECT constraint
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_payments=st.integers(min_value=1, max_value=20)
    )
    def test_total_spent_is_non_negative(self, num_payments):
        """Property: Total spent is always non-negative"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payments with positive amounts
        for i in range(num_payments):
            amount = Decimal(str(round((i + 1) * 12.99, 2)))
            Payment.objects.create(
                user=user,
                amount=amount,
                currency='USD',
                payment_type='tournament_fee',
                status='succeeded',
                completed_at=timezone.now()
            )
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify total spent is non-negative
        assert summary['total_spent'] >= Decimal('0.00'), \
            f"Total spent should be non-negative, got {summary['total_spent']}"
        
        # Cleanup - delete payments first due to PROTECT constraint
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    def test_zero_payments_returns_zero_total(self):
        """Property: User with no payments has zero total spent"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with no payments
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify total spent is zero
        assert summary['total_spent'] == Decimal('0.00'), \
            f"Total spent should be 0.00 for user with no payments, got {summary['total_spent']}"
        
        # Verify recent payments count is zero
        assert summary['recent_payments_count'] == 0, \
            f"Recent payments count should be 0, got {summary['recent_payments_count']}"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_succeeded=st.integers(min_value=1, max_value=10),
        num_refunded=st.integers(min_value=1, max_value=5)
    )
    def test_refunded_payments_not_counted_in_total(self, num_succeeded, num_refunded):
        """Property: Refunded payments are not counted in total spent"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Track expected total (only succeeded, not refunded)
        expected_total = Decimal('0.00')
        
        # Create succeeded payments
        for i in range(num_succeeded):
            amount = Decimal(str(round((i + 1) * 18.50, 2)))
            Payment.objects.create(
                user=user,
                amount=amount,
                currency='USD',
                payment_type='tournament_fee',
                status='succeeded',
                completed_at=timezone.now()
            )
            expected_total += amount
        
        # Create refunded payments (should not count)
        for i in range(num_refunded):
            amount = Decimal(str(round((i + 1) * 22.00, 2)))
            Payment.objects.create(
                user=user,
                amount=amount,
                currency='USD',
                payment_type='tournament_fee',
                status='refunded',
                refund_amount=amount,
                refunded_at=timezone.now()
            )
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify total spent excludes refunded payments
        assert summary['total_spent'] == expected_total, \
            f"Total spent should exclude refunded payments. Expected {expected_total}, got {summary['total_spent']}"
        
        # Cleanup - delete payments first due to PROTECT constraint
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_active_methods=st.integers(min_value=0, max_value=5),
        num_inactive_methods=st.integers(min_value=0, max_value=3)
    )
    def test_saved_payment_methods_count_accuracy(
        self, 
        num_active_methods, 
        num_inactive_methods
    ):
        """Property: Saved payment methods count only includes active methods"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create active payment methods
        for i in range(num_active_methods):
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{1000 + i}',
                card_brand='Visa',
                is_active=True
            )
        
        # Create inactive payment methods (should not count)
        for i in range(num_inactive_methods):
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{2000 + i}',
                card_brand='Mastercard',
                is_active=False
            )
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify saved payment methods count only includes active methods
        assert summary['saved_payment_methods_count'] == num_active_methods, \
            f"Saved payment methods count should be {num_active_methods}, got {summary['saved_payment_methods_count']}"
        
        # Cleanup - delete payment methods first
        PaymentMethod.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        has_default=st.booleans(),
        num_non_default=st.integers(min_value=0, max_value=4)
    )
    def test_has_default_payment_method_accuracy(self, has_default, num_non_default):
        """Property: has_default_method correctly reflects presence of default payment method"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create default payment method if specified
        if has_default:
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4='1234',
                card_brand='Visa',
                is_default=True,
                is_active=True
            )
        
        # Create non-default payment methods
        for i in range(num_non_default):
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{5000 + i}',
                card_brand='Mastercard',
                is_default=False,
                is_active=True
            )
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify has_default_method matches expected
        assert summary['has_default_method'] == has_default, \
            f"has_default_method should be {has_default}, got {summary['has_default_method']}"
        
        # Cleanup - delete payment methods first
        PaymentMethod.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_payments=st.integers(min_value=6, max_value=20)
    )
    def test_recent_payments_list_limited_to_five(self, num_payments):
        """Property: Recent payments list contains at most 5 payments"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create multiple payments
        for i in range(num_payments):
            Payment.objects.create(
                user=user,
                amount=Decimal('15.00'),
                currency='USD',
                payment_type='tournament_fee',
                status='succeeded',
                completed_at=timezone.now()
            )
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify recent payments list has at most 5 items
        recent_payments_list = list(summary['recent_payments'])
        assert len(recent_payments_list) <= 5, \
            f"Recent payments list should have at most 5 items, got {len(recent_payments_list)}"
        
        # If we have more than 5 payments, verify we get exactly 5
        if num_payments >= 5:
            assert len(recent_payments_list) == 5, \
                f"Recent payments list should have exactly 5 items when {num_payments} payments exist, got {len(recent_payments_list)}"
        
        # Cleanup - delete payments first due to PROTECT constraint
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_payments=st.integers(min_value=2, max_value=10)
    )
    def test_recent_payments_ordered_by_date_descending(self, num_payments):
        """Property: Recent payments are ordered by creation date (newest first)"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payments with different timestamps
        now = timezone.now()
        for i in range(num_payments):
            created_at = now - timedelta(hours=i)
            payment = Payment(
                user=user,
                amount=Decimal('20.00'),
                currency='USD',
                payment_type='tournament_fee',
                status='succeeded'
            )
            payment.save()
            # Update created_at after save
            Payment.objects.filter(id=payment.id).update(created_at=created_at)
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify recent payments are ordered by date descending
        recent_payments_list = list(summary['recent_payments'])
        for i in range(len(recent_payments_list) - 1):
            assert recent_payments_list[i].created_at >= recent_payments_list[i + 1].created_at, \
                f"Recent payments should be ordered by date descending"
        
        # Cleanup - delete payments first due to PROTECT constraint
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        amount1=st.decimals(min_value='0.01', max_value='999.99', places=2),
        amount2=st.decimals(min_value='0.01', max_value='999.99', places=2),
        amount3=st.decimals(min_value='0.01', max_value='999.99', places=2)
    )
    def test_total_spent_calculation_with_decimal_precision(self, amount1, amount2, amount3):
        """Property: Total spent calculation maintains decimal precision"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payments with specific decimal amounts
        amounts = [amount1, amount2, amount3]
        expected_total = sum(amounts, Decimal('0.00'))
        
        for amount in amounts:
            Payment.objects.create(
                user=user,
                amount=amount,
                currency='USD',
                payment_type='tournament_fee',
                status='succeeded',
                completed_at=timezone.now()
            )
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify total spent matches expected with proper decimal precision
        assert summary['total_spent'] == expected_total, \
            f"Total spent should be {expected_total}, got {summary['total_spent']}"
        
        # Verify result has at most 2 decimal places
        assert summary['total_spent'].as_tuple().exponent >= -2, \
            f"Total spent should have at most 2 decimal places"
        
        # Cleanup - delete payments first due to PROTECT constraint
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    def test_payment_summary_includes_all_required_fields(self):
        """Property: Payment summary always includes all required fields"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Get payment summary
        summary = PaymentSummaryService.get_payment_summary(user.id)
        
        # Verify all required fields are present
        required_fields = [
            'total_spent',
            'recent_payments_count',
            'saved_payment_methods_count',
            'has_default_method',
            'recent_payments'
        ]
        
        for field in required_fields:
            assert field in summary, \
                f"Payment summary should include '{field}' field"
        
        # Verify field types
        assert isinstance(summary['total_spent'], Decimal), \
            "total_spent should be a Decimal"
        assert isinstance(summary['recent_payments_count'], int), \
            "recent_payments_count should be an integer"
        assert isinstance(summary['saved_payment_methods_count'], int), \
            "saved_payment_methods_count should be an integer"
        assert isinstance(summary['has_default_method'], bool), \
            "has_default_method should be a boolean"
        
        # Cleanup
        user.delete()
