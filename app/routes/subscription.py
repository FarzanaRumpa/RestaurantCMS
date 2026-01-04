"""
Subscription Routes
API endpoints for subscription management in owner dashboard
"""
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from functools import wraps

from app import db
from app.models import User
from app.models.website_content_models import (
    PricingPlan, PaymentGateway, Subscription, SubscriptionStatus
)
from app.services.subscription_service import SubscriptionService
from app.services.geo_service import get_country_info

subscription_bp = Blueprint('subscription', __name__)


def owner_required(f):
    """Decorator to require owner authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        if not session.get('owner_logged_in'):
            flash('Please login to access this page', 'error')
            return redirect(url_for('owner.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_owner():
    """Get the currently logged in owner"""
    from flask import session
    user_id = session.get('owner_user_id')
    if user_id:
        return User.query.get(user_id)
    return None


def get_client_ip():
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


# ===========================================
# SUBSCRIPTION MANAGEMENT PAGES
# ===========================================

@subscription_bp.route('/subscription')
@owner_required
def subscription_status():
    """View current subscription status"""
    user = get_current_owner()
    if not user or not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))

    subscription = SubscriptionService.get_active_subscription(user.restaurant.id)
    access_info = SubscriptionService.check_subscription_access(user.restaurant.id)

    # Get available plans for upgrade
    plans = PricingPlan.query.filter_by(is_active=True).order_by(PricingPlan.display_order).all()
    country_info = get_country_info()
    user_country = user.restaurant.country_code or country_info.get('country_code', 'US')

    return render_template('owner/subscription.html',
        user=user,
        restaurant=user.restaurant,
        subscription=subscription,
        access_info=access_info,
        plans=plans,
        user_country=user_country,
        country_info=country_info
    )


@subscription_bp.route('/subscription/history')
@owner_required
def subscription_history():
    """View subscription event history"""
    user = get_current_owner()
    if not user or not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))

    subscription = SubscriptionService.get_active_subscription(user.restaurant.id)
    events = []
    if subscription:
        events = subscription.events.order_by(db.desc('created_at')).limit(50).all()

    return render_template('owner/subscription_history.html',
        user=user,
        restaurant=user.restaurant,
        subscription=subscription,
        events=events
    )


# ===========================================
# SUBSCRIPTION CHECKOUT FLOW
# ===========================================

@subscription_bp.route('/subscribe/<int:plan_id>')
@owner_required
def subscribe_checkout(plan_id):
    """Checkout page for subscribing to a plan"""
    user = get_current_owner()
    if not user or not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))

    plan = PricingPlan.query.get_or_404(plan_id)

    if not plan.is_active:
        flash('This plan is not available', 'error')
        return redirect(url_for('owner.upgrade_plan'))

    # Check for existing subscription
    existing = SubscriptionService.get_active_subscription(user.restaurant.id)
    if existing:
        flash('You already have an active subscription. Please manage it from your subscription page.', 'info')
        return redirect(url_for('subscription.subscription_status'))

    # Get country-based pricing
    country_info = get_country_info()
    user_country = user.restaurant.country_code or country_info.get('country_code', 'US')
    plan_price = plan.get_price_for_country(user_country)

    # Get available payment gateways
    gateways = PaymentGateway.query.filter_by(is_active=True).order_by(PaymentGateway.display_order).all()

    return render_template('owner/subscribe_checkout.html',
        user=user,
        restaurant=user.restaurant,
        plan=plan,
        plan_price=plan_price,
        has_trial=plan.trial_enabled and plan.trial_days > 0,
        trial_days=plan.trial_days if plan.trial_enabled else 0,
        country_info=country_info,
        user_country=user_country,
        gateways=gateways
    )


@subscription_bp.route('/subscribe/<int:plan_id>/process', methods=['POST'])
@owner_required
def process_subscription(plan_id):
    """Process subscription creation with payment method"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'success': False, 'error': 'No restaurant found'}), 400

    plan = PricingPlan.query.get(plan_id)
    if not plan or not plan.is_active:
        return jsonify({'success': False, 'error': 'Invalid plan'}), 400

    # Get form data
    data = request.get_json() if request.is_json else request.form

    payment_method_token = data.get('payment_method_token')
    payment_gateway = data.get('payment_gateway')
    consent_accepted = data.get('consent_accepted', False)

    if not consent_accepted:
        return jsonify({'success': False, 'error': 'You must accept the terms and conditions'}), 400

    if float(plan.price) > 0:
        if not payment_method_token:
            return jsonify({'success': False, 'error': 'Payment method required'}), 400
        if not payment_gateway:
            return jsonify({'success': False, 'error': 'Please select a payment method'}), 400

    # Payment method details (from frontend tokenization)
    payment_method_details = {
        'last4': data.get('card_last4', ''),
        'brand': data.get('card_brand', ''),
        'expiry': data.get('card_expiry', '')
    }

    country_info = get_country_info()
    user_country = user.restaurant.country_code or country_info.get('country_code', 'US')

    # Create subscription
    if float(plan.price) == 0:
        subscription, error = SubscriptionService.create_free_subscription(
            restaurant_id=user.restaurant.id,
            plan_id=plan_id
        )
    else:
        subscription, error = SubscriptionService.create_subscription_with_trial(
            restaurant_id=user.restaurant.id,
            plan_id=plan_id,
            payment_method_token=payment_method_token,
            payment_gateway=payment_gateway,
            payment_method_details=payment_method_details,
            country_code=user_country,
            consent_ip=get_client_ip(),
            terms_version='v1.0',
            consent_method='checkbox'
        )

    if error:
        return jsonify({'success': False, 'error': error}), 400

    # Success
    if subscription.is_trialing:
        message = f'Your {plan.trial_days}-day free trial has started! You will be charged ${float(subscription.billing_amount):.2f} on {subscription.trial_end_date.strftime("%B %d, %Y")}.'
    else:
        message = f'Successfully subscribed to {plan.name} plan!'

    return jsonify({
        'success': True,
        'message': message,
        'subscription': subscription.to_dict(),
        'redirect_url': url_for('subscription.subscription_status')
    })


# ===========================================
# SUBSCRIPTION ACTIONS
# ===========================================

@subscription_bp.route('/subscription/cancel', methods=['POST'])
@owner_required
def cancel_subscription():
    """Cancel current subscription"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'success': False, 'error': 'No restaurant found'}), 400

    subscription = SubscriptionService.get_active_subscription(user.restaurant.id)
    if not subscription:
        return jsonify({'success': False, 'error': 'No active subscription found'}), 400

    data = request.get_json() if request.is_json else request.form
    reason = data.get('reason', '')
    immediate = data.get('immediate', False)

    success, message = SubscriptionService.cancel_subscription(
        subscription_id=subscription.id,
        reason=reason,
        immediate=immediate,
        user_id=user.id,
        ip_address=get_client_ip()
    )

    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400


@subscription_bp.route('/subscription/reactivate', methods=['POST'])
@owner_required
def reactivate_subscription():
    """Reactivate a cancelled subscription"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'success': False, 'error': 'No restaurant found'}), 400

    subscription = SubscriptionService.get_active_subscription(user.restaurant.id)
    if not subscription:
        # Check for recently cancelled subscription
        subscription = Subscription.query.filter_by(
            restaurant_id=user.restaurant.id,
            status=SubscriptionStatus.CANCELLED
        ).order_by(Subscription.cancelled_at.desc()).first()

    if not subscription:
        return jsonify({'success': False, 'error': 'No subscription found to reactivate'}), 400

    success, message = SubscriptionService.reactivate_subscription(
        subscription_id=subscription.id,
        user_id=user.id
    )

    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400


@subscription_bp.route('/subscription/update-payment', methods=['GET', 'POST'])
@owner_required
def update_payment_method():
    """Update payment method for subscription"""
    user = get_current_owner()
    if not user or not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))

    subscription = SubscriptionService.get_active_subscription(user.restaurant.id)
    if not subscription:
        flash('No active subscription found', 'error')
        return redirect(url_for('subscription.subscription_status'))

    if request.method == 'GET':
        gateways = PaymentGateway.query.filter_by(is_active=True).order_by(PaymentGateway.display_order).all()
        return render_template('owner/update_payment_method.html',
            user=user,
            restaurant=user.restaurant,
            subscription=subscription,
            gateways=gateways
        )

    # POST - update payment method
    data = request.get_json() if request.is_json else request.form

    payment_method_token = data.get('payment_method_token')
    payment_gateway = data.get('payment_gateway')

    if not payment_method_token or not payment_gateway:
        return jsonify({'success': False, 'error': 'Payment method required'}), 400

    payment_method_details = {
        'last4': data.get('card_last4', ''),
        'brand': data.get('card_brand', ''),
        'expiry': data.get('card_expiry', '')
    }

    success, message = SubscriptionService.update_payment_method(
        subscription_id=subscription.id,
        payment_method_token=payment_method_token,
        payment_gateway=payment_gateway,
        details=payment_method_details,
        user_id=user.id,
        ip_address=get_client_ip()
    )

    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400


@subscription_bp.route('/subscription/change-plan/<int:plan_id>', methods=['POST'])
@owner_required
def change_plan(plan_id):
    """Change to a different subscription plan"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'success': False, 'error': 'No restaurant found'}), 400

    subscription = SubscriptionService.get_active_subscription(user.restaurant.id)
    if not subscription:
        # No subscription - redirect to checkout
        return jsonify({
            'success': False,
            'error': 'No active subscription',
            'redirect_url': url_for('subscription.subscribe_checkout', plan_id=plan_id)
        }), 400

    success, message = SubscriptionService.change_plan(
        subscription_id=subscription.id,
        new_plan_id=plan_id,
        user_id=user.id
    )

    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400


# ===========================================
# API ENDPOINTS
# ===========================================

@subscription_bp.route('/api/subscription/status')
@owner_required
def api_subscription_status():
    """API endpoint to get subscription status"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'success': False, 'error': 'No restaurant found'}), 400

    access_info = SubscriptionService.check_subscription_access(user.restaurant.id)
    return jsonify({'success': True, 'data': access_info})


@subscription_bp.route('/api/subscription/events')
@owner_required
def api_subscription_events():
    """API endpoint to get subscription events"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'success': False, 'error': 'No restaurant found'}), 400

    subscription = SubscriptionService.get_active_subscription(user.restaurant.id)
    if not subscription:
        return jsonify({'success': True, 'data': []})

    limit = request.args.get('limit', 20, type=int)
    events = subscription.events.order_by(db.desc('created_at')).limit(limit).all()

    return jsonify({
        'success': True,
        'data': [e.to_dict() for e in events]
    })

