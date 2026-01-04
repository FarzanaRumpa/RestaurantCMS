"""
Payment Service
Handles payment processing for Stripe, PayPal, Google Pay, and Apple Pay
Supports tokenization and recurring payments
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class PaymentResult:
    """Standardized payment result object"""
    def __init__(self, success: bool, payment_method_id: str = None,
                 customer_id: str = None, subscription_id: str = None,
                 error: str = None, gateway: str = None,
                 last4: str = None, brand: str = None, expiry: str = None,
                 raw_response: dict = None):
        self.success = success
        self.payment_method_id = payment_method_id
        self.customer_id = customer_id
        self.subscription_id = subscription_id
        self.error = error
        self.gateway = gateway
        self.last4 = last4
        self.brand = brand
        self.expiry = expiry
        self.raw_response = raw_response or {}

    def to_dict(self):
        return {
            'success': self.success,
            'payment_method_id': self.payment_method_id,
            'customer_id': self.customer_id,
            'subscription_id': self.subscription_id,
            'error': self.error,
            'gateway': self.gateway,
            'last4': self.last4,
            'brand': self.brand,
            'expiry': self.expiry
        }


class PaymentService:
    """
    Unified payment service supporting multiple gateways.
    Google Pay and Apple Pay work through Stripe's Payment Request API.
    """

    def __init__(self):
        self._stripe = None
        self._paypal_access_token = None
        self._paypal_token_expiry = None

    def _get_gateway_config(self, gateway_name: str) -> Optional[Dict]:
        """Get gateway configuration from database"""
        from app.models.website_content_models import PaymentGateway
        gateway = PaymentGateway.query.filter_by(name=gateway_name, is_active=True).first()
        if not gateway:
            return None
        return {
            'gateway': gateway,
            'credentials': gateway.get_active_credentials(),
            'is_sandbox': gateway.is_sandbox
        }

    def get_available_gateways(self) -> list:
        """Get all active payment gateways for frontend"""
        from app.models.website_content_models import PaymentGateway
        gateways = PaymentGateway.query.filter_by(is_active=True).order_by(
            PaymentGateway.display_order
        ).all()
        return [g.to_public_dict() for g in gateways]

    # =========================================================================
    # STRIPE METHODS
    # =========================================================================

    def _init_stripe(self, secret_key: str):
        """Initialize Stripe with secret key"""
        try:
            import stripe
            stripe.api_key = secret_key
            self._stripe = stripe
            return True
        except ImportError:
            logger.error("Stripe library not installed. Run: pip install stripe")
            return False

    def stripe_create_setup_intent(self, customer_email: str, customer_name: str = None,
                                    metadata: dict = None) -> PaymentResult:
        """
        Create a Stripe SetupIntent for collecting payment method without immediate charge.
        This is used for trial subscriptions.
        """
        config = self._get_gateway_config('stripe')
        if not config:
            return PaymentResult(success=False, error="Stripe is not configured or inactive")

        creds = config['credentials']
        if not creds.get('secret_key'):
            return PaymentResult(success=False, error="Stripe secret key not configured")

        if not self._init_stripe(creds['secret_key']):
            return PaymentResult(success=False, error="Failed to initialize Stripe")

        try:
            # Create or retrieve customer
            customers = self._stripe.Customer.list(email=customer_email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer = self._stripe.Customer.create(
                    email=customer_email,
                    name=customer_name,
                    metadata=metadata or {}
                )

            # Create SetupIntent
            setup_intent = self._stripe.SetupIntent.create(
                customer=customer.id,
                payment_method_types=['card'],
                usage='off_session',  # Allow charging later without customer presence
                metadata=metadata or {}
            )

            return PaymentResult(
                success=True,
                customer_id=customer.id,
                payment_method_id=setup_intent.client_secret,  # Client secret for frontend
                gateway='stripe',
                raw_response={'setup_intent_id': setup_intent.id, 'customer_id': customer.id}
            )
        except Exception as e:
            logger.error(f"Stripe SetupIntent error: {str(e)}")
            return PaymentResult(success=False, error=str(e), gateway='stripe')

    def stripe_confirm_setup_intent(self, setup_intent_id: str) -> PaymentResult:
        """Confirm a SetupIntent and get the payment method details"""
        config = self._get_gateway_config('stripe')
        if not config:
            return PaymentResult(success=False, error="Stripe is not configured")

        if not self._init_stripe(config['credentials'].get('secret_key')):
            return PaymentResult(success=False, error="Failed to initialize Stripe")

        try:
            setup_intent = self._stripe.SetupIntent.retrieve(setup_intent_id)

            if setup_intent.status != 'succeeded':
                return PaymentResult(success=False, error=f"SetupIntent not successful: {setup_intent.status}")

            # Get payment method details
            pm = self._stripe.PaymentMethod.retrieve(setup_intent.payment_method)

            return PaymentResult(
                success=True,
                payment_method_id=pm.id,
                customer_id=setup_intent.customer,
                gateway='stripe',
                last4=pm.card.last4 if pm.card else None,
                brand=pm.card.brand if pm.card else None,
                expiry=f"{pm.card.exp_month:02d}/{pm.card.exp_year}" if pm.card else None,
                raw_response={'payment_method': pm.id}
            )
        except Exception as e:
            logger.error(f"Stripe confirm setup error: {str(e)}")
            return PaymentResult(success=False, error=str(e), gateway='stripe')

    def stripe_create_subscription(self, customer_id: str, price_amount: Decimal,
                                    interval: str = 'month', trial_days: int = 0,
                                    metadata: dict = None) -> PaymentResult:
        """
        Create a Stripe subscription with optional trial period.
        Uses the customer's default payment method.
        """
        config = self._get_gateway_config('stripe')
        if not config:
            return PaymentResult(success=False, error="Stripe is not configured")

        if not self._init_stripe(config['credentials'].get('secret_key')):
            return PaymentResult(success=False, error="Failed to initialize Stripe")

        try:
            # Create a price on-the-fly (or use existing price ID in production)
            price = self._stripe.Price.create(
                unit_amount=int(float(price_amount) * 100),  # Convert to cents
                currency='usd',
                recurring={'interval': interval},
                product_data={'name': f'Subscription - ${price_amount}/{interval}'}
            )

            # Create subscription
            sub_params = {
                'customer': customer_id,
                'items': [{'price': price.id}],
                'payment_behavior': 'default_incomplete',
                'payment_settings': {'save_default_payment_method': 'on_subscription'},
                'expand': ['latest_invoice.payment_intent'],
                'metadata': metadata or {}
            }

            if trial_days > 0:
                sub_params['trial_period_days'] = trial_days

            subscription = self._stripe.Subscription.create(**sub_params)

            return PaymentResult(
                success=True,
                subscription_id=subscription.id,
                customer_id=customer_id,
                gateway='stripe',
                raw_response={'subscription': subscription.id, 'status': subscription.status}
            )
        except Exception as e:
            logger.error(f"Stripe subscription error: {str(e)}")
            return PaymentResult(success=False, error=str(e), gateway='stripe')

    def stripe_charge_payment_method(self, payment_method_id: str, customer_id: str,
                                      amount: Decimal, currency: str = 'usd',
                                      description: str = None) -> PaymentResult:
        """Charge a saved payment method (for post-trial billing)"""
        config = self._get_gateway_config('stripe')
        if not config:
            return PaymentResult(success=False, error="Stripe is not configured")

        if not self._init_stripe(config['credentials'].get('secret_key')):
            return PaymentResult(success=False, error="Failed to initialize Stripe")

        try:
            payment_intent = self._stripe.PaymentIntent.create(
                amount=int(float(amount) * 100),
                currency=currency.lower(),
                customer=customer_id,
                payment_method=payment_method_id,
                off_session=True,
                confirm=True,
                description=description or 'Subscription payment'
            )

            return PaymentResult(
                success=payment_intent.status == 'succeeded',
                payment_method_id=payment_method_id,
                customer_id=customer_id,
                gateway='stripe',
                raw_response={'payment_intent_id': payment_intent.id, 'status': payment_intent.status}
            )
        except Exception as e:
            logger.error(f"Stripe charge error: {str(e)}")
            return PaymentResult(success=False, error=str(e), gateway='stripe')

    def stripe_cancel_subscription(self, subscription_id: str,
                                    at_period_end: bool = True) -> PaymentResult:
        """Cancel a Stripe subscription"""
        config = self._get_gateway_config('stripe')
        if not config:
            return PaymentResult(success=False, error="Stripe is not configured")

        if not self._init_stripe(config['credentials'].get('secret_key')):
            return PaymentResult(success=False, error="Failed to initialize Stripe")

        try:
            if at_period_end:
                subscription = self._stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = self._stripe.Subscription.delete(subscription_id)

            return PaymentResult(
                success=True,
                subscription_id=subscription_id,
                gateway='stripe',
                raw_response={'status': subscription.status if hasattr(subscription, 'status') else 'cancelled'}
            )
        except Exception as e:
            logger.error(f"Stripe cancel subscription error: {str(e)}")
            return PaymentResult(success=False, error=str(e), gateway='stripe')

    # =========================================================================
    # PAYPAL METHODS
    # =========================================================================

    def _get_paypal_access_token(self, client_id: str, client_secret: str,
                                  sandbox: bool = True) -> Optional[str]:
        """Get PayPal OAuth access token"""
        import requests
        from base64 import b64encode

        if self._paypal_access_token and self._paypal_token_expiry:
            if datetime.utcnow() < self._paypal_token_expiry:
                return self._paypal_access_token

        base_url = "https://api-m.sandbox.paypal.com" if sandbox else "https://api-m.paypal.com"

        try:
            auth = b64encode(f"{client_id}:{client_secret}".encode()).decode()
            response = requests.post(
                f"{base_url}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"}
            )

            if response.status_code == 200:
                data = response.json()
                self._paypal_access_token = data['access_token']
                self._paypal_token_expiry = datetime.utcnow() + timedelta(seconds=data['expires_in'] - 60)
                return self._paypal_access_token
            else:
                logger.error(f"PayPal token error: {response.text}")
                return None
        except Exception as e:
            logger.error(f"PayPal token request error: {str(e)}")
            return None

    def paypal_create_subscription_plan(self, name: str, amount: Decimal,
                                         interval: str = 'MONTH',
                                         trial_days: int = 0) -> PaymentResult:
        """Create a PayPal billing plan for subscriptions"""
        import requests

        config = self._get_gateway_config('paypal')
        if not config:
            return PaymentResult(success=False, error="PayPal is not configured")

        creds = config['credentials']
        access_token = self._get_paypal_access_token(
            creds.get('client_id'),
            creds.get('client_secret'),
            config['is_sandbox']
        )

        if not access_token:
            return PaymentResult(success=False, error="Failed to authenticate with PayPal")

        base_url = "https://api-m.sandbox.paypal.com" if config['is_sandbox'] else "https://api-m.paypal.com"

        try:
            # Create product first
            product_response = requests.post(
                f"{base_url}/v1/catalogs/products",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "name": name,
                    "type": "SERVICE",
                    "category": "SOFTWARE"
                }
            )

            if product_response.status_code not in [200, 201]:
                return PaymentResult(success=False, error=f"Failed to create product: {product_response.text}")

            product_id = product_response.json()['id']

            # Create billing plan
            billing_cycles = []

            if trial_days > 0:
                billing_cycles.append({
                    "frequency": {"interval_unit": "DAY", "interval_count": trial_days},
                    "tenure_type": "TRIAL",
                    "sequence": 1,
                    "total_cycles": 1,
                    "pricing_scheme": {"fixed_price": {"value": "0", "currency_code": "USD"}}
                })

            billing_cycles.append({
                "frequency": {"interval_unit": interval.upper(), "interval_count": 1},
                "tenure_type": "REGULAR",
                "sequence": 2 if trial_days > 0 else 1,
                "total_cycles": 0,  # Infinite
                "pricing_scheme": {
                    "fixed_price": {"value": str(amount), "currency_code": "USD"}
                }
            })

            plan_response = requests.post(
                f"{base_url}/v1/billing/plans",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "product_id": product_id,
                    "name": f"{name} Plan",
                    "billing_cycles": billing_cycles,
                    "payment_preferences": {
                        "auto_bill_outstanding": True,
                        "payment_failure_threshold": 3
                    }
                }
            )

            if plan_response.status_code not in [200, 201]:
                return PaymentResult(success=False, error=f"Failed to create plan: {plan_response.text}")

            plan_data = plan_response.json()
            return PaymentResult(
                success=True,
                subscription_id=plan_data['id'],
                gateway='paypal',
                raw_response=plan_data
            )
        except Exception as e:
            logger.error(f"PayPal plan creation error: {str(e)}")
            return PaymentResult(success=False, error=str(e), gateway='paypal')

    def paypal_create_subscription(self, plan_id: str, return_url: str,
                                    cancel_url: str) -> PaymentResult:
        """Create a PayPal subscription that user will approve"""
        import requests

        config = self._get_gateway_config('paypal')
        if not config:
            return PaymentResult(success=False, error="PayPal is not configured")

        creds = config['credentials']
        access_token = self._get_paypal_access_token(
            creds.get('client_id'),
            creds.get('client_secret'),
            config['is_sandbox']
        )

        if not access_token:
            return PaymentResult(success=False, error="Failed to authenticate with PayPal")

        base_url = "https://api-m.sandbox.paypal.com" if config['is_sandbox'] else "https://api-m.paypal.com"

        try:
            response = requests.post(
                f"{base_url}/v1/billing/subscriptions",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "plan_id": plan_id,
                    "application_context": {
                        "brand_name": "RestaurantPro",
                        "return_url": return_url,
                        "cancel_url": cancel_url,
                        "user_action": "SUBSCRIBE_NOW"
                    }
                }
            )

            if response.status_code not in [200, 201]:
                return PaymentResult(success=False, error=f"Failed to create subscription: {response.text}")

            sub_data = response.json()
            approval_url = next(
                (link['href'] for link in sub_data.get('links', []) if link['rel'] == 'approve'),
                None
            )

            return PaymentResult(
                success=True,
                subscription_id=sub_data['id'],
                gateway='paypal',
                raw_response={'approval_url': approval_url, **sub_data}
            )
        except Exception as e:
            logger.error(f"PayPal subscription error: {str(e)}")
            return PaymentResult(success=False, error=str(e), gateway='paypal')

    def paypal_cancel_subscription(self, subscription_id: str,
                                    reason: str = "Customer requested cancellation") -> PaymentResult:
        """Cancel a PayPal subscription"""
        import requests

        config = self._get_gateway_config('paypal')
        if not config:
            return PaymentResult(success=False, error="PayPal is not configured")

        creds = config['credentials']
        access_token = self._get_paypal_access_token(
            creds.get('client_id'),
            creds.get('client_secret'),
            config['is_sandbox']
        )

        if not access_token:
            return PaymentResult(success=False, error="Failed to authenticate with PayPal")

        base_url = "https://api-m.sandbox.paypal.com" if config['is_sandbox'] else "https://api-m.paypal.com"

        try:
            response = requests.post(
                f"{base_url}/v1/billing/subscriptions/{subscription_id}/cancel",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"reason": reason}
            )

            # 204 No Content means success
            if response.status_code == 204:
                return PaymentResult(success=True, subscription_id=subscription_id, gateway='paypal')
            else:
                return PaymentResult(success=False, error=response.text, gateway='paypal')
        except Exception as e:
            logger.error(f"PayPal cancel subscription error: {str(e)}")
            return PaymentResult(success=False, error=str(e), gateway='paypal')

    # =========================================================================
    # PAYMENT INTENT FOR CHECKOUT (SUPPORTS STRIPE, GOOGLE PAY, APPLE PAY)
    # =========================================================================

    def create_payment_intent(self, gateway_name: str, amount: Decimal,
                               currency: str = 'usd', customer_email: str = None,
                               metadata: dict = None,
                               payment_method_types: list = None) -> PaymentResult:
        """
        Create a payment intent for one-time or subscription payment.
        For Stripe, this also supports Google Pay and Apple Pay through Payment Request API.
        """
        if gateway_name == 'stripe':
            config = self._get_gateway_config('stripe')
            if not config:
                return PaymentResult(success=False, error="Stripe is not configured")

            if not self._init_stripe(config['credentials'].get('secret_key')):
                return PaymentResult(success=False, error="Failed to initialize Stripe")

            try:
                # Default payment method types including wallets
                if payment_method_types is None:
                    payment_method_types = ['card']
                    gateway = config['gateway']
                    if gateway.supports_apple_pay:
                        payment_method_types.append('apple_pay')
                    if gateway.supports_google_pay:
                        # Google Pay uses 'card' payment method type with Payment Request API
                        pass

                intent_params = {
                    'amount': int(float(amount) * 100),
                    'currency': currency.lower(),
                    'payment_method_types': payment_method_types,
                    'metadata': metadata or {}
                }

                if customer_email:
                    intent_params['receipt_email'] = customer_email

                payment_intent = self._stripe.PaymentIntent.create(**intent_params)

                return PaymentResult(
                    success=True,
                    payment_method_id=payment_intent.client_secret,
                    gateway='stripe',
                    raw_response={
                        'payment_intent_id': payment_intent.id,
                        'client_secret': payment_intent.client_secret
                    }
                )
            except Exception as e:
                logger.error(f"Stripe payment intent error: {str(e)}")
                return PaymentResult(success=False, error=str(e), gateway='stripe')

        elif gateway_name == 'paypal':
            # PayPal uses order creation instead of payment intent
            return PaymentResult(
                success=False,
                error="Use paypal_create_subscription for PayPal payments",
                gateway='paypal'
            )

        return PaymentResult(success=False, error=f"Unknown gateway: {gateway_name}")


# Singleton instance
payment_service = PaymentService()

