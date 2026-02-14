"""
Unit tests for PaymentProcessor implementations.

Tests cover:
- StripePaymentProcessor functionality
- PaystackPaymentProcessor functionality
- Payment intent creation
- Payment confirmation
- Refund processing
- Webhook signature verification
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.conf import settings
import stripe
import json
import hmac
import hashlib

from store.managers import (
    PaymentProcessor,
    StripePaymentProcessor,
    PaystackPaymentProcessor,
    PaymentProcessorError
)


class TestStripePaymentProcessor(TestCase):
    """Test cases for StripePaymentProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = StripePaymentProcessor()
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_create):
        """Test successful payment intent creation."""
        # Mock Stripe response
        mock_intent = Mock()
        mock_intent.id = 'pi_test_123'
        mock_intent.client_secret = 'pi_test_123_secret_456'
        mock_intent.status = 'requires_payment_method'
        mock_create.return_value = mock_intent
        
        # Create payment intent
        result = self.processor.create_payment_intent(
            amount=Decimal('99.99'),
            currency='usd',
            metadata={'order_id': 'test-order-123'}
        )
        
        # Verify result
        self.assertEqual(result['id'], 'pi_test_123')
        self.assertEqual(result['client_secret'], 'pi_test_123_secret_456')
        self.assertEqual(result['amount'], Decimal('99.99'))
        self.assertEqual(result['currency'], 'usd')
        self.assertEqual(result['status'], 'requires_payment_method')
        
        # Verify Stripe API was called correctly
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['amount'], 9999)  # Amount in cents
        self.assertEqual(call_args['currency'], 'usd')
        self.assertEqual(call_args['metadata'], {'order_id': 'test-order-123'})
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_stripe_error(self, mock_create):
        """Test payment intent creation with Stripe error."""
        # Mock Stripe error
        mock_create.side_effect = stripe.error.CardError(
            message='Card declined',
            param='card',
            code='card_declined'
        )
        
        # Attempt to create payment intent
        with self.assertRaises(PaymentProcessorError) as context:
            self.processor.create_payment_intent(
                amount=Decimal('99.99'),
                currency='usd'
            )
        
        self.assertIn('Failed to create payment intent', str(context.exception))
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_confirm_payment_success(self, mock_retrieve):
        """Test successful payment confirmation."""
        # Mock Stripe response
        mock_intent = Mock()
        mock_intent.status = 'succeeded'
        mock_retrieve.return_value = mock_intent
        
        # Confirm payment
        result = self.processor.confirm_payment('pi_test_123')
        
        # Verify result
        self.assertTrue(result)
        mock_retrieve.assert_called_once_with('pi_test_123')
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_confirm_payment_not_successful(self, mock_retrieve):
        """Test payment confirmation when payment not successful."""
        # Mock Stripe response
        mock_intent = Mock()
        mock_intent.status = 'requires_payment_method'
        mock_retrieve.return_value = mock_intent
        
        # Confirm payment
        result = self.processor.confirm_payment('pi_test_123')
        
        # Verify result
        self.assertFalse(result)
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_confirm_payment_stripe_error(self, mock_retrieve):
        """Test payment confirmation with Stripe error."""
        # Mock Stripe error
        mock_retrieve.side_effect = stripe.error.InvalidRequestError(
            message='Invalid payment intent ID',
            param='payment_intent'
        )
        
        # Attempt to confirm payment
        with self.assertRaises(PaymentProcessorError) as context:
            self.processor.confirm_payment('invalid_id')
        
        self.assertIn('Failed to confirm payment', str(context.exception))
    
    @patch('stripe.Refund.create')
    def test_refund_payment_full(self, mock_create):
        """Test full refund processing."""
        # Mock Stripe response
        mock_refund = Mock()
        mock_refund.id = 're_test_123'
        mock_refund.status = 'succeeded'
        mock_refund.amount = 9999
        mock_refund.currency = 'usd'
        mock_create.return_value = mock_refund
        
        # Process refund
        result = self.processor.refund_payment('pi_test_123')
        
        # Verify result
        self.assertEqual(result['refund_id'], 're_test_123')
        self.assertEqual(result['status'], 'succeeded')
        self.assertEqual(result['amount'], Decimal('99.99'))
        self.assertEqual(result['currency'], 'usd')
        
        # Verify Stripe API was called correctly
        mock_create.assert_called_once_with(payment_intent='pi_test_123')
    
    @patch('stripe.Refund.create')
    def test_refund_payment_partial(self, mock_create):
        """Test partial refund processing."""
        # Mock Stripe response
        mock_refund = Mock()
        mock_refund.id = 're_test_123'
        mock_refund.status = 'succeeded'
        mock_refund.amount = 5000
        mock_refund.currency = 'usd'
        mock_create.return_value = mock_refund
        
        # Process partial refund
        result = self.processor.refund_payment('pi_test_123', amount=Decimal('50.00'))
        
        # Verify result
        self.assertEqual(result['amount'], Decimal('50.00'))
        
        # Verify Stripe API was called with correct amount
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['amount'], 5000)  # Amount in cents
    
    @patch('stripe.Webhook.construct_event')
    def test_verify_webhook_success(self, mock_construct):
        """Test successful webhook signature verification."""
        # Mock webhook event
        mock_event = {
            'id': 'evt_test_123',
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_test_123'}}
        }
        mock_construct.return_value = mock_event
        
        # Verify webhook
        payload = b'{"test": "data"}'
        signature = 'test_signature'
        
        result = self.processor.verify_webhook(payload, signature)
        
        # Verify result
        self.assertEqual(result, mock_event)
        mock_construct.assert_called_once_with(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET
        )
    
    @patch('stripe.Webhook.construct_event')
    def test_verify_webhook_invalid_signature(self, mock_construct):
        """Test webhook verification with invalid signature."""
        # Mock signature verification error
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            message='Invalid signature',
            sig_header='invalid'
        )
        
        # Attempt to verify webhook
        with self.assertRaises(PaymentProcessorError) as context:
            self.processor.verify_webhook(b'{"test": "data"}', 'invalid_signature')
        
        self.assertIn('Invalid webhook signature', str(context.exception))
    
    @patch('stripe.Webhook.construct_event')
    def test_verify_webhook_invalid_payload(self, mock_construct):
        """Test webhook verification with invalid payload."""
        # Mock value error
        mock_construct.side_effect = ValueError('Invalid payload')
        
        # Attempt to verify webhook
        with self.assertRaises(PaymentProcessorError) as context:
            self.processor.verify_webhook(b'invalid', 'signature')
        
        self.assertIn('Invalid webhook payload', str(context.exception))


class TestPaystackPaymentProcessor(TestCase):
    """Test cases for PaystackPaymentProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = PaystackPaymentProcessor()
    
    @patch('requests.request')
    def test_create_payment_intent_success(self, mock_request):
        """Test successful transaction initialization."""
        # Mock Paystack response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': True,
            'message': 'Authorization URL created',
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test123',
                'access_code': 'test_access_code',
                'reference': 'test_ref_123'
            }
        }
        mock_request.return_value = mock_response
        
        # Create payment intent
        result = self.processor.create_payment_intent(
            amount=Decimal('9999.99'),
            currency='NGN',
            metadata={'order_id': 'test-order-123'}
        )
        
        # Verify result
        self.assertEqual(result['reference'], 'test_ref_123')
        self.assertEqual(result['authorization_url'], 'https://checkout.paystack.com/test123')
        self.assertEqual(result['access_code'], 'test_access_code')
        self.assertEqual(result['amount'], Decimal('9999.99'))
        self.assertEqual(result['currency'], 'NGN')
        
        # Verify API was called correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args['json']['amount'], 999999)  # Amount in kobo
        self.assertEqual(call_args['json']['currency'], 'NGN')
    
    @patch('requests.request')
    def test_create_payment_intent_api_error(self, mock_request):
        """Test transaction initialization with API error."""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'status': False,
            'message': 'Invalid amount'
        }
        mock_request.return_value = mock_response
        
        # Attempt to create payment intent
        with self.assertRaises(PaymentProcessorError) as context:
            self.processor.create_payment_intent(
                amount=Decimal('9999.99'),
                currency='NGN'
            )
        
        self.assertIn('Failed to initialize transaction', str(context.exception))
    
    @patch('requests.request')
    def test_confirm_payment_success(self, mock_request):
        """Test successful payment verification."""
        # Mock Paystack response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': True,
            'message': 'Verification successful',
            'data': {
                'reference': 'test_ref_123',
                'status': 'success',
                'amount': 999999
            }
        }
        mock_request.return_value = mock_response
        
        # Confirm payment
        result = self.processor.confirm_payment('test_ref_123')
        
        # Verify result
        self.assertTrue(result)
    
    @patch('requests.request')
    def test_confirm_payment_not_successful(self, mock_request):
        """Test payment verification when payment not successful."""
        # Mock Paystack response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': True,
            'message': 'Verification successful',
            'data': {
                'reference': 'test_ref_123',
                'status': 'failed',
                'amount': 999999
            }
        }
        mock_request.return_value = mock_response
        
        # Confirm payment
        result = self.processor.confirm_payment('test_ref_123')
        
        # Verify result
        self.assertFalse(result)
    
    @patch('requests.request')
    def test_refund_payment_success(self, mock_request):
        """Test successful refund processing."""
        # Mock Paystack response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': True,
            'message': 'Refund successful',
            'data': {
                'id': 123456,
                'status': 'pending',
                'amount': 999999,
                'currency': 'NGN'
            }
        }
        mock_request.return_value = mock_response
        
        # Process refund
        result = self.processor.refund_payment('test_ref_123')
        
        # Verify result
        self.assertEqual(result['refund_id'], 123456)
        self.assertEqual(result['status'], 'pending')
        self.assertEqual(result['amount'], Decimal('9999.99'))
        self.assertEqual(result['currency'], 'NGN')
    
    def test_verify_webhook_success(self):
        """Test successful webhook signature verification."""
        # Create test webhook payload
        webhook_data = {
            'event': 'charge.success',
            'data': {
                'reference': 'test_ref_123',
                'status': 'success'
            }
        }
        payload = json.dumps(webhook_data).encode('utf-8')
        
        # Compute valid signature
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        # Verify webhook
        result = self.processor.verify_webhook(payload, signature)
        
        # Verify result
        self.assertEqual(result['event'], 'charge.success')
        self.assertEqual(result['data']['reference'], 'test_ref_123')
    
    def test_verify_webhook_invalid_signature(self):
        """Test webhook verification with invalid signature."""
        # Create test webhook payload
        webhook_data = {
            'event': 'charge.success',
            'data': {'reference': 'test_ref_123'}
        }
        payload = json.dumps(webhook_data).encode('utf-8')
        
        # Use invalid signature
        invalid_signature = 'invalid_signature_hash'
        
        # Attempt to verify webhook
        with self.assertRaises(PaymentProcessorError) as context:
            self.processor.verify_webhook(payload, invalid_signature)
        
        self.assertIn('Invalid webhook signature', str(context.exception))
    
    def test_verify_webhook_invalid_json(self):
        """Test webhook verification with invalid JSON payload."""
        # Create invalid JSON payload
        payload = b'invalid json data'
        
        # Compute signature (even though payload is invalid)
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        # Attempt to verify webhook
        with self.assertRaises(PaymentProcessorError) as context:
            self.processor.verify_webhook(payload, signature)
        
        self.assertIn('Invalid webhook payload', str(context.exception))
    
    def test_verify_webhook_string_payload(self):
        """Test webhook verification with string payload (should convert to bytes)."""
        # Create test webhook payload as string
        webhook_data = {
            'event': 'charge.success',
            'data': {'reference': 'test_ref_123'}
        }
        payload_str = json.dumps(webhook_data)
        payload_bytes = payload_str.encode('utf-8')
        
        # Compute valid signature using bytes
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload_bytes,
            hashlib.sha512
        ).hexdigest()
        
        # Verify webhook with string payload
        result = self.processor.verify_webhook(payload_str, signature)
        
        # Verify result
        self.assertEqual(result['event'], 'charge.success')


class TestPaymentProcessorInterface(TestCase):
    """Test cases for PaymentProcessor abstract interface."""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that PaymentProcessor cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            PaymentProcessor()
    
    def test_subclass_must_implement_all_methods(self):
        """Test that subclasses must implement all abstract methods."""
        # Create incomplete subclass
        class IncompleteProcessor(PaymentProcessor):
            def create_payment_intent(self, amount, currency, metadata=None):
                pass
        
        # Attempt to instantiate
        with self.assertRaises(TypeError):
            IncompleteProcessor()


class TestPaymentProcessorConfiguration(TestCase):
    """Test cases for payment processor configuration."""
    
    @override_settings(STRIPE_SECRET_KEY='')
    def test_stripe_processor_requires_secret_key(self):
        """Test that StripePaymentProcessor requires STRIPE_SECRET_KEY."""
        with self.assertRaises(ValueError) as context:
            StripePaymentProcessor()
        
        self.assertIn('STRIPE_SECRET_KEY must be configured', str(context.exception))
    
    @override_settings(PAYSTACK_SECRET_KEY='')
    def test_paystack_processor_requires_secret_key(self):
        """Test that PaystackPaymentProcessor requires PAYSTACK_SECRET_KEY."""
        with self.assertRaises(ValueError) as context:
            PaystackPaymentProcessor()
        
        self.assertIn('PAYSTACK_SECRET_KEY must be configured', str(context.exception))
