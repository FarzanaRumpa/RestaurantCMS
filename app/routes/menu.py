from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Category, MenuItem
from app.schemas import validate_required_fields, json_response, error_response, role_required

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/categories', methods=['GET'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def get_categories():
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    categories = Category.query.filter_by(restaurant_id=user.restaurant.id).order_by(Category.sort_order).all()
    return json_response([cat.to_dict() for cat in categories])

@menu_bp.route('/categories', methods=['POST'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def create_category():
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    validation = validate_required_fields(data, ['name'])
    if validation:
        return validation
    category = Category(
        name=data['name'],
        description=data.get('description'),
        sort_order=data.get('sort_order', 0),
        restaurant_id=user.restaurant.id
    )
    db.session.add(category)
    db.session.commit()
    return json_response(category.to_dict(), 'Category created', 201)

@menu_bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def update_category(category_id):
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    category = Category.query.filter_by(id=category_id, restaurant_id=user.restaurant.id).first()
    if not category:
        return error_response('Category not found', 404)
    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'sort_order' in data:
        category.sort_order = data['sort_order']
    if 'is_active' in data:
        category.is_active = data['is_active']
    db.session.commit()
    return json_response(category.to_dict(), 'Category updated')

@menu_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def delete_category(category_id):
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    category = Category.query.filter_by(id=category_id, restaurant_id=user.restaurant.id).first()
    if not category:
        return error_response('Category not found', 404)
    db.session.delete(category)
    db.session.commit()
    return json_response(message='Category deleted')

@menu_bp.route('/items', methods=['GET'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def get_items():
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    items = MenuItem.query.join(Category).filter(Category.restaurant_id == user.restaurant.id).all()
    return json_response([item.to_dict() for item in items])

@menu_bp.route('/items', methods=['POST'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def create_item():
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    validation = validate_required_fields(data, ['name', 'price', 'category_id'])
    if validation:
        return validation
    category = Category.query.filter_by(id=data['category_id'], restaurant_id=user.restaurant.id).first()
    if not category:
        return error_response('Category not found', 404)
    item = MenuItem(
        name=data['name'],
        description=data.get('description'),
        price=float(data['price']),
        is_available=data.get('is_available', True),
        image_url=data.get('image_url'),
        category_id=category.id
    )
    db.session.add(item)
    db.session.commit()
    return json_response(item.to_dict(), 'Item created', 201)

@menu_bp.route('/items/<int:item_id>', methods=['PUT'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def update_item(item_id):
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    item = MenuItem.query.join(Category).filter(MenuItem.id == item_id, Category.restaurant_id == user.restaurant.id).first()
    if not item:
        return error_response('Item not found', 404)
    if 'name' in data:
        item.name = data['name']
    if 'description' in data:
        item.description = data['description']
    if 'price' in data:
        item.price = float(data['price'])
    if 'is_available' in data:
        item.is_available = data['is_available']
    if 'image_url' in data:
        item.image_url = data['image_url']
    db.session.commit()
    return json_response(item.to_dict(), 'Item updated')

@menu_bp.route('/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def delete_item(item_id):
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    item = MenuItem.query.join(Category).filter(MenuItem.id == item_id, Category.restaurant_id == user.restaurant.id).first()
    if not item:
        return error_response('Item not found', 404)
    db.session.delete(item)
    db.session.commit()
    return json_response(message='Item deleted')
