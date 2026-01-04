from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Restaurant, Order, OrderItem, MenuItem, Table
from app.schemas import validate_required_fields, json_response, error_response, role_required
from datetime import datetime
import uuid

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('', methods=['GET'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def get_orders():
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    status = request.args.get('status')
    query = Order.query.filter_by(restaurant_id=user.restaurant.id)
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    return json_response([order.to_dict() for order in orders])

@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def get_order(order_id):
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant.id).first()
    if not order:
        return error_response('Order not found', 404)
    return json_response(order.to_dict())

@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def update_order_status(order_id):
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    validation = validate_required_fields(data, ['status'])
    if validation:
        return validation
    valid_statuses = ['pending', 'preparing', 'served', 'completed']
    if data['status'] not in valid_statuses:
        return error_response(f'Invalid status. Must be one of: {", ".join(valid_statuses)}', 400)
    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant.id).first()
    if not order:
        return error_response('Order not found', 404)
    order.status = data['status']
    db.session.commit()
    return json_response(order.to_dict(), 'Order status updated')

@orders_bp.route('/active', methods=['GET'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def get_active_orders():
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    orders = Order.query.filter(
        Order.restaurant_id == user.restaurant.id,
        Order.status.in_(['pending', 'preparing'])
    ).order_by(Order.created_at.asc()).all()
    return json_response([order.to_dict() for order in orders])

@orders_bp.route('/stats', methods=['GET'])
@jwt_required()
@role_required('restaurant_owner', 'system_admin')
def get_order_stats():
    identity = get_jwt_identity()
    user = User.query.filter_by(public_id=identity).first()
    if not user.restaurant:
        return error_response('No restaurant found', 404)
    today = datetime.utcnow().date()
    today_orders = Order.query.filter(
        Order.restaurant_id == user.restaurant.id,
        db.func.date(Order.created_at) == today
    ).all()
    total_orders = len(today_orders)
    total_revenue = sum(o.total_price for o in today_orders)
    pending = sum(1 for o in today_orders if o.status == 'pending')
    preparing = sum(1 for o in today_orders if o.status == 'preparing')
    completed = sum(1 for o in today_orders if o.status == 'completed')
    return json_response({
        'today_orders': total_orders,
        'today_revenue': total_revenue,
        'pending': pending,
        'preparing': preparing,
        'completed': completed
    })

@orders_bp.route('/create', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        validation = validate_required_fields(data, ['restaurant_id', 'table_number', 'items'])
        if validation:
            return validation

        restaurant = Restaurant.query.filter_by(public_id=data['restaurant_id']).first()
        if not restaurant or not restaurant.is_active:
            return error_response('Restaurant not found or inactive', 404)

        # Validate table and access token if provided
        table_number = data['table_number']
        access_token = data.get('access_token')

        if access_token:
            # If access token is provided, validate it
            table = Table.query.filter_by(restaurant_id=restaurant.id, table_number=table_number).first()
            if not table or table.access_token != access_token:
                return error_response('Invalid table access', 403)
        else:
            # If no access token, get or create the table
            table = Table.query.filter_by(restaurant_id=restaurant.id, table_number=table_number).first()
            if not table:
                # Create table if it doesn't exist
                table = Table(
                    restaurant_id=restaurant.id,
                    table_number=table_number,
                    access_token=str(uuid.uuid4())
                )
                db.session.add(table)
                db.session.flush()

        if not data['items'] or not isinstance(data['items'], list):
            return error_response('Items are required', 400)

        order = Order(
            table_number=data['table_number'],
            notes=data.get('notes'),
            restaurant_id=restaurant.id,
            order_source='qr',  # Mark as QR order for analytics
            order_type='dine_in'
        )
        db.session.add(order)
        db.session.flush()

        order.generate_order_number()  # Use the proper method to generate order number

        order_items_count = 0
        for item_data in data['items']:
            menu_item = MenuItem.query.get(item_data.get('menu_item_id'))
            if not menu_item or not menu_item.is_available:
                continue
            quantity = item_data.get('quantity', 1)
            order_item = OrderItem(
                menu_item_id=menu_item.id,
                quantity=quantity,
                unit_price=menu_item.price,
                subtotal=menu_item.price * quantity,
                notes=item_data.get('notes'),
                order_id=order.id
            )
            db.session.add(order_item)
            order_items_count += 1

        if order_items_count == 0:
            return error_response('No valid items in order', 400)

        db.session.flush()
        order.calculate_total()
        db.session.commit()

        return json_response(order.to_dict(), 'Order placed successfully', 201)
    except Exception as e:
        db.session.rollback()
        print(f"Order creation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f'Failed to create order: {str(e)}', 500)
