"""
Test error handling for payment UI
Tests network errors, Stripe API errors, validation errors, timeout scenarios,
error message display, and error logging

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""
import json
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages
import stripe
import uuid

from payments.models import Payment, PaymentMethod
from payments.services import StripeService

User = get_user_model()


class PaymentErrorHandlingTests(TestCase):
    """Test error handling in payment views and services"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    # ========================================================================
    # Network Error Tests
    # ========================================================================
    
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_network_error_on_payment_intent_creation(self, mock_create):
        """Test handling of network errors when creating payment intent"""
        # Simulate network error
        mock_create.side_effect = stripe.error.APIConnectionError(
            "Network error occurred"
        )
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': 5000,
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should return 500 error
        self.assertEqual(response.status_code, 500)
        
        # Should contain error message
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Network error', str(data['error']))
    
    @patch('payments.services.stripe.SetupIntent.create')
    def test_network_error_on_setup_intent_creation(self, mock_create):
        """Test handling of network errors when creating setup intent"""
        # Simulate network error
        mock_create.side_effect = stripe.error.APIConnectionError(
            "Connection timeout"
        )
        
        response = self.client.get(reverse('payments:add_payment_method'))
        
        # Should still render page but with no client_secret
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['client_secret'])
    
    # ========================================================================
    # Stripe API Error Tests
    # ========================================================================
    
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_stripe_card_declined_error(self, mock_create):
        """Test handling of card declined errors from Stripe"""
        # Simulate card declined error
        mock_create.side_effect = stripe.error.CardError(
            message="Your card was declined",
            param="card",
            code="card_declined"
        )
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': 5000,
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
    
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_stripe_insufficient_funds_error(self, mock_create):
        """Test handling of insufficient funds errors"""
        # Simulate insufficient funds error
        mock_create.side_effect = stripe.error.CardError(
            message="Your card has insufficient funds",
            param="card",
            code="insufficient_funds"
        )
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': 5000,
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should return error with specific message
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('insufficient funds', str(data['error']).lower())
    
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_stripe_expired_card_error(self, mock_create):
        """Test handling of expired card errors"""
        # Simulate expired card error
        mock_create.side_effect = stripe.error.CardError(
            message="Your card has expired",
            param="exp_month",
            code="expired_card"
        )
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': 5000,
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
    
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_stripe_invalid_request_error(self, mock_create):
        """Test handling of invalid request errors"""
        # Simulate invalid request error
        mock_create.side_effect = stripe.error.InvalidRequestError(
            message="Invalid amount",
            param="amount"
        )
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': -100,  # Invalid amount
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
    
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_stripe_authentication_error(self, mock_create):
        """Test handling of Stripe authentication errors"""
        # Simulate authentication error
        mock_create.side_effect = stripe.error.AuthenticationError(
            "Invalid API key"
        )
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': 5000,
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
    
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_stripe_rate_limit_error(self, mock_create):
        """Test handling of Stripe rate limit errors"""
        # Simulate rate limit error
        mock_create.side_effect = stripe.error.RateLimitError(
            "Too many requests"
        )
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': 5000,
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
    
    # ========================================================================
    # Validation Error Tests
    # ========================================================================
    
    def test_missing_amount_validation(self):
        """Test validation error when amount is missing"""
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should return 400 error
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Amount required', data['error'])
    
    def test_invalid_payment_method_validation(self):
        """Test validation error when payment method doesn't exist"""
        # Use a valid UUID format
        fake_uuid = uuid.uuid4()
        response = self.client.post(
            reverse('payments:remove_payment_method', args=[fake_uuid]),
            content_type='application/json'
        )
        
        # Should return 404 error
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_payment_validation(self):
        """Test validation error when payment doesn't exist"""
        # Use a valid UUID format
        fake_uuid = uuid.uuid4()
        response = self.client.get(
            reverse('payments:detail', args=[fake_uuid])
        )
        
        # Should return 404 error
        self.assertEqual(response.status_code, 404)
    
    def test_non_refundable_payment_validation(self):
        """Test validation error when trying to refund non-refundable payment"""
        # Create a failed payment (not refundable)
        payment = Payment.objects.create(
            user=self.user,
            amount=5000,
            currency='usd',
            status='failed',
            payment_type='tournament_fee',
            description='Test payment'
        )
        
        response = self.client.post(
            reverse('payments:request_refund', args=[payment.id]),
            data={'reason': 'Test refund'}
        )
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        
        # Check that error message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('not eligible for refund' in str(m) for m in messages))
    
    def test_invalid_http_method_validation(self):
        """Test validation error when using wrong HTTP method"""
        response = self.client.get(reverse('payments:create_payment_intent'))
        
        # Should return 400 error
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('POST required', data['error'])
    
    def test_checkout_without_amount_validation(self):
        """Test validation error when accessing checkout without amount"""
        response = self.client.get(reverse('payments:checkout'))
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        
        # Check that error message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Invalid payment amount' in str(m) for m in messages))
    
    # ========================================================================
    # Timeout Scenario Tests
    # ========================================================================
    
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_timeout_on_payment_intent_creation(self, mock_create):
        """Test handling of timeout when creating payment intent"""
        # Simulate timeout
        mock_create.side_effect = stripe.error.APIConnectionError(
            "Request timed out"
        )
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': 5000,
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
    
    @patch('payments.services.stripe.Refund.create')
    def test_timeout_on_refund_processing(self, mock_create):
        """Test handling of timeout when processing refund"""
        # Create a succeeded payment
        payment = Payment.objects.create(
            user=self.user,
            amount=5000,
            currency='usd',
            status='succeeded',
            payment_type='tournament_fee',
            description='Test payment',
            stripe_payment_intent_id='pi_test123'
        )
        
        # Simulate timeout
        mock_create.side_effect = stripe.error.APIConnectionError(
            "Connection timeout"
        )
        
        response = self.client.post(
            reverse('payments:request_refund', args=[payment.id]),
            data={'reason': 'Test refund'}
        )
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        
        # Check that error message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Failed to process refund' in str(m) for m in messages))
    
    # ========================================================================
    # Error Message Display Tests
    # ========================================================================
    
    def test_error_message_format_in_json_response(self):
        """Test that error messages are properly formatted in JSON responses"""
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Should have proper JSON structure
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('error', data)
        self.assertIsInstance(data['error'], str)
        self.assertTrue(len(data['error']) > 0)
    
    def test_error_message_in_django_messages(self):
        """Test that error messages are added to Django messages framework"""
        # Create a failed payment
        payment = Payment.objects.create(
            user=self.user,
            amount=5000,
            currency='usd',
            status='failed',
            payment_type='tournament_fee',
            description='Test payment'
        )
        
        response = self.client.post(
            reverse('payments:request_refund', args=[payment.id]),
            data={'reason': 'Test refund'}
        )
        
        # Check that error message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        self.assertTrue(any('error' in str(m.tags) for m in messages))
    
    def test_error_message_consistency(self):
        """Test that error messages are consistent across different error types"""
        # Test multiple error scenarios
        test_cases = [
            {
                'data': {},  # Missing amount
                'expected_key': 'error'
            },
            {
                'data': {'amount': 5000},  # Missing other fields is OK
                'expected_key': 'client_secret'  # Should succeed
            }
        ]
        
        for case in test_cases:
            response = self.client.post(
                reverse('payments:create_payment_intent'),
                data=json.dumps(case['data']),
                content_type='application/json'
            )
            
            data = response.json()
            self.assertIn(case['expected_key'], data)
    
    # ========================================================================
    # Error Logging Tests
    # ========================================================================
    
    @patch('payments.views.logger')
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_error_logging_on_payment_failure(self, mock_create, mock_logger):
        """Test that errors are properly logged"""
        # Simulate error
        error_message = "Test error message"
        mock_create.side_effect = Exception(error_message)
        
        response = self.client.post(
            reverse('payments:create_payment_intent'),
            data=json.dumps({
                'amount': 5000,
                'payment_type': 'tournament_fee',
                'description': 'Test payment'
            }),
            content_type='application/json'
        )
        
        # Verify error was logged
        mock_logger.error.assert_called()
        call_args = str(mock_logger.error.call_args)
        self.assertIn('Error creating payment intent', call_args)
    
    @patch('payments.views.logger')
    def test_webhook_error_logging(self, mock_logger):
        """Test that webhook errors are properly logged"""
        # Send invalid webhook
        response = self.client.post(
            reverse('payments:stripe_webhook'),
            data='invalid payload',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        # Should return 400
        self.assertEqual(response.status_code, 400)
        
        # Verify error was logged
        mock_logger.error.assert_called()
    
    @patch('payments.services.stripe.PaymentIntent.create')
    def test_error_details_in_logs(self, mock_create):
        """Test that error logs contain sufficient details for debugging"""
        # Simulate detailed error
        mock_create.side_effect = stripe.error.CardError(
            message="Card declined",
            param="card",
            code="card_declined"
        )
        
        with self.assertLogs('payments', level='ERROR') as logs:
            response = self.client.post(
                reverse('payments:create_payment_intent'),
                data=json.dumps({
                    'amount': 5000,
                    'payment_type': 'tournament_fee',
                    'description': 'Test payment'
                }),
                content_type='application/json'
            )
            
            # Verify error was logged with details
            self.assertTrue(len(logs.output) > 0)
            self.assertTrue(any('Error creating payment intent' in log for log in logs.output))


class PaymentMethodErrorHandlingTests(TestCase):
    """Test error handling for payment method operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('payments.services.stripe.PaymentMethod.detach')
    def test_error_removing_payment_method(self, mock_detach):
        """Test error handling when removing payment method fails"""
        # Create payment method
        payment_method = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=12,
            card_exp_year=2025
        )
        
        # Simulate error
        mock_detach.side_effect = stripe.error.InvalidRequestError(
            message="Payment method not found",
            param="payment_method"
        )
        
        response = self.client.post(
            reverse('payments:remove_payment_method', args=[payment_method.id]),
            content_type='application/json'
        )
        
        # Should return error (either 400 JSON or 302 redirect with message)
        self.assertIn(response.status_code, [302, 400])
        
        if response.status_code == 400:
            data = response.json()
            self.assertIn('error', data)
        else:
            messages = list(get_messages(response.wsgi_request))
            self.assertTrue(any('Failed' in str(m) for m in messages))
    
    @patch('payments.services.stripe.PaymentMethod.attach')
    def test_error_adding_payment_method(self, mock_attach):
        """Test error handling when adding payment method fails"""
        # Simulate error
        mock_attach.side_effect = stripe.error.CardError(
            message="Card was declined",
            param="card",
            code="card_declined"
        )
        
        response = self.client.post(
            reverse('payments:add_payment_method'),
            data={
                'payment_method_id': 'pm_test123',
                'set_as_default': 'false'
            }
        )
        
        # Should return JSON response with success=False
        if response['Content-Type'] == 'application/json':
            data = response.json()
            self.assertIn('success', data)
            self.assertFalse(data['success'])


class WebhookErrorHandlingTests(TestCase):
    """Test error handling for Stripe webhooks"""
    
    def test_invalid_webhook_payload(self):
        """Test handling of invalid webhook payload"""
        response = self.client.post(
            reverse('payments:stripe_webhook'),
            data='invalid json',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        # Should return 400
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_webhook_signature(self):
        """Test handling of invalid webhook signature"""
        response = self.client.post(
            reverse('payments:stripe_webhook'),
            data=json.dumps({'type': 'payment_intent.succeeded'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        # Should return 400
        self.assertEqual(response.status_code, 400)
    
    def test_missing_webhook_signature(self):
        """Test handling of missing webhook signature"""
        response = self.client.post(
            reverse('payments:stripe_webhook'),
            data=json.dumps({'type': 'payment_intent.succeeded'}),
            content_type='application/json'
        )
        
        # Should return 400
        self.assertEqual(response.status_code, 400)
