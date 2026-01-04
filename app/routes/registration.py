"""
API endpoints for restaurant registration from mobile app
"""
from flask import Blueprint, request
from app import db
from app.models import RegistrationRequest
from app.schemas import validate_required_fields, json_response, error_response

registration_bp = Blueprint('registration', __name__)

@registration_bp.route('/apply', methods=['POST'])
def apply_for_registration():
    """
    Submit a new restaurant registration application

    MODERATION DISABLED: Registrations are auto-approved instantly.
    The moderation system architecture remains intact for future use.

    Required fields:
    - applicant_name: str
    - applicant_email: str
    - restaurant_name: str

    Optional fields:
    - applicant_phone: str
    - restaurant_description: str
    - restaurant_address: str
    - restaurant_phone: str
    - restaurant_type: str (cafe, restaurant, bar, fast-food, etc.)
    - pricing_plan_id: int (selected pricing plan)
    - country_code: str (ISO country code for tier-based pricing)
    """
    data = request.get_json()

    validation = validate_required_fields(data, ['applicant_name', 'applicant_email', 'restaurant_name'])
    if validation:
        return validation

    # Validate pricing plan if provided
    pricing_plan_id = data.get('pricing_plan_id')
    pricing_plan = None
    if pricing_plan_id:
        from app.models.website_content_models import PricingPlan
        pricing_plan = PricingPlan.query.get(pricing_plan_id)
        if not pricing_plan or not pricing_plan.is_active:
            return error_response('Invalid or inactive pricing plan selected', 400)

    # Check if email already has a pending request
    existing = RegistrationRequest.query.filter_by(
        applicant_email=data['applicant_email'],
        status='pending'
    ).first()

    if existing:
        return error_response('You already have a pending registration request', 400)

    # Check if email already has an approved request
    approved = RegistrationRequest.query.filter_by(
        applicant_email=data['applicant_email'],
        status='approved'
    ).first()

    if approved:
        return error_response('A restaurant with this email has already been approved', 400)

    # Check if user already exists
    from app.models import User, Restaurant
    existing_user = User.query.filter_by(email=data['applicant_email']).first()
    if existing_user:
        return error_response('An account with this email already exists', 400)

    # Create registration request (for audit trail)
    reg_request = RegistrationRequest(
        applicant_name=data['applicant_name'],
        applicant_email=data['applicant_email'],
        applicant_phone=data.get('applicant_phone'),
        restaurant_name=data['restaurant_name'],
        restaurant_description=data.get('restaurant_description'),
        restaurant_address=data.get('restaurant_address'),
        restaurant_phone=data.get('restaurant_phone'),
        restaurant_type=data.get('restaurant_type'),
        status='pending',  # Will be set based on moderation setting
        priority='normal'
    )

    # Store pricing plan selection and country for later
    if pricing_plan_id:
        reg_request.notes = f"Selected Plan ID: {pricing_plan_id}"
        if data.get('country_code'):
            reg_request.notes += f", Country: {data.get('country_code')}"

    db.session.add(reg_request)
    db.session.flush()  # Get the ID

    # Check if moderation is enabled
    from app.models import SystemSettings
    moderation_enabled = SystemSettings.is_moderation_enabled()

    # Automatically create user and restaurant account
    from datetime import datetime, timedelta
    import secrets
    import string

    # Generate username from email
    username = data['applicant_email'].split('@')[0]
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    # Generate temporary password
    temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

    # Create user
    new_user = User(
        username=username,
        email=data['applicant_email'],
        role='restaurant_owner',
        is_active=True
    )
    new_user.set_password(temp_password)
    db.session.add(new_user)
    db.session.flush()

    # Determine registration status based on moderation setting
    if moderation_enabled:
        registration_status = 'pending_review'
        reg_request_status = 'pending'
        status_message = 'Your account has been created and is pending review. You can access limited features until approved.'
    else:
        registration_status = 'approved'
        reg_request_status = 'approved'
        status_message = 'Your account has been created successfully! Please login with your credentials.'

    # Create restaurant
    new_restaurant = Restaurant(
        name=data['restaurant_name'],
        description=data.get('restaurant_description'),
        address=data.get('restaurant_address'),
        phone=data.get('restaurant_phone'),
        email=data['applicant_email'],
        owner_id=new_user.id,
        is_active=True,
        country_code=data.get('country_code', 'US'),
        pricing_plan_id=pricing_plan_id if pricing_plan else None,
        registration_status=registration_status,
        registration_request_id=reg_request.id
    )

    # Set trial period if plan selected
    if pricing_plan:
        new_restaurant.is_trial = True
        new_restaurant.trial_ends_at = datetime.utcnow() + timedelta(days=14)
        new_restaurant.subscription_start_date = datetime.utcnow()

    db.session.add(new_restaurant)
    db.session.flush()

    # Update registration request
    reg_request.status = reg_request_status
    reg_request.reviewed_at = datetime.utcnow() if not moderation_enabled else None
    reg_request.approved_user_id = new_user.id
    reg_request.approved_restaurant_id = new_restaurant.id
    reg_request.admin_notes = 'Auto-approved (moderation disabled)' if not moderation_enabled else 'Pending moderation review'

    # Create moderation log for audit trail
    from app.models import ModerationLog
    log = ModerationLog(
        registration_id=reg_request.id,
        admin_id=None,  # System
        action='approved' if not moderation_enabled else 'created',
        old_status='new',
        new_status=reg_request_status,
        notes='Auto-approved by system' if not moderation_enabled else 'Account created, pending moderation'
    )
    db.session.add(log)

    db.session.commit()

    return json_response({
        'request_id': reg_request.request_id,
        'status': reg_request_status,
        'registration_status': registration_status,
        'moderation_enabled': moderation_enabled,
        'username': username,
        'temp_password': temp_password,
        'restaurant_id': new_restaurant.id,
        'pricing_plan_id': pricing_plan_id,
        'message': status_message
    }, 'Registration successful', 201)


@registration_bp.route('/status/<request_id>', methods=['GET'])
def check_registration_status(request_id):
    """
    Check the status of a registration request
    """
    reg_request = RegistrationRequest.query.filter_by(request_id=request_id).first()

    if not reg_request:
        return error_response('Registration request not found', 404)

    response = {
        'request_id': reg_request.request_id,
        'status': reg_request.status,
        'restaurant_name': reg_request.restaurant_name,
        'submitted_at': reg_request.created_at.isoformat(),
        'updated_at': reg_request.updated_at.isoformat() if reg_request.updated_at else None
    }

    if reg_request.status == 'rejected':
        response['rejection_reason'] = reg_request.rejection_reason

    if reg_request.status == 'more_info_needed':
        response['moderator_message'] = reg_request.moderator_notes

    if reg_request.status == 'approved':
        response['message'] = 'Your registration has been approved! Check your email for login credentials.'

    return json_response(response)


@registration_bp.route('/update/<request_id>', methods=['PUT'])
def update_registration(request_id):
    """
    Update a registration request (only if status is pending or more_info_needed)
    """
    reg_request = RegistrationRequest.query.filter_by(request_id=request_id).first()

    if not reg_request:
        return error_response('Registration request not found', 404)

    if reg_request.status not in ['pending', 'more_info_needed']:
        return error_response('Cannot update a processed registration request', 400)

    data = request.get_json()

    # Update allowed fields
    if 'applicant_name' in data:
        reg_request.applicant_name = data['applicant_name']
    if 'applicant_phone' in data:
        reg_request.applicant_phone = data['applicant_phone']
    if 'restaurant_name' in data:
        reg_request.restaurant_name = data['restaurant_name']
    if 'restaurant_description' in data:
        reg_request.restaurant_description = data['restaurant_description']
    if 'restaurant_address' in data:
        reg_request.restaurant_address = data['restaurant_address']
    if 'restaurant_phone' in data:
        reg_request.restaurant_phone = data['restaurant_phone']
    if 'restaurant_type' in data:
        reg_request.restaurant_type = data['restaurant_type']

    # If user was asked for more info, move back to pending
    if reg_request.status == 'more_info_needed':
        reg_request.status = 'pending'

    db.session.commit()

    return json_response(reg_request.to_dict(), 'Registration updated')


@registration_bp.route('/cancel/<request_id>', methods=['DELETE'])
def cancel_registration(request_id):
    """
    Cancel a pending registration request
    """
    reg_request = RegistrationRequest.query.filter_by(request_id=request_id).first()

    if not reg_request:
        return error_response('Registration request not found', 404)

    if reg_request.status not in ['pending', 'more_info_needed']:
        return error_response('Cannot cancel a processed registration request', 400)

    db.session.delete(reg_request)
    db.session.commit()

    return json_response(message='Registration request cancelled')

