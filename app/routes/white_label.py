"""
White-Label Routes
==================
API endpoints for custom domain and branding management.
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
import logging

from app import db
from app.services.white_label_service import WhiteLabelService
from app.api.versioning import api_response, ValidationError, NotFoundError, AuthorizationError

logger = logging.getLogger(__name__)

white_label_bp = Blueprint('white_label', __name__, url_prefix='/owner/api/white-label')


def owner_required(f):
    """Require authenticated restaurant owner"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        if 'owner_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        from app.models import Restaurant
        restaurant = Restaurant.query.filter_by(owner_id=session['owner_id']).first()
        if not restaurant:
            return jsonify({'error': 'No restaurant found'}), 404

        g.restaurant_id = restaurant.id
        g.restaurant = restaurant
        return f(*args, **kwargs)
    return decorated_function


@white_label_bp.route('/status', methods=['GET'])
@owner_required
def get_white_label_status():
    """Get white-label feature status for restaurant"""
    from app.models.white_label_models import CustomDomain, WhiteLabelBranding

    allowed = WhiteLabelService.is_white_label_allowed(g.restaurant_id)

    custom_domain = CustomDomain.query.filter_by(restaurant_id=g.restaurant_id).first()
    branding = WhiteLabelBranding.query.filter_by(restaurant_id=g.restaurant_id).first()

    return api_response(data={
        'is_allowed': allowed,
        'custom_domain': custom_domain.to_dict() if custom_domain else None,
        'branding': branding.to_dict() if branding else None,
        'plan_required': 'enterprise' if not allowed else None
    })


@white_label_bp.route('/domain', methods=['POST'])
@owner_required
def register_domain():
    """Register a custom domain"""
    data = request.get_json()
    if not data or 'domain' not in data:
        raise ValidationError("Domain is required", field='domain')

    success, domain, error = WhiteLabelService.register_custom_domain(
        restaurant_id=g.restaurant_id,
        domain=data['domain'],
        verification_method=data.get('verification_method', 'dns')
    )

    if not success:
        raise ValidationError(error or "Failed to register domain")

    return api_response(
        data={
            'domain': domain.to_dict(),
            'verification_instructions': _get_verification_instructions(domain)
        },
        message="Domain registered. Please complete verification."
    )


@white_label_bp.route('/domain/verify', methods=['POST'])
@owner_required
def verify_domain():
    """Verify domain ownership"""
    success, error = WhiteLabelService.verify_domain(g.restaurant_id)

    if not success:
        raise ValidationError(error or "Verification failed")

    from app.models.white_label_models import CustomDomain
    domain = CustomDomain.query.filter_by(restaurant_id=g.restaurant_id).first()

    return api_response(
        data=domain.to_dict(),
        message="Domain verified successfully. SSL certificate is being issued."
    )


@white_label_bp.route('/domain', methods=['DELETE'])
@owner_required
def remove_domain():
    """Remove custom domain"""
    success = WhiteLabelService.remove_custom_domain(g.restaurant_id)

    if not success:
        raise NotFoundError("Custom domain")

    return api_response(message="Custom domain removed")


@white_label_bp.route('/branding', methods=['GET'])
@owner_required
def get_branding():
    """Get branding configuration"""
    branding = WhiteLabelService.get_branding(g.restaurant_id)

    if not branding:
        return api_response(data={
            'is_enabled': False,
            'message': 'No custom branding configured'
        })

    return api_response(data=branding.to_dict())


@white_label_bp.route('/branding', methods=['PUT'])
@owner_required
def update_branding():
    """Update branding configuration"""
    data = request.get_json()
    if not data:
        raise ValidationError("Request body required")

    success, error = WhiteLabelService.update_branding(
        restaurant_id=g.restaurant_id,
        **data
    )

    if not success:
        raise ValidationError(error or "Failed to update branding")

    branding = WhiteLabelService.get_branding(g.restaurant_id)

    return api_response(
        data=branding.to_dict() if branding else None,
        message="Branding updated successfully"
    )


@white_label_bp.route('/preview', methods=['GET'])
@owner_required
def preview_branding():
    """Get branding preview for customer-facing pages"""
    branding = WhiteLabelService.get_customer_facing_branding(g.restaurant_id)
    return api_response(data=branding)


def _get_verification_instructions(domain):
    """Get verification instructions based on method"""
    if domain.verification_method == 'dns':
        return {
            'method': 'dns',
            'record_type': 'TXT',
            'record_name': f"_rcms-verify.{domain.domain}",
            'record_value': domain.verification_token,
            'instructions': [
                f"1. Log in to your domain registrar or DNS provider",
                f"2. Add a TXT record with name: _rcms-verify.{domain.domain}",
                f"3. Set the value to: {domain.verification_token}",
                f"4. Wait for DNS propagation (usually 5-30 minutes)",
                f"5. Click 'Verify' to complete the process"
            ]
        }
    elif domain.verification_method == 'cname':
        return {
            'method': 'cname',
            'record_type': 'CNAME',
            'record_name': domain.domain,
            'record_value': 'custom.restaurantcms.com',
            'instructions': [
                f"1. Log in to your domain registrar or DNS provider",
                f"2. Add a CNAME record for: {domain.domain}",
                f"3. Point it to: custom.restaurantcms.com",
                f"4. Wait for DNS propagation",
                f"5. Click 'Verify' to complete the process"
            ]
        }
    return {}

