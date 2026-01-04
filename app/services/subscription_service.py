"""
Subscription Service
Handles subscription lifecycle, trials, billing, and payment method management
"""
from datetime import datetime, timedelta
from decimal import Decimal
import json
import uuid
from typing import Optional, Dict, Any, Tuple

from app import db
from app.models import Restaurant
from app.models.website_content_models import (
    PricingPlan, Subscription, SubscriptionEvent, ScheduledBillingJob,
    PaymentGateway, PaymentTransaction, SubscriptionStatus
)


class SubscriptionService:
    """Core subscription management service"""

    # ===========================================
    # SUBSCRIPTION CREATION
    # ===========================================

    @staticmethod
    def create_subscription_with_trial(
        restaurant_id: int,
        plan_id: int,
        payment_method_token: str,
        payment_gateway: str,
        payment_method_details: Dict[str, str],
        country_code: str,
        consent_ip: str,
        terms_version: str = 'v1.0',
        consent_method: str = 'checkbox'
    ) -> Tuple[Optional[Subscription], Optional[str]]:
        """
        Create a new subscription with trial period.
        No charge is made immediately - payment method is stored for future billing.

        Args:
            restaurant_id: The restaurant ID
            plan_id: The pricing plan ID
            payment_method_token: Tokenized payment method from gateway
            payment_gateway: Gateway name (stripe, paypal, etc.)
            payment_method_details: Dict with last4, brand, expiry
            country_code: Country code for tier-based pricing
            consent_ip: IP address for consent record
            terms_version: Version of terms accepted
            consent_method: How consent was given (checkbox, button)

        Returns:
            Tuple of (Subscription, None) on success or (None, error_message) on failure
        """
        # Validate restaurant exists
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return None, "Restaurant not found"

        # Validate plan exists and is active
        plan = PricingPlan.query.get(plan_id)
        if not plan or not plan.is_active:
            return None, "Invalid or inactive pricing plan"

        # Check for existing active subscription
        existing = Subscription.query.filter(
            Subscription.restaurant_id == restaurant_id,
            Subscription.status.in_([
                SubscriptionStatus.TRIALING,
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.PAYMENT_PENDING
            ])
        ).first()

        if existing:
            return None, "Restaurant already has an active subscription"

        # Get price for country
        billing_amount = plan.get_price_for_country(country_code)

        # Determine trial period
        trial_days = plan.trial_days if plan.trial_enabled else 0
        now = datetime.utcnow()

        # Create subscription
        subscription = Subscription(
            public_id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            pricing_plan_id=plan_id,
            status=SubscriptionStatus.TRIALING if trial_days > 0 else SubscriptionStatus.ACTIVE,

            # Trial dates
            trial_start_date=now if trial_days > 0 else None,
            trial_end_date=now + timedelta(days=trial_days) if trial_days > 0 else None,

            # Billing period (starts after trial)
            current_period_start=now if trial_days == 0 else None,
            current_period_end=(now + timedelta(days=30 if plan.price_period == 'month' else 365)) if trial_days == 0 else None,
            next_billing_date=now + timedelta(days=trial_days) if trial_days > 0 else now + timedelta(days=30 if plan.price_period == 'month' else 365),

            # Payment method (tokenized)
            payment_method_id=payment_method_token,
            payment_gateway=payment_gateway,
            payment_method_last4=payment_method_details.get('last4'),
            payment_method_brand=payment_method_details.get('brand'),
            payment_method_expiry=payment_method_details.get('expiry'),

            # Billing details
            billing_country_code=country_code,
            billing_currency=plan.currency,
            billing_amount=Decimal(str(billing_amount)),
            billing_interval=plan.price_period,

            # Consent
            consent_timestamp=now,
            consent_ip_address=consent_ip,
            terms_version=terms_version,
            consent_method=consent_method
        )

        db.session.add(subscription)
        db.session.flush()  # Get ID

        # Update restaurant reference
        restaurant.pricing_plan_id = plan_id
        restaurant.is_trial = trial_days > 0
        restaurant.trial_ends_at = subscription.trial_end_date
        restaurant.subscription_start_date = now
        restaurant.subscription_end_date = subscription.current_period_end or subscription.trial_end_date

        # Log event
        SubscriptionService._log_event(
            subscription.id,
            'trial_started' if trial_days > 0 else 'created',
            {
                'plan_name': plan.name,
                'trial_days': trial_days,
                'billing_amount': float(billing_amount),
                'currency': plan.currency
            },
            triggered_by='user',
            ip_address=consent_ip
        )

        # Schedule billing jobs
        if trial_days > 0:
            # Reminder 2 days before trial ends
            if trial_days > 2:
                SubscriptionService._schedule_job(
                    subscription.id,
                    'trial_ending_reminder',
                    subscription.trial_end_date - timedelta(days=2),
                    {'days_remaining': 2}
                )

            # Trial end charge
            SubscriptionService._schedule_job(
                subscription.id,
                'trial_end_charge',
                subscription.trial_end_date,
                {'amount': float(billing_amount), 'currency': plan.currency}
            )
        else:
            # For non-trial, charge immediately
            charge_result = SubscriptionService.process_charge(subscription.id)
            if not charge_result['success']:
                # Rollback
                db.session.rollback()
                return None, charge_result.get('error', 'Payment failed')

        db.session.commit()
        return subscription, None

    @staticmethod
    def create_free_subscription(restaurant_id: int, plan_id: int) -> Tuple[Optional[Subscription], Optional[str]]:
        """Create a subscription for a free plan (no payment method required)"""
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return None, "Restaurant not found"

        plan = PricingPlan.query.get(plan_id)
        if not plan or not plan.is_active:
            return None, "Invalid or inactive pricing plan"

        if float(plan.price) > 0:
            return None, "This plan requires payment"

        now = datetime.utcnow()

        subscription = Subscription(
            public_id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            pricing_plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            billing_amount=Decimal('0'),
            billing_currency=plan.currency,
            billing_interval=plan.price_period
        )

        db.session.add(subscription)

        # Update restaurant
        restaurant.pricing_plan_id = plan_id
        restaurant.is_trial = False
        restaurant.subscription_start_date = now

        SubscriptionService._log_event(
            subscription.id,
            'created',
            {'plan_name': plan.name, 'type': 'free'},
            triggered_by='user'
        )

        db.session.commit()
        return subscription, None

    # ===========================================
    # PAYMENT PROCESSING
    # ===========================================

    @staticmethod
    def process_charge(subscription_id: int) -> Dict[str, Any]:
        """
        Process a charge for the subscription.
        This is called at trial end or renewal.

        Returns dict with 'success' boolean and either 'transaction' or 'error'
        """
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return {'success': False, 'error': 'Subscription not found'}

        if not subscription.payment_method_id:
            return {'success': False, 'error': 'No payment method on file'}

        plan = subscription.pricing_plan
        gateway = PaymentGateway.query.filter_by(
            name=subscription.payment_gateway,
            is_active=True
        ).first()

        if not gateway:
            return {'success': False, 'error': 'Payment gateway not configured'}

        amount = float(subscription.billing_amount)
        currency = subscription.billing_currency

        # Create transaction record
        transaction = PaymentTransaction(
            transaction_id=str(uuid.uuid4()),
            gateway_name=subscription.payment_gateway,
            user_id=subscription.restaurant.owner_id,
            restaurant_id=subscription.restaurant_id,
            amount=amount,
            currency=currency,
            status='pending',
            pricing_plan_id=subscription.pricing_plan_id,
            subscription_months=1 if subscription.billing_interval == 'month' else 12
        )
        db.session.add(transaction)
        db.session.flush()

        # Attempt charge via gateway
        charge_result = SubscriptionService._execute_gateway_charge(
            gateway,
            subscription.payment_method_id,
            amount,
            currency,
            {
                'subscription_id': subscription.public_id,
                'restaurant_id': subscription.restaurant_id,
                'plan_name': plan.name
            }
        )

        subscription.last_payment_attempt = datetime.utcnow()

        if charge_result['success']:
            # Update transaction
            transaction.status = 'completed'
            transaction.completed_at = datetime.utcnow()
            transaction.gateway_response = json.dumps(charge_result.get('gateway_response', {}))

            # Update subscription
            now = datetime.utcnow()
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.current_period_start = now

            if subscription.billing_interval == 'month':
                subscription.current_period_end = now + timedelta(days=30)
            else:
                subscription.current_period_end = now + timedelta(days=365)

            subscription.next_billing_date = subscription.current_period_end
            subscription.failed_payment_count = 0
            subscription.next_retry_date = None
            subscription.grace_period_end = None

            # Update restaurant
            subscription.restaurant.subscription_start_date = now
            subscription.restaurant.subscription_end_date = subscription.current_period_end
            subscription.restaurant.is_trial = False

            # Log event
            SubscriptionService._log_event(
                subscription_id,
                'charged',
                {
                    'amount': amount,
                    'currency': currency,
                    'transaction_id': transaction.transaction_id
                },
                triggered_by='system'
            )

            # Schedule next renewal
            SubscriptionService._schedule_job(
                subscription_id,
                'renewal',
                subscription.next_billing_date,
                {'amount': amount, 'currency': currency}
            )

            db.session.commit()
            return {'success': True, 'transaction': transaction.to_dict()}

        else:
            # Payment failed
            transaction.status = 'failed'
            transaction.error_message = charge_result.get('error', 'Unknown error')
            transaction.gateway_response = json.dumps(charge_result.get('gateway_response', {}))

            subscription.failed_payment_count += 1
            subscription.status = SubscriptionStatus.PAYMENT_FAILED

            # Set up retry
            retry_interval = timedelta(hours=plan.retry_interval_hours)
            subscription.next_retry_date = datetime.utcnow() + retry_interval

            # Set grace period
            if not subscription.grace_period_end:
                subscription.grace_period_end = datetime.utcnow() + timedelta(days=plan.grace_period_days)

            # Log event
            SubscriptionService._log_event(
                subscription_id,
                'payment_failed',
                {
                    'amount': amount,
                    'currency': currency,
                    'error': charge_result.get('error'),
                    'attempt': subscription.failed_payment_count
                },
                triggered_by='system'
            )

            # Schedule retry if under max attempts
            if subscription.failed_payment_count < plan.max_retry_attempts:
                SubscriptionService._schedule_job(
                    subscription_id,
                    'retry',
                    subscription.next_retry_date,
                    {
                        'amount': amount,
                        'currency': currency,
                        'attempt': subscription.failed_payment_count + 1
                    }
                )
            else:
                # Max retries reached - suspend
                subscription.status = SubscriptionStatus.SUSPENDED
                subscription.ended_at = datetime.utcnow()

                SubscriptionService._log_event(
                    subscription_id,
                    'suspended',
                    {'reason': 'Max payment retries exceeded'},
                    triggered_by='system'
                )

            db.session.commit()
            return {
                'success': False,
                'error': charge_result.get('error', 'Payment failed'),
                'retry_scheduled': subscription.failed_payment_count < plan.max_retry_attempts
            }

    @staticmethod
    def _execute_gateway_charge(
        gateway: PaymentGateway,
        payment_method_id: str,
        amount: float,
        currency: str,
        metadata: Dict
    ) -> Dict[str, Any]:
        """
        Execute charge through payment gateway.
        This is the abstraction point for different payment providers.

        In production, implement actual gateway API calls here.
        Currently uses sandbox simulation.
        """
        credentials = gateway.get_active_credentials()

        if gateway.is_sandbox:
            # Simulate charge in sandbox mode
            # For testing: amounts ending in .99 fail, others succeed
            if str(amount).endswith('.99'):
                return {
                    'success': False,
                    'error': 'Card declined (sandbox test)',
                    'gateway_response': {'sandbox': True, 'simulated': True}
                }
            return {
                'success': True,
                'gateway_response': {
                    'sandbox': True,
                    'simulated': True,
                    'charge_id': f'ch_sandbox_{uuid.uuid4().hex[:12]}'
                }
            }

        # Production gateway implementations would go here
        if gateway.name == 'stripe':
            return SubscriptionService._charge_stripe(credentials, payment_method_id, amount, currency, metadata)
        elif gateway.name == 'paypal':
            return SubscriptionService._charge_paypal(credentials, payment_method_id, amount, currency, metadata)
        else:
            return {'success': False, 'error': f'Unsupported gateway: {gateway.name}'}

    @staticmethod
    def _charge_stripe(credentials: Dict, payment_method_id: str, amount: float, currency: str, metadata: Dict) -> Dict:
        """Stripe charge implementation placeholder"""
        # In production: Use stripe library to charge
        # import stripe
        # stripe.api_key = credentials['secret_key']
        # try:
        #     intent = stripe.PaymentIntent.create(
        #         amount=int(amount * 100),  # Stripe uses cents
        #         currency=currency.lower(),
        #         payment_method=payment_method_id,
        #         confirm=True,
        #         metadata=metadata
        #     )
        #     return {'success': True, 'gateway_response': intent}
        # except stripe.error.CardError as e:
        #     return {'success': False, 'error': str(e), 'gateway_response': e.json_body}
        return {'success': True, 'gateway_response': {'simulated': True, 'note': 'Stripe not configured'}}

    @staticmethod
    def _charge_paypal(credentials: Dict, payment_method_id: str, amount: float, currency: str, metadata: Dict) -> Dict:
        """PayPal charge implementation placeholder"""
        # In production: Use PayPal SDK
        return {'success': True, 'gateway_response': {'simulated': True, 'note': 'PayPal not configured'}}

    # ===========================================
    # CANCELLATION
    # ===========================================

    @staticmethod
    def cancel_subscription(
        subscription_id: int,
        reason: Optional[str] = None,
        immediate: bool = False,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID
            reason: Optional cancellation reason
            immediate: If True, cancel immediately; if False, cancel at period end
            user_id: ID of user performing cancellation
            ip_address: IP address for audit

        Returns:
            Tuple of (success, message)
        """
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return False, "Subscription not found"

        if not subscription.can_cancel():
            return False, f"Cannot cancel subscription in {subscription.status} status"

        now = datetime.utcnow()
        plan = subscription.pricing_plan

        # Determine cancellation behavior
        if subscription.status == SubscriptionStatus.TRIALING:
            # During trial - always immediate, no charge
            immediate = True if plan.cancellation_behavior == 'immediate' else False

        subscription.cancelled_at = now
        subscription.cancellation_reason = reason

        if immediate or subscription.status == SubscriptionStatus.TRIALING:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.ended_at = now
            subscription.cancel_at_period_end = False

            # Update restaurant
            subscription.restaurant.is_trial = False
            subscription.restaurant.subscription_end_date = now

            message = "Subscription cancelled immediately"
        else:
            subscription.cancel_at_period_end = True
            access_until = subscription.current_period_end or subscription.trial_end_date
            message = f"Subscription will end on {access_until.strftime('%Y-%m-%d')}"

        # Cancel pending billing jobs
        ScheduledBillingJob.query.filter(
            ScheduledBillingJob.subscription_id == subscription_id,
            ScheduledBillingJob.status == 'pending'
        ).update({'status': 'cancelled'})

        # Log event
        SubscriptionService._log_event(
            subscription_id,
            'cancelled',
            {
                'reason': reason,
                'immediate': immediate,
                'access_until': subscription.ended_at.isoformat() if subscription.ended_at else (subscription.current_period_end.isoformat() if subscription.current_period_end else None)
            },
            triggered_by='user' if user_id else 'system',
            user_id=user_id,
            ip_address=ip_address
        )

        db.session.commit()
        return True, message

    @staticmethod
    def reactivate_subscription(subscription_id: int, user_id: Optional[int] = None) -> Tuple[bool, str]:
        """Reactivate a cancelled subscription (if within current period)"""
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return False, "Subscription not found"

        if subscription.status != SubscriptionStatus.CANCELLED and not subscription.cancel_at_period_end:
            return False, "Subscription is not cancelled"

        # Check if still within period
        now = datetime.utcnow()
        end_date = subscription.current_period_end or subscription.trial_end_date

        if end_date and now > end_date:
            return False, "Subscription period has ended. Please create a new subscription."

        # Reactivate
        if subscription.trial_end_date and now < subscription.trial_end_date:
            subscription.status = SubscriptionStatus.TRIALING
        else:
            subscription.status = SubscriptionStatus.ACTIVE

        subscription.cancel_at_period_end = False
        subscription.cancelled_at = None
        subscription.cancellation_reason = None

        SubscriptionService._log_event(
            subscription_id,
            'reactivated',
            {},
            triggered_by='user' if user_id else 'system',
            user_id=user_id
        )

        db.session.commit()
        return True, "Subscription reactivated successfully"

    # ===========================================
    # PAYMENT METHOD MANAGEMENT
    # ===========================================

    @staticmethod
    def update_payment_method(
        subscription_id: int,
        payment_method_token: str,
        payment_gateway: str,
        details: Dict[str, str],
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Update the payment method for a subscription"""
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return False, "Subscription not found"

        old_last4 = subscription.payment_method_last4

        subscription.payment_method_id = payment_method_token
        subscription.payment_gateway = payment_gateway
        subscription.payment_method_last4 = details.get('last4')
        subscription.payment_method_brand = details.get('brand')
        subscription.payment_method_expiry = details.get('expiry')

        SubscriptionService._log_event(
            subscription_id,
            'payment_method_updated',
            {
                'old_last4': old_last4,
                'new_last4': details.get('last4'),
                'brand': details.get('brand')
            },
            triggered_by='user' if user_id else 'system',
            user_id=user_id,
            ip_address=ip_address
        )

        db.session.commit()
        return True, "Payment method updated successfully"

    # ===========================================
    # PLAN CHANGES
    # ===========================================

    @staticmethod
    def change_plan(
        subscription_id: int,
        new_plan_id: int,
        user_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Change subscription to a different plan"""
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return False, "Subscription not found"

        if subscription.status not in [SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE]:
            return False, "Can only change plans on active subscriptions"

        old_plan = subscription.pricing_plan
        new_plan = PricingPlan.query.get(new_plan_id)

        if not new_plan or not new_plan.is_active:
            return False, "Invalid or inactive plan"

        # Calculate new billing amount
        new_amount = new_plan.get_price_for_country(subscription.billing_country_code)
        old_amount = float(subscription.billing_amount) if subscription.billing_amount else 0

        is_upgrade = new_amount > old_amount

        subscription.pricing_plan_id = new_plan_id
        subscription.billing_amount = Decimal(str(new_amount))
        subscription.billing_interval = new_plan.price_period

        # Update restaurant
        subscription.restaurant.pricing_plan_id = new_plan_id

        SubscriptionService._log_event(
            subscription_id,
            'upgraded' if is_upgrade else 'downgraded',
            {
                'old_plan': old_plan.name,
                'new_plan': new_plan.name,
                'old_amount': old_amount,
                'new_amount': new_amount
            },
            triggered_by='user' if user_id else 'system',
            user_id=user_id
        )

        db.session.commit()
        return True, f"Plan changed to {new_plan.name}"

    # ===========================================
    # QUERIES
    # ===========================================

    @staticmethod
    def get_active_subscription(restaurant_id: int) -> Optional[Subscription]:
        """Get the active subscription for a restaurant"""
        return Subscription.query.filter(
            Subscription.restaurant_id == restaurant_id,
            Subscription.status.in_([
                SubscriptionStatus.TRIALING,
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.PAYMENT_PENDING,
                SubscriptionStatus.PAYMENT_FAILED
            ])
        ).first()

    @staticmethod
    def get_subscription_by_public_id(public_id: str) -> Optional[Subscription]:
        """Get subscription by public ID"""
        return Subscription.query.filter_by(public_id=public_id).first()

    @staticmethod
    def get_subscriptions_due_for_billing(limit: int = 100) -> list:
        """Get subscriptions that need billing (trial end or renewal)"""
        now = datetime.utcnow()
        return Subscription.query.filter(
            Subscription.status.in_([SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE]),
            Subscription.next_billing_date <= now,
            Subscription.cancel_at_period_end == False
        ).limit(limit).all()

    @staticmethod
    def get_subscriptions_for_retry() -> list:
        """Get subscriptions that need payment retry"""
        now = datetime.utcnow()
        return Subscription.query.filter(
            Subscription.status == SubscriptionStatus.PAYMENT_FAILED,
            Subscription.next_retry_date <= now,
            Subscription.grace_period_end > now
        ).all()

    @staticmethod
    def get_expired_grace_periods() -> list:
        """Get subscriptions with expired grace periods that should be suspended"""
        now = datetime.utcnow()
        return Subscription.query.filter(
            Subscription.status == SubscriptionStatus.PAYMENT_FAILED,
            Subscription.grace_period_end <= now
        ).all()

    # ===========================================
    # HELPERS
    # ===========================================

    @staticmethod
    def _log_event(
        subscription_id: int,
        event_type: str,
        event_data: Dict,
        triggered_by: str = 'system',
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log a subscription event"""
        event = SubscriptionEvent(
            subscription_id=subscription_id,
            event_type=event_type,
            event_data=json.dumps(event_data),
            triggered_by=triggered_by,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        db.session.add(event)

    @staticmethod
    def _schedule_job(
        subscription_id: int,
        job_type: str,
        scheduled_for: datetime,
        job_data: Dict,
        max_attempts: int = 1
    ):
        """Schedule a billing job"""
        job = ScheduledBillingJob(
            subscription_id=subscription_id,
            job_type=job_type,
            scheduled_for=scheduled_for,
            job_data=json.dumps(job_data),
            max_attempts=max_attempts,
            status='pending'
        )
        db.session.add(job)

    @staticmethod
    def check_subscription_access(restaurant_id: int) -> Dict[str, Any]:
        """
        Check subscription status and access level for a restaurant.

        Returns dict with:
            - has_access: bool
            - access_level: 'full', 'limited', 'free', 'none'
            - subscription: subscription dict or None
            - message: status message
        """
        subscription = SubscriptionService.get_active_subscription(restaurant_id)

        if not subscription:
            return {
                'has_access': False,
                'access_level': 'free',
                'subscription': None,
                'message': 'No active subscription'
            }

        status_access = {
            SubscriptionStatus.TRIALING: ('full', True, f'Trial: {subscription.days_until_trial_end} days remaining'),
            SubscriptionStatus.ACTIVE: ('full', True, 'Active subscription'),
            SubscriptionStatus.PAYMENT_PENDING: ('full', True, 'Payment pending'),
            SubscriptionStatus.PAYMENT_FAILED: ('limited', True, 'Payment failed - please update payment method'),
            SubscriptionStatus.SUSPENDED: ('none', False, 'Subscription suspended'),
            SubscriptionStatus.CANCELLED: ('limited', subscription.cancel_at_period_end, 'Subscription cancelled'),
            SubscriptionStatus.EXPIRED: ('free', False, 'Subscription expired'),
        }

        access_level, has_access, message = status_access.get(
            subscription.status,
            ('free', False, 'Unknown status')
        )

        return {
            'has_access': has_access,
            'access_level': access_level,
            'subscription': subscription.to_dict(),
            'message': message
        }


class BillingJobProcessor:
    """Process scheduled billing jobs"""

    @staticmethod
    def process_due_jobs():
        """Process all due billing jobs"""
        now = datetime.utcnow()

        jobs = ScheduledBillingJob.query.filter(
            ScheduledBillingJob.status == 'pending',
            ScheduledBillingJob.scheduled_for <= now
        ).all()

        results = []
        for job in jobs:
            result = BillingJobProcessor.process_job(job)
            results.append(result)

        return results

    @staticmethod
    def process_job(job: ScheduledBillingJob) -> Dict[str, Any]:
        """Process a single billing job"""
        job.status = 'processing'
        job.attempts += 1
        job.last_attempt_at = datetime.utcnow()
        db.session.commit()

        try:
            if job.job_type == 'trial_end_charge':
                result = BillingJobProcessor._process_trial_end(job)
            elif job.job_type == 'renewal':
                result = BillingJobProcessor._process_renewal(job)
            elif job.job_type == 'retry':
                result = BillingJobProcessor._process_retry(job)
            elif job.job_type == 'trial_ending_reminder':
                result = BillingJobProcessor._send_trial_reminder(job)
            else:
                result = {'success': False, 'error': f'Unknown job type: {job.job_type}'}

            if result['success']:
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
            else:
                if job.attempts >= job.max_attempts:
                    job.status = 'failed'
                else:
                    job.status = 'pending'  # Will retry
                job.error_message = result.get('error')

            job.result_data = json.dumps(result)
            db.session.commit()
            return result

        except Exception as e:
            job.status = 'failed' if job.attempts >= job.max_attempts else 'pending'
            job.error_message = str(e)
            db.session.commit()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _process_trial_end(job: ScheduledBillingJob) -> Dict:
        """Process trial end - charge the customer"""
        subscription = job.subscription

        if subscription.status != SubscriptionStatus.TRIALING:
            return {'success': True, 'message': 'Subscription no longer in trial'}

        if subscription.cancel_at_period_end:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.ended_at = datetime.utcnow()
            db.session.commit()
            return {'success': True, 'message': 'Trial ended, subscription cancelled'}

        return SubscriptionService.process_charge(subscription.id)

    @staticmethod
    def _process_renewal(job: ScheduledBillingJob) -> Dict:
        """Process subscription renewal"""
        subscription = job.subscription

        if subscription.status != SubscriptionStatus.ACTIVE:
            return {'success': True, 'message': 'Subscription not active'}

        if subscription.cancel_at_period_end:
            subscription.status = SubscriptionStatus.EXPIRED
            subscription.ended_at = datetime.utcnow()
            db.session.commit()
            return {'success': True, 'message': 'Subscription expired (cancelled)'}

        return SubscriptionService.process_charge(subscription.id)

    @staticmethod
    def _process_retry(job: ScheduledBillingJob) -> Dict:
        """Process payment retry"""
        return SubscriptionService.process_charge(job.subscription_id)

    @staticmethod
    def _send_trial_reminder(job: ScheduledBillingJob) -> Dict:
        """Send trial ending reminder notification"""
        subscription = job.subscription

        if subscription.status != SubscriptionStatus.TRIALING:
            return {'success': True, 'message': 'Not in trial'}

        # Log the reminder event
        SubscriptionService._log_event(
            subscription.id,
            'trial_ending_soon',
            {
                'days_remaining': subscription.days_until_trial_end,
                'billing_amount': float(subscription.billing_amount) if subscription.billing_amount else 0,
                'billing_date': subscription.trial_end_date.isoformat() if subscription.trial_end_date else None
            },
            triggered_by='system'
        )

        # In production: Send actual notification (email, push, etc.)
        # NotificationService.send_trial_ending_reminder(subscription)

        return {'success': True, 'message': 'Reminder sent'}

