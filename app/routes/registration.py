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
    """
    data = request.get_json()

    validation = validate_required_fields(data, ['applicant_name', 'applicant_email', 'restaurant_name'])
    if validation:
        return validation

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

    reg_request = RegistrationRequest(
        applicant_name=data['applicant_name'],
        applicant_email=data['applicant_email'],
        applicant_phone=data.get('applicant_phone'),
        restaurant_name=data['restaurant_name'],
        restaurant_description=data.get('restaurant_description'),
        restaurant_address=data.get('restaurant_address'),
        restaurant_phone=data.get('restaurant_phone'),
        restaurant_type=data.get('restaurant_type'),
        status='pending',
        priority='normal'
    )

    db.session.add(reg_request)
    db.session.commit()

    return json_response({
        'request_id': reg_request.request_id,
        'status': reg_request.status,
        'message': 'Your registration request has been submitted successfully. You will be notified once it has been reviewed.'
    }, 'Registration submitted', 201)


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

