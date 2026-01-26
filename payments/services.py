"""
Stripe payment processing service
"""
import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from decimal import Decimal
from typing import Optional, Dict, Any
import logging

from .models import Payment, PaymentMethod, StripeWebhookEvent
from security.utils import log_audit_action

User = get_user_model()
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for handling Stripe payment operations"""
    
    @staticmethod
    def get_or_create_customer(user: User) -> str:
        """
        Get existing Stripe customer or create a new one
        
        Args:
            user: User instance
            
        Returns:
            Stripe customer ID
        """
        if user.stripe_customer_id:
            try:
                # Verify customer still exists
                stripe.Customer.retrieve(user.stripe_customer_id)
                return user.stripe_customer_id
            except stripe.error.InvalidRequestError:
                # Customer doesn't exist, create new one
                pass
        
        # Create new customer
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.get_full_name(),
                metadata={
                    'user_id': str(user.id),
                    'username': user.username,
                }
            )
            
            user.stripe_customer_id = customer.id
            user.save(update_fields=['stripe_customer_id'])
            
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise
    
    @staticmethod
    def create_payment_intent(
        user: User,
        amount: Decimal,
        currency: str = 'usd',
        payment_type: str = 'other',
        description: str = '',
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[Payment, stripe.PaymentIntent]:
        """
        Create a Stripe PaymentIntent and corresponding Payment record
        
        Args:
            user: User making the payment
            amount: Payment amount
            currency: Currency code (default: 'usd')
            payment_type: Type of payment
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            Tuple of (Payment instance, Stripe PaymentIntent)
        """
        try:
            # Get or create Stripe customer
            customer_id = StripeService.get_or_create_customer(user)
            
            # Calculate amount in cents
            amount_cents = int(amount * 100)
            
            # Prepare metadata
            payment_metadata = metadata or {}
            payment_metadata.update({
                'user_id': str(user.id),
                'payment_type': payment_type,
            })
            
            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                customer=customer_id,
                description=description,
                metadata=payment_metadata,
                automatic_payment_methods={'enabled': True},
            )
            
            # Create Payment record
            payment = Payment.objects.create(
                user=user,
                amount=amount,
                currency=currency.upper(),
                payment_type=payment_type,
                status='pending',
                description=description,
                stripe_payment_intent_id=intent.id,
                stripe_customer_id=customer_id,
                metadata=payment_metadata
            )
            
            logger.info(f"Created payment intent {intent.id} for user {user.id}")
            
            return payment, intent
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise
    
    @staticmethod
    def confirm_payment(payment: Payment) -> bool:
        """
        Confirm a payment after successful PaymentIntent
        
        Args:
            payment: Payment instance
            
        Returns:
            True if successful
        """
        try:
            # Retrieve PaymentIntent
            intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
            
            if intent.status == 'succeeded':
                # Get charge details
                if intent.charges and intent.charges.data:
                    charge = intent.charges.data[0]
                    payment.stripe_charge_id = charge.id
                    
                    # Calculate fees
                    if charge.balance_transaction:
                        balance_txn = stripe.BalanceTransaction.retrieve(
                            charge.balance_transaction
                        )
                        payment.stripe_fee = Decimal(balance_txn.fee) / 100
                
                payment.mark_succeeded()
                
                logger.info(f"Payment {payment.id} confirmed successfully")
                return True
            
            return False
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to confirm payment: {e}")
            return False
    
    @staticmethod
    def refund_payment(
        payment: Payment,
        amount: Optional[Decimal] = None,
        reason: str = ''
    ) -> bool:
        """
        Refund a payment (full or partial)
        
        Args:
            payment: Payment to refund
            amount: Amount to refund (None for full refund)
            reason: Reason for refund
            
        Returns:
            True if successful
        """
        if not payment.is_refundable:
            logger.warning(f"Payment {payment.id} is not refundable")
            return False
        
        try:
            # Calculate refund amount (full refund only for now)
            refund_amount = amount or payment.amount
            refund_cents = int(refund_amount * 100)
            
            # Create refund
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=refund_cents,
                reason='requested_by_customer',
                metadata={'reason': reason}
            )
            
            # Update payment using process_refund method
            payment.process_refund(amount=refund_amount, reason=reason)
            
            logger.info(f"Refunded ${refund_amount} for payment {payment.id}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to refund payment: {e}")
            return False
    
    @staticmethod
    def add_payment_method(
        user: User,
        payment_method_id: str,
        set_as_default: bool = False
    ) -> Optional[PaymentMethod]:
        """
        Attach a payment method to a customer
        
        Args:
            user: User instance
            payment_method_id: Stripe PaymentMethod ID
            set_as_default: Whether to set as default
            
        Returns:
            PaymentMethod instance or None
        """
        try:
            # Get or create customer
            customer_id = StripeService.get_or_create_customer(user)
            
            # Attach payment method to customer
            stripe_pm = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            
            # Set as default if requested
            if set_as_default:
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={'default_payment_method': payment_method_id}
                )
            
            # Create PaymentMethod record
            payment_method = PaymentMethod.objects.create(
                user=user,
                method_type='card',  # Assuming card for now
                stripe_payment_method_id=payment_method_id,
                is_default=set_as_default
            )
            
            # Update card details if it's a card
            if stripe_pm.type == 'card':
                card = stripe_pm.card
                payment_method.card_brand = card.brand
                payment_method.card_last4 = card.last4
                payment_method.card_exp_month = card.exp_month
                payment_method.card_exp_year = card.exp_year
                payment_method.save()
            
            logger.info(f"Added payment method {payment_method_id} for user {user.id}")
            return payment_method
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to add payment method: {e}")
            return None
    
    @staticmethod
    def remove_payment_method(payment_method: PaymentMethod) -> bool:
        """
        Detach a payment method from customer
        
        Args:
            payment_method: PaymentMethod instance
            
        Returns:
            True if successful
        """
        try:
            stripe.PaymentMethod.detach(payment_method.stripe_payment_method_id)
            payment_method.is_active = False
            payment_method.save()
            
            logger.info(f"Removed payment method {payment_method.id}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to remove payment method: {e}")
            return False
    
    @staticmethod
    def list_payment_methods(user: User) -> list:
        """
        List all payment methods for a user
        
        Args:
            user: User instance
            
        Returns:
            List of Stripe PaymentMethod objects
        """
        if not user.stripe_customer_id:
            return []
        
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=user.stripe_customer_id,
                type='card',
            )
            return payment_methods.data
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {e}")
            return []
    
    @staticmethod
    def create_setup_intent(user: User) -> Optional[stripe.SetupIntent]:
        """
        Create a SetupIntent for saving payment method without charging
        
        Args:
            user: User instance
            
        Returns:
            Stripe SetupIntent or None
        """
        try:
            customer_id = StripeService.get_or_create_customer(user)
            
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=['card'],
            )
            
            return setup_intent
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create setup intent: {e}")
            return None


class WebhookHandler:
    """Handle Stripe webhook events"""
    
    @staticmethod
    def handle_event(event_data: Dict[str, Any]) -> bool:
        """
        Process a Stripe webhook event
        
        Args:
            event_data: Stripe event data
            
        Returns:
            True if processed successfully
        """
        event_id = event_data.get('id')
        event_type = event_data.get('type')
        
        # Check if already processed
        if StripeWebhookEvent.objects.filter(stripe_event_id=event_id).exists():
            logger.info(f"Event {event_id} already processed")
            return True
        
        # Create webhook event record
        webhook_event = StripeWebhookEvent.objects.create(
            stripe_event_id=event_id,
            event_type=event_type,
            payload=event_data
        )
        
        try:
            # Route to appropriate handler
            handler_map = {
                'payment_intent.succeeded': WebhookHandler.handle_payment_succeeded,
                'payment_intent.payment_failed': WebhookHandler.handle_payment_failed,
                'payment_intent.canceled': WebhookHandler.handle_payment_canceled,
                'charge.refunded': WebhookHandler.handle_charge_refunded,
                'customer.subscription.created': WebhookHandler.handle_subscription_created,
                'customer.subscription.deleted': WebhookHandler.handle_subscription_deleted,
            }
            
            handler = handler_map.get(event_type)
            if handler:
                success = handler(event_data, webhook_event)
                if success:
                    webhook_event.mark_processed()
                    return True
            else:
                logger.info(f"No handler for event type: {event_type}")
                webhook_event.mark_processed()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            webhook_event.mark_failed(str(e))
            return False
    
    @staticmethod
    def handle_payment_succeeded(event_data: Dict, webhook_event: StripeWebhookEvent) -> bool:
        """Handle successful payment"""
        payment_intent = event_data['data']['object']
        intent_id = payment_intent['id']
        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
            webhook_event.payment = payment
            webhook_event.save()
            
            # Confirm payment
            StripeService.confirm_payment(payment)
            
            logger.info(f"Payment {payment.id} succeeded")
            return True
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for intent {intent_id}")
            return False
    
    @staticmethod
    def handle_payment_failed(event_data: Dict, webhook_event: StripeWebhookEvent) -> bool:
        """Handle failed payment"""
        payment_intent = event_data['data']['object']
        intent_id = payment_intent['id']
        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
            webhook_event.payment = payment
            webhook_event.save()
            
            error_message = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
            payment.mark_failed(error_message)
            
            logger.info(f"Payment {payment.id} failed: {error_message}")
            return True
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for intent {intent_id}")
            return False
    
    @staticmethod
    def handle_payment_canceled(event_data: Dict, webhook_event: StripeWebhookEvent) -> bool:
        """Handle canceled payment"""
        payment_intent = event_data['data']['object']
        intent_id = payment_intent['id']
        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
            webhook_event.payment = payment
            webhook_event.save()
            
            payment.status = 'cancelled'
            payment.save()
            
            logger.info(f"Payment {payment.id} canceled")
            return True
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for intent {intent_id}")
            return False
    
    @staticmethod
    def handle_charge_refunded(event_data: Dict, webhook_event: StripeWebhookEvent) -> bool:
        """Handle charge refund"""
        charge = event_data['data']['object']
        charge_id = charge['id']
        
        try:
            payment = Payment.objects.get(stripe_charge_id=charge_id)
            webhook_event.payment = payment
            webhook_event.save()
            
            # Update refund amount
            refund_amount = Decimal(charge['amount_refunded']) / 100
            payment.refund_amount = refund_amount
            
            if refund_amount >= payment.amount:
                payment.status = 'refunded'
            else:
                payment.status = 'partially_refunded'
            
            payment.save()
            
            logger.info(f"Payment {payment.id} refunded: ${refund_amount}")
            return True
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for charge {charge_id}")
            return False
    
    @staticmethod
    def handle_subscription_created(event_data: Dict, webhook_event: StripeWebhookEvent) -> bool:
        """Handle subscription creation"""
        # TODO: Implement subscription handling
        logger.info("Subscription created (not yet implemented)")
        return True
    
    @staticmethod
    def handle_subscription_deleted(event_data: Dict, webhook_event: StripeWebhookEvent) -> bool:
        """Handle subscription deletion"""
        # TODO: Implement subscription handling
        logger.info("Subscription deleted (not yet implemented)")
        return True
