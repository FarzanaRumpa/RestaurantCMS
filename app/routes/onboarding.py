"""
Onboarding Routes
API endpoints for restaurant owner onboarding flow
"""
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, session
from functools import wraps

from app import db
from app.models import User, Restaurant
from app.models.onboarding_models import OnboardingStep, RestaurantOnboarding
from app.services.onboarding_service import OnboardingService

onboarding_bp = Blueprint('onboarding', __name__)


def owner_required(f):
    """Decorator to require owner authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('owner_logged_in'):
            flash('Please login to access this page', 'error')
            return redirect(url_for('owner.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_owner():
    """Get the currently logged in owner"""
    user_id = session.get('owner_user_id')
    if user_id:
        return User.query.get(user_id)
    return None


# ===========================================
# ONBOARDING PAGES
# ===========================================

@onboarding_bp.route('/onboarding')
@owner_required
def onboarding_flow():
    """Main onboarding page showing current progress"""
    user = get_current_owner()
    if not user or not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.login'))

    # Get onboarding progress
    progress = OnboardingService.get_progress(user.restaurant.id)

    # If onboarding complete, redirect to dashboard
    if progress.get('is_complete') or progress.get('skipped'):
        flash('Onboarding complete! Welcome to your dashboard.', 'success')
        return redirect(url_for('owner.dashboard', restaurant_id=user.restaurant.public_id))

    return render_template('owner/onboarding/index.html',
        user=user,
        restaurant=user.restaurant,
        progress=progress,
        steps=progress.get('steps', []),
        current_step=progress.get('current_step'),
        OnboardingStep=OnboardingStep
    )


@onboarding_bp.route('/onboarding/step/<step_name>')
@owner_required
def onboarding_step(step_name):
    """Show specific onboarding step with guidance"""
    user = get_current_owner()
    if not user or not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.login'))

    # Validate step name
    if step_name not in OnboardingStep.ALL_STEPS:
        flash('Invalid onboarding step', 'error')
        return redirect(url_for('onboarding.onboarding_flow'))

    progress = OnboardingService.get_progress(user.restaurant.id)
    step_info = None
    for step in progress.get('steps', []):
        if step['name'] == step_name:
            step_info = step
            break

    if not step_info:
        flash('Step not found', 'error')
        return redirect(url_for('onboarding.onboarding_flow'))

    return render_template(f'owner/onboarding/step_{step_name}.html',
        user=user,
        restaurant=user.restaurant,
        progress=progress,
        step_info=step_info,
        OnboardingStep=OnboardingStep
    )


# ===========================================
# ONBOARDING API ENDPOINTS
# ===========================================

@onboarding_bp.route('/api/onboarding/progress', methods=['GET'])
@owner_required
def api_get_progress():
    """Get current onboarding progress"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'error': 'No restaurant found'}), 404

    progress = OnboardingService.get_progress(user.restaurant.id)
    return jsonify(progress)


@onboarding_bp.route('/api/onboarding/check', methods=['POST'])
@owner_required
def api_check_progress():
    """Re-check and update onboarding progress"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'error': 'No restaurant found'}), 404

    # Force re-check of all steps
    onboarding = OnboardingService.check_and_update_progress(user.restaurant.id)
    progress = onboarding.to_dict()

    return jsonify({
        'success': True,
        'progress': progress,
        'is_complete': progress.get('is_complete', False)
    })


@onboarding_bp.route('/api/onboarding/step/<step_name>/complete', methods=['POST'])
@owner_required
def api_complete_step(step_name):
    """Mark a specific step as complete (manual)"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'error': 'No restaurant found'}), 404

    success, message = OnboardingService.mark_step_complete_manual(
        user.restaurant.id,
        step_name
    )

    if success:
        progress = OnboardingService.get_progress(user.restaurant.id)
        return jsonify({
            'success': True,
            'message': message,
            'progress': progress
        })
    else:
        return jsonify({
            'success': False,
            'error': message
        }), 400


@onboarding_bp.route('/api/onboarding/features', methods=['GET'])
@owner_required
def api_get_features():
    """Get feature visibility status"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'error': 'No restaurant found'}), 404

    features = OnboardingService.get_all_feature_visibility(user.restaurant.id)
    return jsonify({
        'features': features,
        'onboarding_complete': OnboardingService.is_onboarding_complete(user.restaurant.id)
    })


@onboarding_bp.route('/api/onboarding/feature/<feature_name>/check', methods=['GET'])
@owner_required
def api_check_feature(feature_name):
    """Check if a specific feature is accessible"""
    user = get_current_owner()
    if not user or not user.restaurant:
        return jsonify({'error': 'No restaurant found'}), 404

    accessible, reason = OnboardingService.is_feature_accessible(
        user.restaurant.id,
        feature_name
    )

    return jsonify({
        'feature': feature_name,
        'is_accessible': accessible,
        'lock_reason': reason
    })


# ===========================================
# ADMIN ONBOARDING MANAGEMENT
# ===========================================

@onboarding_bp.route('/api/admin/onboarding/<int:restaurant_id>/skip', methods=['POST'])
def api_admin_skip_onboarding(restaurant_id):
    """Admin endpoint to skip onboarding for a restaurant"""
    # Check admin authentication
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    admin_user = User.query.get(session.get('admin_user_id'))
    if not admin_user or admin_user.role not in ['admin', 'superadmin', 'system_admin']:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    reason = data.get('reason', 'Skipped by admin')

    success = OnboardingService.skip_onboarding(
        restaurant_id,
        admin_user.id,
        reason
    )

    if success:
        return jsonify({
            'success': True,
            'message': 'Onboarding skipped successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to skip onboarding'
        }), 500


@onboarding_bp.route('/api/admin/onboarding/<int:restaurant_id>/reset', methods=['POST'])
def api_admin_reset_onboarding(restaurant_id):
    """Admin endpoint to reset onboarding for a restaurant"""
    # Check admin authentication
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    admin_user = User.query.get(session.get('admin_user_id'))
    if not admin_user or admin_user.role not in ['admin', 'superadmin', 'system_admin']:
        return jsonify({'error': 'Unauthorized'}), 401

    success = OnboardingService.reset_onboarding(restaurant_id)

    if success:
        return jsonify({
            'success': True,
            'message': 'Onboarding reset successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to reset onboarding'
        }), 500


@onboarding_bp.route('/api/admin/onboarding/<int:restaurant_id>/status', methods=['GET'])
def api_admin_get_onboarding(restaurant_id):
    """Admin endpoint to get onboarding status for a restaurant"""
    # Check admin authentication
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    progress = OnboardingService.get_progress(restaurant_id)
    features = OnboardingService.get_all_feature_visibility(restaurant_id)

    return jsonify({
        'progress': progress,
        'features': features
    })

