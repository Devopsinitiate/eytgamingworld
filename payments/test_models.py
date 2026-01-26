"""
Tests for Payment models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from .models import Payment, PaymentMethod, Invoice, StripeWebhookEvent

User = get_user_model()


class PaymentModelTests(TestCase):
    """Test Payment model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_payment_creation(self):
        """Test creating a payment"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            currency='USD',
            payment_type='tournament_fee',
            status='pending',
            description='Test tournament fee'
        )
        
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.amount, Decimal('50.00'))
        self.assertEqual(payment.currency, 'USD')
        self.assertEqual(payment.payment_type, 'tournament_fee')
        self.assertEqual(payment.status, 'pending')
        self.assertIsNotNone(payment.id)
        self.assertIsNotNone(payment.created_at)
    
    def test_payment_str_representation(self):
        """Test payment string representation"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending'
        )
        
        expected = f"{self.user.email} - tournament_fee - $50.00 - pending"
        self.assertEqual(str(payment), expected)
    
    def test_mark_succeeded(self):
        """Test marking payment as succeeded"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending'
        )
        
        payment.mark_succeeded()
        
        self.assertEqual(payment.status, 'succeeded')
        self.assertIsNotNone(payment.completed_at)

    
    def test_mark_failed(self):
        """Test marking payment as failed"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending'
        )
        
        payment.mark_failed('Card declined')
        
        self.assertEqual(payment.status, 'failed')
        self.assertEqual(payment.metadata['failure_reason'], 'Card declined')
    
    def test_process_refund(self):
        """Test processing a refund"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded',
            stripe_charge_id='ch_test123'
        )
        
        payment.process_refund(amount=Decimal('50.00'), reason='Customer request')
        
        self.assertEqual(payment.status, 'refunded')
        self.assertEqual(payment.refund_amount, Decimal('50.00'))
        self.assertEqual(payment.refund_reason, 'Customer request')
        self.assertIsNotNone(payment.refunded_at)
    
    def test_is_refundable_succeeded_payment(self):
        """Test that succeeded payment with charge ID is refundable"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded',
            stripe_charge_id='ch_test123'
        )
        
        self.assertTrue(payment.is_refundable)
    
    def test_is_not_refundable_without_charge_id(self):
        """Test that payment without charge ID is not refundable"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded'
        )
        
        self.assertFalse(payment.is_refundable)
    
    def test_is_not_refundable_already_refunded(self):
        """Test that already refunded payment is not refundable"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded',
            stripe_charge_id='ch_test123',
            refund_amount=Decimal('50.00')
        )
        
        self.assertFalse(payment.is_refundable)
    
    def test_is_not_refundable_pending_payment(self):
        """Test that pending payment is not refundable"""
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='pending',
            stripe_charge_id='ch_test123'
        )
        
        self.assertFalse(payment.is_refundable)


class PaymentMethodModelTests(TestCase):
    """Test PaymentMethod model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_payment_method_creation(self):
        """Test creating a payment method"""
        method = PaymentMethod.objects.create(
            user=self.user,
            method_type='card',
            stripe_payment_method_id='pm_test123',
            card_last4='4242',
            card_brand='visa',
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True
        )
        
        self.assertEqual(method.user, self.user)
        self.assertEqual(method.method_type, 'card')
        self.assertEqual(method.card_last4, '4242')
        self.assertEqual(method.card_brand, 'visa')
        self.assertTrue(method.is_default)
        self.assertTrue(method.is_active)
    
    def test_payment_method_str_with_card(self):
        """Test payment method string representation with card"""
        method = PaymentMethod.objects.create(
            user=self.user,
            method_type='card',
            card_last4='4242',
            card_brand='visa'
        )
        
        self.assertEqual(str(method), 'visa ending in 4242')
    
    def test_payment_method_str_without_card(self):
        """Test payment method string representation without card details"""
        method = PaymentMethod.objects.create(
            user=self.user,
            method_type='paypal'
        )
        
        expected = f"paypal - {self.user.email}"
        self.assertEqual(str(method), expected)


class InvoiceModelTests(TestCase):
    """Test Invoice model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee',
            status='succeeded'
        )
    
    def test_invoice_creation(self):
        """Test creating an invoice"""
        invoice = Invoice.objects.create(
            payment=self.payment,
            invoice_number='INV-001',
            bill_to_name='Test User',
            bill_to_email='test@example.com',
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00'),
            due_date=timezone.now().date() + timedelta(days=30)
        )
        
        self.assertEqual(invoice.payment, self.payment)
        self.assertEqual(invoice.invoice_number, 'INV-001')
        self.assertEqual(invoice.status, 'draft')
        self.assertEqual(invoice.subtotal, Decimal('50.00'))
        self.assertEqual(invoice.total_amount, Decimal('50.00'))
    
    def test_invoice_str_representation(self):
        """Test invoice string representation"""
        invoice = Invoice.objects.create(
            payment=self.payment,
            invoice_number='INV-001',
            bill_to_name='Test User',
            bill_to_email='test@example.com',
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00'),
            due_date=timezone.now().date() + timedelta(days=30)
        )
        
        self.assertEqual(str(invoice), 'Invoice INV-001 - Test User')


class StripeWebhookEventModelTests(TestCase):
    """Test StripeWebhookEvent model"""
    
    def test_webhook_event_creation(self):
        """Test creating a webhook event"""
        event = StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test123',
            event_type='payment_intent.succeeded',
            payload={'test': 'data'}
        )
        
        self.assertEqual(event.stripe_event_id, 'evt_test123')
        self.assertEqual(event.event_type, 'payment_intent.succeeded')
        self.assertFalse(event.processed)
        self.assertIsNone(event.processed_at)
    
    def test_mark_processed(self):
        """Test marking event as processed"""
        event = StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test123',
            event_type='payment_intent.succeeded',
            payload={'test': 'data'}
        )
        
        event.mark_processed()
        
        self.assertTrue(event.processed)
        self.assertIsNotNone(event.processed_at)
    
    def test_mark_error(self):
        """Test marking event with error"""
        event = StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test123',
            event_type='payment_intent.succeeded',
            payload={'test': 'data'}
        )
        
        event.mark_error('Test error message')
        
        self.assertEqual(event.error_message, 'Test error message')
    
    def test_webhook_event_str_representation(self):
        """Test webhook event string representation"""
        event = StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test123',
            event_type='payment_intent.succeeded',
            payload={'test': 'data'}
        )
        
        self.assertEqual(str(event), 'payment_intent.succeeded - evt_test123')
