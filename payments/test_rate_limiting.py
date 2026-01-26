"""
Tests for Payment rate limiting
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal
import json

from .models import Payment, PaymentMethod

User = get_user_model()


@override_settings(RATELIMIT_ENABLE=True)
class PaymentRateLimitTests(TestCase):
    """Test rate limiting on payment operations"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('payments.views.StripeService.create_payment_intent')
    def test_create_payment_intent_rate_limit(self, mock_create):
        """Test rate limiting on payment intent creation (20/hour)"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending',
            stripe_payment_intent_id='pi_test123'
        )
        
        mock_intent = MagicMock()
        mock_intent.client_secret = 'secret_test123'
        mock_create.return_value = (payment, mock_intent)
        
        # Make 20 requests (should succeed)
        for i in range(20):
            response = self.client.post(
                reverse('payments:create_payment_intent'),
                data=json.dumps({
                    'amount': '50.00',
                    'payment_type': 'tournament_fee',
                    'description': f'Test payment {i}'
                }),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200, f"Request {i+1} should succeed")
        
        # 21st request should be rate limited
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': '50.00',
                'payment_type': 'tournament_fee',
                'description': 'Test payment 21'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 429)  # Too Many Requests
    
    @patch('payments.views.StripeService.add_payment_method')
    def test_add_payment_method_rate_limit(self, mock_add):
        """Test rate limiting on adding payment methods (10/hour)"""
        mock_method = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            card_last4='4242',
            card_brand='visa'
        )
        mock_add.return_value = mock_method
        
        # Make 10 requests (should succeed)
        for i in range(10):
            response = self.client.post(
                reverse('payments:add_payment_method'),
                {'payment_method_id': f'pm_test{i}', 'set_as_default': 'false'}
            )
            self.assertIn(response.status_code, [200, 302], f"Request {i+1} should succeed")
        
        # 11th request should be rate limited
        response = self.client.post(
            reverse('payments:add_payment_method'),
            {'payment_method_id': 'pm_test11', 'set_as_default': 'false'}
        )
        self.assertEqual(response.status_code, 429)
    
    @patch('payments.views.StripeService.remove_payment_method')
    def test_remove_payment_method_rate_limit(self, mock_remove):
        """Test rate limiting on removing payment methods (10/hour)"""
        mock_remove.return_value = True
        
        # Create 11 payment methods
        methods = []
        for i in range(11):
            method = PaymentMethod.objects.create(
                user=self.user,
                stripe_payment_method_id=f'pm_test{i}',
                card_last4='4242',
                card_brand='visa'
            )
            methods.append(method)
        
        # Remove 10 methods (should succeed)
        for i in range(10):
            response = self.client.post(
                reverse('payments:remove_payment_method', args=[methods[i].id]),
                content_type='application/json'
            )
            self.assertIn(response.status_code, [200, 302], f"Request {i+1} should succeed")
        
        # 11th removal should be rate limited
        response = self.client.post(
            reverse('payments:remove_payment_method', args=[methods[10].id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 429)
    
    @patch('payments.views.StripeService.refund_payment')
    def test_refund_request_rate_limit(self, mock_refund):
        """Test rate limiting on refund requests (5/hour)"""
        mock_refund.return_value = True
        
        # Create 6 payments
        payments = []
        for i in range(6):
            payment = Payment.objects.create(
                user=self.user,
                amount=Decimal('50.00'),
                payment_type='tournament_fee',
                status='succeeded',
                stripe_charge_id=f'ch_test{i}'
            )
            payments.append(payment)
        
        # Request 5 refunds (should succeed)
        for i in range(5):
            response = self.client.post(
                reverse('payments:request_refund', args=[payments[i].id]),
                {'reason': f'Test refund {i}'}
            )
            self.assertIn(response.status_code, [200, 302], f"Request {i+1} should succeed")
        
        # 6th refund should be rate limited
        response = self.client.post(
            reverse('payments:request_refund', args=[payments[5].id]),
            {'reason': 'Test refund 6'}
        )
        self.assertEqual(response.status_code, 429)
    
    def test_rate_limit_per_user(self):
        """Test that rate limits are per-user"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create payments for both users
        for i in range(6):
            Payment.objects.create(
                user=self.user,
                amount=Decimal('50.00'),
                payment_type='tournament_fee',
                status='succeeded',
                stripe_charge_id=f'ch_test{i}'
            )
            Payment.objects.create(
                user=other_user,
                amount=Decimal('50.00'),
                payment_type='tournament_fee',
                status='succeeded',
                stripe_charge_id=f'ch_other{i}'
            )
        
        # First user makes 5 refund requests
        with patch('payments.views.StripeService.refund_payment', return_value=True):
            for i in range(5):
                payment = Payment.objects.filter(user=self.user)[i]
                response = self.client.post(
                    reverse('payments:request_refund', args=[payment.id]),
                    {'reason': 'Test'}
                )
                self.assertIn(response.status_code, [200, 302])
        
        # Second user should still be able to make requests
        other_client = Client()
        other_client.login(username='otheruser', password='testpass123')
        
        with patch('payments.views.StripeService.refund_payment', return_value=True):
            payment = Payment.objects.filter(user=other_user).first()
            response = other_client.post(
                reverse('payments:request_refund', args=[payment.id]),
                {'reason': 'Test'}
            )
            self.assertIn(response.status_code, [200, 302])
    
    def test_rate_limit_json_response(self):
        """Test rate limit returns JSON for AJAX requests"""
        # Create 6 payments
        payments = []
        for i in range(6):
            payment = Payment.objects.create(
                user=self.user,
                amount=Decimal('50.00'),
                payment_type='tournament_fee',
                status='succeeded',
                stripe_charge_id=f'ch_test{i}'
            )
            payments.append(payment)
        
        # Make 5 requests to hit rate limit
        with patch('payments.views.StripeService.refund_payment', return_value=True):
            for i in range(5):
                self.client.post(
                    reverse('payments:request_refund', args=[payments[i].id]),
                    {'reason': 'Test'}
                )
        
        # 6th request should return JSON error
        response = self.client.post(
            reverse('payments:request_refund', args=[payments[5].id]),
            {'reason': 'Test'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('retry_after', data)


@override_settings(RATELIMIT_ENABLE=False)
class PaymentRateLimitDisabledTests(TestCase):
    """Test that rate limiting can be disabled"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('payments.views.StripeService.create_payment_intent')
    def test_rate_limit_disabled(self, mock_create):
        """Test that rate limiting can be disabled via settings"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending',
            stripe_payment_intent_id='pi_test123'
        )
        
        mock_intent = MagicMock()
        mock_intent.client_secret = 'secret_test123'
        mock_create.return_value = (payment, mock_intent)
        
        # Make 25 requests (more than the limit)
        for i in range(25):
            response = self.client.post(
                reverse('payments:create_payment_intent'),
                data=json.dumps({
                    'amount': '50.00',
                    'payment_type': 'tournament_fee',
                    'description': f'Test payment {i}'
                }),
                content_type='application/json'
            )
            # All should succeed when rate limiting is disabled
            self.assertEqual(response.status_code, 200, f"Request {i+1} should succeed")
