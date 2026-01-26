"""
Tests for Payment views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal
import json

from .models import Payment, PaymentMethod

User = get_user_model()


class PaymentViewTests(TestCase):
    """Test payment views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_payment_methods_list_requires_login(self):
        """Test that payment methods list requires login"""
        self.client.logout()
        response = self.client.get(reverse('payments:payment_methods'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_payment_methods_list_renders(self):
        """Test payment methods list page renders"""
        response = self.client.get(reverse('payments:payment_methods'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/payment_methods.html')
    
    def test_payment_methods_list_shows_methods(self):
        """Test payment methods list shows user's methods"""
        PaymentMethod.objects.create(
            user=self.user,
            card_last4='4242',
            card_brand='visa',
            card_exp_month=12,
            card_exp_year=2025
        )
        
        response = self.client.get(reverse('payments:payment_methods'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '4242')
        self.assertContains(response, 'visa')
    
    @patch('payments.views.StripeService.create_setup_intent')
    def test_add_payment_method_get(self, mock_setup_intent):
        """Test add payment method GET request"""
        mock_intent = MagicMock()
        mock_intent.client_secret = 'secret_test123'
        mock_setup_intent.return_value = mock_intent
        
        response = self.client.get(reverse('payments:add_payment_method'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/add_payment_method.html')
        self.assertIn('client_secret', response.context)
    
    @patch('payments.views.StripeService.add_payment_method')
    def test_add_payment_method_post_success(self, mock_add):
        """Test add payment method POST request success"""
        mock_method = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            card_last4='4242',
            card_brand='visa'
        )
        mock_add.return_value = mock_method
        
        response = self.client.post(
            reverse('payments:add_payment_method'),
            {'payment_method_id': 'pm_test123', 'set_as_default': 'true'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    
    @patch('payments.views.StripeService.remove_payment_method')
    def test_remove_payment_method(self, mock_remove):
        """Test removing a payment method"""
        method = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            card_last4='4242',
            card_brand='visa'
        )
        mock_remove.return_value = True
        
        response = self.client.post(
            reverse('payments:remove_payment_method', args=[method.id]),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_set_default_payment_method(self):
        """Test setting default payment method"""
        method1 = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test1',
            card_last4='4242',
            card_brand='visa',
            is_default=True
        )
        method2 = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test2',
            card_last4='5555',
            card_brand='mastercard',
            is_default=False
        )
        
        response = self.client.post(
            reverse('payments:set_default_payment_method', args=[method2.id]),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify method2 is now default
        method1.refresh_from_db()
        method2.refresh_from_db()
        self.assertFalse(method1.is_default)
        self.assertTrue(method2.is_default)
    
    @patch('payments.views.StripeService.create_payment_intent')
    def test_create_payment_intent(self, mock_create):
        """Test creating a payment intent"""
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
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': '50.00',
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['client_secret'], 'secret_test123')
        self.assertEqual(data['payment_id'], str(payment.id))
    
    def test_checkout_page_requires_amount(self):
        """Test checkout page requires amount parameter"""
        response = self.client.get(reverse('payments:checkout'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_checkout_page_renders(self):
        """Test checkout page renders with amount"""
        response = self.client.get(
            reverse('payments:checkout') + '?amount=50.00&type=tournament_fee&description=Test'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/checkout.html')
        self.assertContains(response, '50.00')
    
    def test_payment_history_requires_login(self):
        """Test payment history requires login"""
        self.client.logout()
        response = self.client.get(reverse('payments:history'))
        self.assertEqual(response.status_code, 302)
    
    def test_payment_history_renders(self):
        """Test payment history page renders"""
        response = self.client.get(reverse('payments:history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/history.html')
    
    def test_payment_history_shows_user_payments(self):
        """Test payment history shows only user's payments"""
        # Create payment for current user
        payment1 = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded',
            description='User payment'
        )
        
        # Create payment for another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        payment2 = Payment.objects.create(
            user=other_user,
            amount=Decimal('100.00'),
            payment_type='tournament_fee',
            status='succeeded',
            description='Other user payment'
        )
        
        response = self.client.get(reverse('payments:history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User payment')
        self.assertNotContains(response, 'Other user payment')
    
    def test_payment_detail_requires_login(self):
        """Test payment detail requires login"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded'
        )
        
        self.client.logout()
        response = self.client.get(reverse('payments:detail', args=[payment.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_payment_detail_renders(self):
        """Test payment detail page renders"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded',
            description='Test payment'
        )
        
        response = self.client.get(reverse('payments:detail', args=[payment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/detail.html')
        self.assertContains(response, '50.00')
        self.assertContains(response, 'Test payment')
    
    def test_payment_detail_only_shows_own_payment(self):
        """Test user can only view their own payments"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        payment = Payment.objects.create(
            user=other_user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded'
        )
        
        response = self.client.get(reverse('payments:detail', args=[payment.id]))
        self.assertEqual(response.status_code, 404)
    
    @patch('payments.views.StripeService.refund_payment')
    def test_request_refund(self, mock_refund):
        """Test requesting a refund"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded',
            stripe_charge_id='ch_test123'
        )
        mock_refund.return_value = True
        
        response = self.client.post(
            reverse('payments:request_refund', args=[payment.id]),
            {'reason': 'Customer request'}
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
        mock_refund.assert_called_once()
    
    def test_request_refund_not_refundable(self):
        """Test requesting refund for non-refundable payment"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending'  # Not refundable
        )
        
        response = self.client.post(
            reverse('payments:request_refund', args=[payment.id]),
            {'reason': 'Customer request'}
        )
        
        self.assertEqual(response.status_code, 302)
        # Payment should still be pending
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'pending')
    
    def test_payment_cancel_page_renders(self):
        """Test payment cancel page renders"""
        response = self.client.get(reverse('payments:cancel'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/cancel.html')
    
    @patch('payments.views.stripe.Webhook.construct_event')
    @patch('payments.views.WebhookHandler.handle_event')
    def test_stripe_webhook(self, mock_handle, mock_construct):
        """Test Stripe webhook endpoint"""
        mock_event = {'id': 'evt_test123', 'type': 'payment_intent.succeeded'}
        mock_construct.return_value = mock_event
        mock_handle.return_value = True
        
        response = self.client.post(
            reverse('payments:stripe_webhook'),
            data='{"test": "data"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        mock_handle.assert_called_once_with(mock_event)
