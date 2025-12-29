from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Restaurant, Table
from app.schemas import validate_required_fields, json_response, error_response, role_required
from app.services.qr_service import generate_qr_code, generate_restaurant_qr_code
import uuid

restaurants_bp = Blueprint('restaurants', __name__)

@restaurants_bp.route('', methods=['POST'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def create_restaurant():
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if user.restaurant:
        return error_response('You already have a restaurant', 400)
    validation = validate_required_fields(data, ['name'])
    if validation:
        return validation
    restaurant = Restaurant(
        name=data['name'],
        description=data.get('description'),
        address=data.get('address'),
        phone=data.get('phone'),
        owner_id=user.id
    )
    db.session.add(restaurant)
    db.session.commit()
    return json_response(restaurant.to_dict(), 'Restaurant created', 201)

@restaurants_bp.route('', methods=['GET'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def get_restaurant():
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    return json_response(user.restaurant.to_dict())

@restaurants_bp.route('', methods=['PUT'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def update_restaurant():
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    restaurant = user.restaurant
    if 'name' in data:
        restaurant.name = data['name']
    if 'description' in data:
        restaurant.description = data['description']
    if 'address' in data:
        restaurant.address = data['address']
    if 'phone' in data:
        restaurant.phone = data['phone']
    db.session.commit()
    return json_response(restaurant.to_dict(), 'Restaurant updated')

@restaurants_bp.route('/tables', methods=['GET'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def get_tables():
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    tables = [table.to_dict() for table in user.restaurant.tables]
    return json_response(tables)

@restaurants_bp.route('/tables', methods=['POST'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def create_table():
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    validation = validate_required_fields(data, ['table_number'])
    if validation:
        return validation
    existing = Table.query.filter_by(restaurant_id=user.restaurant.id, table_number=data['table_number']).first()
    if existing:
        return error_response('Table number already exists', 400)
    table = Table(table_number=data['table_number'], restaurant_id=user.restaurant.id)
    db.session.add(table)
    db.session.commit()
    qr_filename = generate_qr_code(user.restaurant.public_id, table.table_number, table.access_token)
    table.qr_code_path = qr_filename
    db.session.commit()
    return json_response(table.to_dict(), 'Table created', 201)

@restaurants_bp.route('/tables/<int:table_number>', methods=['DELETE'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def delete_table(table_number):
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    table = Table.query.filter_by(restaurant_id=user.restaurant.id, table_number=table_number).first()
    if not table:
        return error_response('Table not found', 404)
    db.session.delete(table)
    db.session.commit()
    return json_response(message='Table deleted')

@restaurants_bp.route('/tables/<int:table_number>/regenerate-qr', methods=['POST'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def regenerate_qr(table_number):
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    table = Table.query.filter_by(restaurant_id=user.restaurant.id, table_number=table_number).first()
    if not table:
        return error_response('Table not found', 404)
    table.access_token = str(uuid.uuid4())[:12]
    qr_filename = generate_qr_code(user.restaurant.public_id, table.table_number, table.access_token)
    table.qr_code_path = qr_filename
    db.session.commit()
    return json_response(table.to_dict(), 'QR code regenerated')


# ==================== RESTAURANT QR CODE ENDPOINTS ====================

@restaurants_bp.route('/qr-code', methods=['GET'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def get_restaurant_qr():
    """Get the restaurant's main QR code"""
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)

    restaurant = user.restaurant

    # Generate QR code if it doesn't exist
    if not restaurant.qr_code_path:
        qr_filename = generate_restaurant_qr_code(restaurant.public_id, restaurant.name)
        restaurant.qr_code_path = qr_filename
        db.session.commit()

    return json_response({
        'restaurant_id': restaurant.public_id,
        'restaurant_name': restaurant.name,
        'qr_code_url': f'/static/qrcodes/{restaurant.qr_code_path}',
        'menu_url': f'/public/restaurant/{restaurant.public_id}'
    })


@restaurants_bp.route('/qr-code/generate', methods=['POST'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def generate_restaurant_qr():
    """Generate or regenerate the restaurant's main QR code"""
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)

    restaurant = user.restaurant

    # Generate new QR code
    qr_filename = generate_restaurant_qr_code(restaurant.public_id, restaurant.name)
    restaurant.qr_code_path = qr_filename
    db.session.commit()

    return json_response({
        'restaurant_id': restaurant.public_id,
        'restaurant_name': restaurant.name,
        'qr_code_url': f'/static/qrcodes/{restaurant.qr_code_path}',
        'menu_url': f'/public/restaurant/{restaurant.public_id}'
    }, 'QR code generated successfully')

