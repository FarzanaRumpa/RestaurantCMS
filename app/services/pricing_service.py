"""
Pricing Plan Service
Handles plan access control and feature validation
"""
from functools import wraps
from flask import jsonify
from app.models import Restaurant
from app.models.website_content_models import PricingPlan


class PlanAccessControl:
    """Access control based on pricing plans"""

    @staticmethod
    def check_feature_access(restaurant_id, feature_name):
        """Check if restaurant has access to a feature"""
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return False
        return restaurant.has_feature(feature_name)

    @staticmethod
    def check_limit(restaurant_id, limit_name, current_count):
        """Check if restaurant is within plan limits"""
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return False

        limit = restaurant.get_limit(limit_name)
        if limit is None:
            return True  # Unlimited

        return current_count < limit

    @staticmethod
    def get_remaining(restaurant_id, limit_name, current_count):
        """Get remaining allowance for a limit"""
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return 0

        limit = restaurant.get_limit(limit_name)
        if limit is None:
            return float('inf')  # Unlimited

        return max(0, limit - current_count)


def require_feature(feature_name):
    """
    Decorator to require a specific feature based on plan
    Note: This should be used in routes where current_user is available (with Flask-Login)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Import here to avoid circular dependency
            try:
                from flask_login import current_user
            except ImportError:
                return jsonify({
                    'success': False,
                    'error': 'Flask-Login not configured'
                }), 500

            if not current_user.is_authenticated:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401

            restaurant = current_user.restaurant
            if not restaurant:
                return jsonify({
                    'success': False,
                    'error': 'No restaurant associated with account'
                }), 403

            # Check feature access
            if not restaurant.has_feature(feature_name):
                plan_name = restaurant.pricing_plan.name if restaurant.pricing_plan else 'No Plan'
                return jsonify({
                    'success': False,
                    'error': f'This feature is not available in your current plan ({plan_name})',
                    'feature': feature_name,
                    'upgrade_required': True
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_limit(limit_name, count_func):
    """
    Decorator to check if within plan limits
    count_func should be a function that takes restaurant_id and returns current count
    Note: This should be used in routes where current_user is available (with Flask-Login)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                from flask_login import current_user
            except ImportError:
                return jsonify({
                    'success': False,
                    'error': 'Flask-Login not configured'
                }), 500

            if not current_user.is_authenticated:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401

            restaurant = current_user.restaurant
            if not restaurant:
                return jsonify({
                    'success': False,
                    'error': 'No restaurant associated with account'
                }), 403

            # Get current count
            current_count = count_func(restaurant.id)

            # Check limit
            limit = restaurant.get_limit(limit_name)
            if limit is not None and current_count >= limit:
                plan_name = restaurant.pricing_plan.name if restaurant.pricing_plan else 'No Plan'
                return jsonify({
                    'success': False,
                    'error': f'You have reached your plan limit for {limit_name} ({limit})',
                    'limit': limit_name,
                    'current_count': current_count,
                    'max_allowed': limit,
                    'plan_name': plan_name,
                    'upgrade_required': True
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


class PricingPlanService:
    """Service for managing pricing plans and subscriptions"""

    @staticmethod
    def assign_plan_to_restaurant(restaurant_id, plan_id, country_code='US', start_date=None):
        """Assign a pricing plan to a restaurant"""
        from datetime import datetime, timedelta, timezone
        from app import db

        restaurant = Restaurant.query.get(restaurant_id)
        plan = PricingPlan.query.get(plan_id)

        if not restaurant or not plan:
            return False

        restaurant.pricing_plan_id = plan_id
        restaurant.country_code = country_code
        restaurant.subscription_start_date = start_date or datetime.now(timezone.utc)

        # Set end date based on plan period
        if plan.price_period == 'month':
            restaurant.subscription_end_date = restaurant.subscription_start_date + timedelta(days=30)
        elif plan.price_period == 'year':
            restaurant.subscription_end_date = restaurant.subscription_start_date + timedelta(days=365)
        else:
            restaurant.subscription_end_date = None  # One-time or lifetime

        db.session.commit()
        return True

    @staticmethod
    def get_plan_for_country(plan_id, country_code):
        """Get plan details with country-specific pricing"""
        plan = PricingPlan.query.get(plan_id)
        if not plan:
            return None

        return plan.to_dict(country_code=country_code)

    @staticmethod
    def get_active_plans(country_code='US'):
        """Get all active plans with country-specific pricing"""
        plans = PricingPlan.query.filter_by(is_active=True).order_by(
            PricingPlan.display_order
        ).all()

        return [plan.to_dict(country_code=country_code) for plan in plans]

    @staticmethod
    def get_plan_comparison():
        """Get feature comparison matrix for all active plans"""
        plans = PricingPlan.query.filter_by(is_active=True).order_by(
            PricingPlan.display_order
        ).all()

        features = [
            {'key': 'kitchen_display', 'name': 'Kitchen Display Screen'},
            {'key': 'customer_display', 'name': 'Customer Display Screen'},
            {'key': 'owner_dashboard', 'name': 'Owner Dashboard'},
            {'key': 'advanced_analytics', 'name': 'Advanced Analytics'},
            {'key': 'qr_ordering', 'name': 'QR Code Ordering'},
            {'key': 'table_management', 'name': 'Table Management'},
            {'key': 'order_history', 'name': 'Order History'},
            {'key': 'customer_feedback', 'name': 'Customer Feedback'},
            {'key': 'inventory_management', 'name': 'Inventory Management'},
            {'key': 'staff_management', 'name': 'Staff Management'},
            {'key': 'multi_language', 'name': 'Multi-Language Support'},
            {'key': 'custom_branding', 'name': 'Custom Branding'},
            {'key': 'email_notifications', 'name': 'Email Notifications'},
            {'key': 'sms_notifications', 'name': 'SMS Notifications'},
            {'key': 'api_access', 'name': 'API Access'},
            {'key': 'priority_support', 'name': 'Priority Support'},
            {'key': 'white_label', 'name': 'White Label'},
            {'key': 'reports_export', 'name': 'Reports Export'},
            {'key': 'pos_integration', 'name': 'POS Integration'},
            {'key': 'payment_integration', 'name': 'Payment Integration'},
        ]

        limits = [
            {'key': 'max_tables', 'name': 'Maximum Tables'},
            {'key': 'max_menu_items', 'name': 'Maximum Menu Items'},
            {'key': 'max_categories', 'name': 'Maximum Categories'},
            {'key': 'max_orders_per_month', 'name': 'Orders per Month'},
            {'key': 'max_restaurants', 'name': 'Restaurant Locations'},
            {'key': 'max_staff_accounts', 'name': 'Staff Accounts'},
        ]

        comparison = {
            'plans': [p.to_dict() for p in plans],
            'features': features,
            'limits': limits
        }

        return comparison

