"""
Tests for Payment services
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal

from .services import StripeService, WebhookHandler
from .models import Payment, PaymentMethod, StripeWebhookEvent

User = get_user_model()


class StripeServiceTests(TestCase):
    """Test StripeService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('payments.services.stripe.Customer.create')
    def test_get_or_create_customer_creates_new(self, mock_create):
        """Test creating a new Stripe customer"""
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test123'
        mock_create.return_value = mock_customer
        
        customer_id = StripeService.get_or_create_customer(self.user)
        
        self.assertEqual(customer_id, 'cus_test123')
        self.user.refresh_from_db()
        self.assertEqual(self.user.stripe_customer_id, 'cus_test123')
        mock_create.assert_called_once()
    
    @patch('payments.services.stripe.Customer.retrieve')
    def test_get_or_create_customer_returns_existing(self, mock_retrieve):
        """Test returning existing Stripe customer"""
        self.user.stripe_customer_id = 'cus_existing'
        self.user.save()
        
        mock_customer = MagicMock()
        mock_customer.id = 'cus_existing'
        mock_retrieve.return_value = mock_customer
        
        customer_id = StripeService.get_or_create_customer(self.user)
        
        self.assertEqual(customer_id, 'cus_existing')
        mock_retrieve.assert_called_once_with('cus_existing')
    
    @patch('payments.services.stripe.PaymentIntent.create')
    @patch('payments.services.StripeService.get_or_create_customer')
    def test_create_payment_intent(self, mock_get_customer, mock_create_intent):
        """Test creating a payment intent"""
        mock_get_customer.return_value = 'cus_test123'
        
        mock_intent = MagicMock()
        mock_intent.id = 'pi_test123'
        mock_intent.client_secret = 'secret_test123'
        mock_create_intent.return_value = mock_intent
        
        payment, intent = StripeService.create_payment_intent(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            description='Test payment'
        )
        
        self.assertIsInstance(payment, Payment)
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.amount, Decimal('50.00'))
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.stripe_payment_intent_id, 'pi_test123')
        self.assertEqual(intent.id, 'pi_test123')
        
        # Verify Stripe was called with correct amount in cents
        mock_create_intent.assert_called_once()
        call_kwargs = mock_create_intent.call_args[1]
        self.assertEqual(call_kwargs['amount'], 5000)  # 50.00 * 100

    
    @patch('payments.services.stripe.PaymentIntent.retrieve')
    def test_confirm_payment_success(self, mock_retrieve):
        """Test confirming a successful payment"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending',
            stripe_payment_intent_id='pi_test123'
        )
        
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_intent.charges = MagicMock()
        mock_intent.charges.data = [MagicMock(id='ch_test123', balance_transaction=None)]
        mock_retrieve.return_value = mock_intent
        
        result = StripeService.confirm_payment(payment)
        
        self.assertTrue(result)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'succeeded')
        self.assertEqual(payment.stripe_charge_id, 'ch_test123')
        self.assertIsNotNone(payment.completed_at)
    
    @patch('payments.services.stripe.Refund.create')
    def test_refund_payment(self, mock_refund):
        """Test refunding a payment"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded',
            stripe_payment_intent_id='pi_test123',
            stripe_charge_id='ch_test123'
        )
        
        mock_refund_obj = MagicMock()
        mock_refund_obj.id = 're_test123'
        mock_refund.return_value = mock_refund_obj
        
        result = StripeService.refund_payment(payment, reason='Customer request')
        
        self.assertTrue(result)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'refunded')
        self.assertEqual(payment.refund_amount, Decimal('50.00'))
        self.assertEqual(payment.refund_reason, 'Customer request')
        
        # Verify Stripe was called with correct amount in cents
        mock_refund.assert_called_once()
        call_kwargs = mock_refund.call_args[1]
        self.assertEqual(call_kwargs['amount'], 5000)
    
    def test_refund_payment_not_refundable(self):
        """Test refunding a non-refundable payment"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending'  # Not succeeded
        )
        
        result = StripeService.refund_payment(payment)
        
        self.assertFalse(result)
    
    @patch('payments.services.stripe.PaymentMethod.attach')
    @patch('payments.services.StripeService.get_or_create_customer')
    def test_add_payment_method(self, mock_get_customer, mock_attach):
        """Test adding a payment method"""
        mock_get_customer.return_value = 'cus_test123'
        
        mock_pm = MagicMock()
        mock_pm.type = 'card'
        mock_pm.card = MagicMock(
            brand='visa',
            last4='4242',
            exp_month=12,
            exp_year=2025
        )
        mock_attach.return_value = mock_pm
        
        payment_method = StripeService.add_payment_method(
            user=self.user,
            payment_method_id='pm_test123',
            set_as_default=True
        )
        
        self.assertIsInstance(payment_method, PaymentMethod)
        self.assertEqual(payment_method.user, self.user)
        self.assertEqual(payment_method.stripe_payment_method_id, 'pm_test123')
        self.assertEqual(payment_method.card_brand, 'visa')
        self.assertEqual(payment_method.card_last4, '4242')
        self.assertTrue(payment_method.is_default)
    
    @patch('payments.services.stripe.PaymentMethod.detach')
    def test_remove_payment_method(self, mock_detach):
        """Test removing a payment method"""
        payment_method = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_test123',
            card_last4='4242',
            card_brand='visa'
        )
        
        result = StripeService.remove_payment_method(payment_method)
        
        self.assertTrue(result)
        payment_method.refresh_from_db()
        self.assertFalse(payment_method.is_active)
        mock_detach.assert_called_once_with('pm_test123')
    
    @patch('payments.services.stripe.SetupIntent.create')
    @patch('payments.services.StripeService.get_or_create_customer')
    def test_create_setup_intent(self, mock_get_customer, mock_create):
        """Test creating a setup intent"""
        mock_get_customer.return_value = 'cus_test123'
        
        mock_intent = MagicMock()
        mock_intent.id = 'seti_test123'
        mock_intent.client_secret = 'secret_test123'
        mock_create.return_value = mock_intent
        
        setup_intent = StripeService.create_setup_intent(self.user)
        
        self.assertEqual(setup_intent.id, 'seti_test123')
        mock_create.assert_called_once()


class WebhookHandlerTests(TestCase):
    """Test WebhookHandler"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_handle_event_creates_webhook_record(self):
        """Test that handling event creates webhook record"""
        event_data = {
            'id': 'evt_test123',
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test123'
                }
            }
        }
        
        # Create payment for the event
        Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending',
            stripe_payment_intent_id='pi_test123'
        )
        
        WebhookHandler.handle_event(event_data)
        
        # Verify webhook event was created
        webhook_event = StripeWebhookEvent.objects.get(stripe_event_id='evt_test123')
        self.assertEqual(webhook_event.event_type, 'payment_intent.succeeded')
        self.assertTrue(webhook_event.processed)
    
    def test_handle_event_duplicate_ignored(self):
        """Test that duplicate events are ignored"""
        # Create existing webhook event
        StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test123',
            event_type='payment_intent.succeeded',
            payload={'test': 'data'},
            processed=True
        )
        
        event_data = {
            'id': 'evt_test123',
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_test123'}}
        }
        
        result = WebhookHandler.handle_event(event_data)
        
        self.assertTrue(result)
        # Should still only have one event
        self.assertEqual(StripeWebhookEvent.objects.filter(stripe_event_id='evt_test123').count(), 1)
    
    def test_handle_payment_succeeded(self):
        """Test handling payment succeeded event"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending',
            stripe_payment_intent_id='pi_test123'
        )
        
        webhook_event = StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test123',
            event_type='payment_intent.succeeded',
            payload={'test': 'data'}
        )
        
        event_data = {
            'data': {
                'object': {
                    'id': 'pi_test123',
                    'status': 'succeeded',
                    'charges': {
                        'data': [{'id': 'ch_test123', 'balance_transaction': None}]
                    }
                }
            }
        }
        
        with patch('payments.services.stripe.PaymentIntent.retrieve') as mock_retrieve:
            mock_intent = MagicMock()
            mock_intent.status = 'succeeded'
            mock_intent.charges = MagicMock()
            mock_intent.charges.data = [MagicMock(id='ch_test123', balance_transaction=None)]
            mock_retrieve.return_value = mock_intent
            
            result = WebhookHandler.handle_payment_succeeded(event_data, webhook_event)
        
        self.assertTrue(result)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'succeeded')
    
    def test_handle_payment_failed(self):
        """Test handling payment failed event"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending',
            stripe_payment_intent_id='pi_test123'
        )
        
        webhook_event = StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test123',
            event_type='payment_intent.payment_failed',
            payload={'test': 'data'}
        )
        
        event_data = {
            'data': {
                'object': {
                    'id': 'pi_test123',
                    'last_payment_error': {
                        'message': 'Card declined'
                    }
                }
            }
        }
        
        result = WebhookHandler.handle_payment_failed(event_data, webhook_event)
        
        self.assertTrue(result)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')
        self.assertEqual(payment.metadata['failure_reason'], 'Card declined')
