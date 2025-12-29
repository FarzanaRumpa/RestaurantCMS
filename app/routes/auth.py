from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from app import db, limiter
from app.models import User
from app.schemas import validate_required_fields, json_response, error_response

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for domain verification"""
    return jsonify({
        'status': 'healthy',
        'service': 'QR Restaurant Platform',
        'version': '1.0.0'
    })


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    data = request.get_json()

    validation = validate_required_fields(data, ['username', 'email', 'password'])
    if validation:
        return validation

    if User.query.filter_by(username=data['username']).first():
        return error_response('Username already exists', 400)

    if User.query.filter_by(email=data['email']).first():
        return error_response('Email already exists', 400)

    user = User(
        username=data['username'],
        email=data['email'],
        role='restaurant_owner'
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(
        identity=user.public_id,
        additional_claims={'role': user.role}
    )
    refresh_token = create_refresh_token(identity=user.public_id)

    return json_response({
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }, 'Registration successful', 201)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("20 per hour")
def login():
    data = request.get_json()

    validation = validate_required_fields(data, ['username', 'password'])
    if validation:
        return validation

    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        return error_response('Invalid credentials', 401)

    if not user.is_active:
        return error_response('Account is disabled', 403)

    access_token = create_access_token(
        identity=user.public_id,
        additional_claims={'role': user.role}
    )
    refresh_token = create_refresh_token(identity=user.public_id)

    return json_response({
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }, 'Login successful')

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()

    if not user or not user.is_active:
        return error_response('Invalid user', 401)

    access_token = create_access_token(
        identity=user.public_id,
        additional_claims={'role': user.role}
    )

    return json_response({'access_token': access_token})

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()

    if not user:
        return error_response('User not found', 404)

    return json_response(user.to_dict())

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.get_json()

    validation = validate_required_fields(data, ['current_password', 'new_password'])
    if validation:
        return validation

    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()

    if not user.check_password(data['current_password']):
        return error_response('Current password is incorrect', 400)

    user.set_password(data['new_password'])
    db.session.commit()

    return json_response(message='Password changed successfully')

