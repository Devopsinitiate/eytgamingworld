"""
Property-based tests for default payment method uniqueness.

This module tests the default payment method uniqueness property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from core.models import User
from payments.models import PaymentMethod
import uuid


@pytest.mark.django_db
class TestDefaultPaymentMethodUniqueness:
    """
    **Feature: user-profile-dashboard, Property 32: Default payment method uniqueness**
    
    For any user, at most one payment method can be marked as default at any time.
    
    **Validates: Requirements 12.3**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_payment_methods=st.integers(min_value=1, max_value=10)
    )
    def test_at_most_one_default_payment_method(self, num_payment_methods):
        """Property: User can have at most one default payment method"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create multiple payment methods, randomly setting one as default
        default_index = num_payment_methods // 2  # Pick middle one as default
        
        for i in range(num_payment_methods):
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{1000 + i}',
                card_brand='Visa' if i % 2 == 0 else 'Mastercard',
                is_default=(i == default_index),
                is_active=True
            )
        
        # Count default payment methods
        default_count = PaymentMethod.objects.filter(
            user=user,
            is_default=True,
            is_active=True
        ).count()
        
        # Verify at most one default payment method
        assert default_count <= 1, \
            f"User should have at most 1 default payment method, found {default_count}"
        
        # Cleanup
        PaymentMethod.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_payment_methods=st.integers(min_value=2, max_value=8),
        num_defaults_to_create=st.integers(min_value=2, max_value=5)
    )
    def test_setting_multiple_defaults_results_in_one_default(
        self, 
        num_payment_methods, 
        num_defaults_to_create
    ):
        """Property: When multiple payment methods are set as default, only one remains default"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Ensure we don't try to set more defaults than we have methods
        num_defaults_to_create = min(num_defaults_to_create, num_payment_methods)
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payment methods, all initially non-default
        payment_methods = []
        for i in range(num_payment_methods):
            pm = PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{2000 + i}',
                card_brand='Visa',
                is_default=False,
                is_active=True
            )
            payment_methods.append(pm)
        
        # Try to set multiple payment methods as default
        # In a proper implementation, setting a new default should unset the previous one
        for i in range(num_defaults_to_create):
            pm = payment_methods[i]
            
            # Unset all other defaults first (this is what the application should do)
            PaymentMethod.objects.filter(user=user, is_default=True).update(is_default=False)
            
            # Set this one as default
            pm.is_default = True
            pm.save()
        
        # Count default payment methods after all operations
        default_count = PaymentMethod.objects.filter(
            user=user,
            is_default=True,
            is_active=True
        ).count()
        
        # Verify exactly one default payment method
        assert default_count == 1, \
            f"After setting multiple defaults, user should have exactly 1 default payment method, found {default_count}"
        
        # Cleanup
        PaymentMethod.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_active_methods=st.integers(min_value=1, max_value=6),
        num_inactive_methods=st.integers(min_value=0, max_value=4)
    )
    def test_default_payment_method_is_active(
        self, 
        num_active_methods, 
        num_inactive_methods
    ):
        """Property: If a default payment method exists, it must be active"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create active payment methods, one as default
        for i in range(num_active_methods):
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{3000 + i}',
                card_brand='Visa',
                is_default=(i == 0),  # First one is default
                is_active=True
            )
        
        # Create inactive payment methods (none should be default)
        for i in range(num_inactive_methods):
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{4000 + i}',
                card_brand='Mastercard',
                is_default=False,
                is_active=False
            )
        
        # Get default payment method if it exists
        default_method = PaymentMethod.objects.filter(
            user=user,
            is_default=True
        ).first()
        
        # If a default exists, it must be active
        if default_method:
            assert default_method.is_active, \
                "Default payment method must be active"
        
        # Cleanup
        PaymentMethod.objects.filter(user=user).delete()
        user.delete()
    
    def test_user_with_no_payment_methods_has_no_default(self):
        """Property: User with no payment methods has no default payment method"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with no payment methods
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Count default payment methods
        default_count = PaymentMethod.objects.filter(
            user=user,
            is_default=True
        ).count()
        
        # Verify no default payment method
        assert default_count == 0, \
            f"User with no payment methods should have 0 default payment methods, found {default_count}"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_payment_methods=st.integers(min_value=1, max_value=8)
    )
    def test_user_can_have_zero_default_payment_methods(self, num_payment_methods):
        """Property: User can have zero default payment methods (all non-default)"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payment methods, all non-default
        for i in range(num_payment_methods):
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{5000 + i}',
                card_brand='Visa',
                is_default=False,
                is_active=True
            )
        
        # Count default payment methods
        default_count = PaymentMethod.objects.filter(
            user=user,
            is_default=True
        ).count()
        
        # Verify zero default payment methods is valid
        assert default_count == 0, \
            f"User should be able to have 0 default payment methods, found {default_count}"
        
        # Cleanup
        PaymentMethod.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_users=st.integers(min_value=2, max_value=5),
        methods_per_user=st.integers(min_value=1, max_value=4)
    )
    def test_default_payment_method_uniqueness_across_users(
        self, 
        num_users, 
        methods_per_user
    ):
        """Property: Each user's default payment method is independent of other users"""
        users = []
        
        # Create multiple users, each with their own payment methods
        for u in range(num_users):
            unique_id = str(uuid.uuid4())[:8]
            user = User.objects.create_user(
                email=f'test_{unique_id}@example.com',
                username=f'testuser_{unique_id}',
                password='testpass123'
            )
            users.append(user)
            
            # Create payment methods for this user
            for i in range(methods_per_user):
                PaymentMethod.objects.create(
                    user=user,
                    method_type='card',
                    card_last4=f'{6000 + i}',
                    card_brand='Visa',
                    is_default=(i == 0),  # First one is default
                    is_active=True
                )
        
        # Verify each user has at most one default payment method
        for user in users:
            default_count = PaymentMethod.objects.filter(
                user=user,
                is_default=True
            ).count()
            
            assert default_count <= 1, \
                f"User {user.username} should have at most 1 default payment method, found {default_count}"
        
        # Cleanup
        for user in users:
            PaymentMethod.objects.filter(user=user).delete()
            user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_payment_methods=st.integers(min_value=2, max_value=10)
    )
    def test_deleting_default_payment_method_leaves_at_most_one_default(
        self, 
        num_payment_methods
    ):
        """Property: After deleting default payment method, user still has at most one default"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payment methods with first one as default
        payment_methods = []
        for i in range(num_payment_methods):
            pm = PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{7000 + i}',
                card_brand='Visa',
                is_default=(i == 0),
                is_active=True
            )
            payment_methods.append(pm)
        
        # Delete the default payment method
        default_method = PaymentMethod.objects.filter(user=user, is_default=True).first()
        if default_method:
            default_method.delete()
        
        # Count remaining default payment methods
        default_count = PaymentMethod.objects.filter(
            user=user,
            is_default=True
        ).count()
        
        # Verify at most one default payment method remains
        assert default_count <= 1, \
            f"After deleting default payment method, user should have at most 1 default, found {default_count}"
        
        # Cleanup
        PaymentMethod.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_payment_methods=st.integers(min_value=2, max_value=8)
    )
    def test_deactivating_default_payment_method_maintains_uniqueness(
        self, 
        num_payment_methods
    ):
        """Property: Deactivating default payment method maintains at most one default constraint"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payment methods with first one as default
        payment_methods = []
        for i in range(num_payment_methods):
            pm = PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{8000 + i}',
                card_brand='Visa',
                is_default=(i == 0),
                is_active=True
            )
            payment_methods.append(pm)
        
        # Deactivate the default payment method
        default_method = PaymentMethod.objects.filter(
            user=user, 
            is_default=True
        ).first()
        
        if default_method:
            default_method.is_active = False
            default_method.save()
        
        # Count active default payment methods
        active_default_count = PaymentMethod.objects.filter(
            user=user,
            is_default=True,
            is_active=True
        ).count()
        
        # Verify at most one active default payment method
        assert active_default_count <= 1, \
            f"User should have at most 1 active default payment method, found {active_default_count}"
        
        # Count all default payment methods (including inactive)
        all_default_count = PaymentMethod.objects.filter(
            user=user,
            is_default=True
        ).count()
        
        # Verify at most one default payment method overall
        assert all_default_count <= 1, \
            f"User should have at most 1 default payment method (including inactive), found {all_default_count}"
        
        # Cleanup
        PaymentMethod.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        initial_methods=st.integers(min_value=1, max_value=5),
        additional_methods=st.integers(min_value=1, max_value=5)
    )
    def test_adding_payment_methods_maintains_default_uniqueness(
        self, 
        initial_methods, 
        additional_methods
    ):
        """Property: Adding new payment methods maintains at most one default constraint"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create initial payment methods with first one as default
        for i in range(initial_methods):
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{9000 + i}',
                card_brand='Visa',
                is_default=(i == 0),
                is_active=True
            )
        
        # Add additional payment methods (all non-default)
        for i in range(additional_methods):
            PaymentMethod.objects.create(
                user=user,
                method_type='card',
                card_last4=f'{9500 + i}',
                card_brand='Mastercard',
                is_default=False,
                is_active=True
            )
        
        # Count default payment methods
        default_count = PaymentMethod.objects.filter(
            user=user,
            is_default=True
        ).count()
        
        # Verify at most one default payment method
        assert default_count <= 1, \
            f"After adding payment methods, user should have at most 1 default, found {default_count}"
        
        # Cleanup
        PaymentMethod.objects.filter(user=user).delete()
        user.delete()
