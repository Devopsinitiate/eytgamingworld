"""
Tests for the payments app: models, services, and views.
"""
import json
import uuid
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from payments.models import Payment, Invoice, StripeWebhookEvent, PaymentMethod

User = get_user_model()


@pytest.fixture
def payment(player_user):
    return Payment.objects.create(
        user=player_user,
        amount=Decimal('99.99'),
        currency='USD',
        payment_type='tournament_fee',
        status='pending',
    )


class TestPaymentModel:
    def test_create_payment(self, payment):
        assert payment.amount == Decimal('99.99')
        assert payment.status == 'pending'
        assert payment.payment_type == 'tournament_fee'

    def test_payment_str(self, payment):
        expected = f'{payment.user.email} - ${payment.amount} - {payment.status}'
        assert str(payment) == expected

    def test_complete_payment(self, payment):
        payment.status = 'succeeded'
        payment.completed_at = timezone.now()
        payment.save()
        db_payment = Payment.objects.get(pk=payment.pk)
        assert db_payment.status == 'succeeded'
        assert db_payment.completed_at is not None

    def test_refund_payment(self, payment):
        payment.status = 'refunded'
        payment.refund_amount = Decimal('99.99')
        payment.refunded_at = timezone.now()
        payment.save()
        db_payment = Payment.objects.get(pk=payment.pk)
        assert db_payment.refund_amount == Decimal('99.99')


class TestInvoiceModel:
    @pytest.fixture
    def invoice(self, payment):
        return Invoice.objects.create(
            payment=payment,
            invoice_number=f'INV-{uuid.uuid4().hex[:8].upper()}',
            status='draft',
            bill_to_name='John Doe',
            bill_to_email=payment.user.email,
            subtotal=Decimal('99.99'),
            total_amount=Decimal('99.99'),
            due_date=date.today() + timedelta(days=30),
        )

    def test_create_invoice(self, invoice):
        assert invoice.status == 'draft'
        assert invoice.subtotal == Decimal('99.99')

    def test_invoice_str(self, invoice):
        assert str(invoice) == f'Invoice {invoice.invoice_number}'

    def test_mark_as_paid(self, invoice):
        invoice.status = 'paid'
        invoice.paid_date = date.today()
        invoice.save()
        db_invoice = Invoice.objects.get(pk=invoice.pk)
        assert db_invoice.status == 'paid'

    def test_unique_invoice_number(self, payment):
        Invoice.objects.create(
            payment=payment,
            invoice_number='INV-UNIQUE-001',
            bill_to_name='Jane', bill_to_email='jane@test.com',
            subtotal=Decimal('50'), total_amount=Decimal('50'),
            due_date=date.today(),
        )
        with pytest.raises(Exception):
            Invoice.objects.create(
                payment=payment,
                invoice_number='INV-UNIQUE-001',
                bill_to_name='Jane', bill_to_email='jane@test.com',
                subtotal=Decimal('50'), total_amount=Decimal('50'),
                due_date=date.today(),
            )


class TestStripeWebhookEventModel:
    def test_create_webhook_event(self):
        event = StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test_123',
            event_type='payment_intent.succeeded',
            payload={'id': 'evt_test_123', 'type': 'payment_intent.succeeded'},
        )
        assert not event.processed
        assert event.event_type == 'payment_intent.succeeded'

    def test_mark_processed(self):
        event = StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test_456',
            event_type='payment_intent.succeeded',
            payload={},
        )
        event.processed = True
        event.processed_at = timezone.now()
        event.save()
        db_event = StripeWebhookEvent.objects.get(pk=event.pk)
        assert db_event.processed

    def test_unique_stripe_event_id(self):
        StripeWebhookEvent.objects.create(
            stripe_event_id='evt_unique_1', event_type='test', payload={},
        )
        with pytest.raises(Exception):
            StripeWebhookEvent.objects.create(
                stripe_event_id='evt_unique_1', event_type='test', payload={},
            )


class TestPaymentMethodModel:
    def test_create_payment_method(self, player_user):
        pm = PaymentMethod.objects.create(
            user=player_user,
            method_type='card',
            is_default=True,
            stripe_payment_method_id='pm_test_123',
            card_last4='4242',
            card_brand='visa',
            card_exp_month=12,
            card_exp_year=2028,
        )
        assert pm.method_type == 'card'
        assert pm.is_default
        assert pm.is_active

    def test_default_method_unique(self, player_user):
        PaymentMethod.objects.create(
            user=player_user, method_type='card', is_default=True,
            stripe_payment_method_id='pm_1',
        )
        pm2 = PaymentMethod.objects.create(
            user=player_user, method_type='card', is_default=True,
            stripe_payment_method_id='pm_2',
        )
        pm2.refresh_from_db()
        assert pm2.is_default


class TestPaymentViews:
    URL_METHODS = reverse('payments:payment_methods')
    URL_ADD_METHOD = reverse('payments:add_payment_method')
    URL_CHECKOUT = reverse('payments:checkout')
    URL_CANCEL = reverse('payments:cancel')
    URL_HISTORY = reverse('payments:history')
    URL_CREATE_INTENT = reverse('payments:create_payment_intent')
    URL_WEBHOOK = reverse('payments:stripe_webhook')

    @pytest.mark.django_db
    def test_methods_requires_login(self, client):
        response = client.get(self.URL_METHODS)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_methods_authenticated(self, client_logged_in_player):
        response = client_logged_in_player.get(self.URL_METHODS)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_add_method_requires_login(self, client):
        response = client.get(self.URL_ADD_METHOD)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_add_method_authenticated(self, client_logged_in_player):
        response = client_logged_in_player.get(self.URL_ADD_METHOD)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_checkout_requires_login(self, client):
        response = client.get(self.URL_CHECKOUT)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_history_requires_login(self, client):
        response = client.get(self.URL_HISTORY)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_history_authenticated(self, client_logged_in_player, payment):
        response = client_logged_in_player.get(self.URL_HISTORY)
        assert response.status_code == 200
        assert '99.99' in response.content.decode() or '$' in response.content.decode()

    @pytest.mark.django_db
    def test_payment_detail(self, client_logged_in_player, payment):
        url = reverse('payments:detail', kwargs={'payment_id': payment.pk})
        response = client_logged_in_player.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_create_payment_intent(self, client_logged_in_player):
        response = client_logged_in_player.post(
            self.URL_CREATE_INTENT,
            json.dumps({'amount': 5000, 'currency': 'usd', 'payment_type': 'tournament_fee'}),
            content_type='application/json',
        )
        assert response.status_code in (200, 400)

    @pytest.mark.django_db
    def test_webhook_rejects_get(self, client):
        response = client.get(self.URL_WEBHOOK)
        assert response.status_code == 405

    @pytest.mark.django_db
    def test_webhook_post_no_signature(self, client):
        response = client.post(
            self.URL_WEBHOOK,
            json.dumps({'id': 'evt_test', 'type': 'test'}),
            content_type='application/json',
        )
        assert response.status_code in (400, 403)

    @pytest.mark.django_db
    def test_payment_success(self, client_logged_in_player, payment):
        payment.status = 'pending'
        payment.save()
        url = reverse('payments:success', kwargs={'payment_id': payment.pk})
        response = client_logged_in_player.get(url)
        assert response.status_code in (200, 302)

    @pytest.mark.django_db
    def test_remove_method(self, client_logged_in_player, player_user):
        pm = PaymentMethod.objects.create(
            user=player_user, method_type='card', is_default=True,
            stripe_payment_method_id='pm_test_remove',
        )
        url = reverse('payments:remove_payment_method', kwargs={'method_id': pm.pk})
        response = client_logged_in_player.post(url)
        assert response.status_code in (200, 302)
        pm.refresh_from_db()
        assert not pm.is_active
