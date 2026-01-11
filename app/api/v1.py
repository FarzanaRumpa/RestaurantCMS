"""
API v1 Routes
=============
Versioned API endpoints with standardized responses.

This blueprint implements:
1. Versioned API paths (/api/v1/...)
2. Standardized error responses
3. Consistent pagination
4. Rate limit headers
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
import logging

from app import db
from app.api.versioning import (
    api_version, api_response, PaginatedResponse,
    APIError, ValidationError, NotFoundError, AuthenticationError, AuthorizationError,
    API_VERSION_1
)
from app.services.operational_safety import restaurant_rate_limit, feature_flag_required

logger = logging.getLogger(__name__)

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')


# =============================================================================
# AUTHENTICATION MIDDLEWARE
# =============================================================================

def api_key_required(f):
    """Require valid API key for access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.models import ApiKey

        api_key = request.headers.get('X-API-Key')
        if not api_key:
            raise AuthenticationError("API key required")

        key = ApiKey.query.filter_by(token=api_key, is_active=True).first()
        if not key:
            raise AuthenticationError("Invalid API key")

        g.api_key = key
        g.restaurant_id = key.restaurant_id

        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# RESTAURANT ENDPOINTS
# =============================================================================

@api_v1_bp.route('/restaurants/<public_id>', methods=['GET'])
@api_version(API_VERSION_1)
@api_key_required
def get_restaurant(public_id):
    """Get restaurant details"""
    from app.models import Restaurant

    restaurant = Restaurant.query.filter_by(public_id=public_id).first()
    if not restaurant:
        raise NotFoundError('Restaurant', public_id)

    # Check authorization
    if restaurant.id != g.restaurant_id:
        raise AuthorizationError("Cannot access other restaurant's data")

    return api_response(data=restaurant.to_dict())


@api_v1_bp.route('/restaurants/<public_id>/menu', methods=['GET'])
@api_version(API_VERSION_1)
@api_key_required
def get_menu(public_id):
    """Get restaurant menu with categories and items"""
    from app.models import Restaurant, Category

    restaurant = Restaurant.query.filter_by(public_id=public_id).first()
    if not restaurant:
        raise NotFoundError('Restaurant', public_id)

    if restaurant.id != g.restaurant_id:
        raise AuthorizationError()

    categories = Category.query.filter_by(
        restaurant_id=restaurant.id,
        is_active=True
    ).order_by(Category.sort_order).all()

    return api_response(data={
        'restaurant_id': public_id,
        'categories': [cat.to_dict() for cat in categories]
    })


# =============================================================================
# ORDER ENDPOINTS
# =============================================================================

@api_v1_bp.route('/orders', methods=['GET'])
@api_version(API_VERSION_1)
@api_key_required
@restaurant_rate_limit('api_call')
def list_orders():
    """List orders with pagination"""
    from app.models import Order

    page, per_page = PaginatedResponse.get_pagination_params()

    query = Order.query.filter_by(restaurant_id=g.restaurant_id)

    # Apply filters
    status = request.args.get('status')
    if status:
        query = query.filter(Order.status == status)

    date_from = request.args.get('date_from')
    if date_from:
        query = query.filter(Order.created_at >= date_from)

    date_to = request.args.get('date_to')
    if date_to:
        query = query.filter(Order.created_at <= date_to)

    # Order by created_at desc
    query = query.order_by(Order.created_at.desc())

    result = PaginatedResponse.paginate(query, page, per_page)
    return api_response(data=result['data'], meta={'pagination': result['pagination']})


@api_v1_bp.route('/orders/<order_id>', methods=['GET'])
@api_version(API_VERSION_1)
@api_key_required
def get_order(order_id):
    """Get order details"""
    from app.models import Order

    # Try internal order ID first, then legacy order number
    order = Order.query.filter_by(
        internal_order_id=order_id,
        restaurant_id=g.restaurant_id
    ).first()

    if not order:
        order = Order.query.filter_by(
            order_number=order_id,
            restaurant_id=g.restaurant_id
        ).first()

    if not order:
        raise NotFoundError('Order', order_id)

    return api_response(data=order.to_dict())


@api_v1_bp.route('/orders', methods=['POST'])
@api_version(API_VERSION_1)
@api_key_required
@restaurant_rate_limit('order_create')
def create_order():
    """Create a new order"""
    from app.models import Order, OrderItem, MenuItem

    data = request.get_json()
    if not data:
        raise ValidationError("Request body required")

    # Validate required fields
    required = ['table_number', 'items']
    for field in required:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}", field=field)

    if not data['items'] or not isinstance(data['items'], list):
        raise ValidationError("Items must be a non-empty array", field='items')

    # Create order
    order = Order(
        restaurant_id=g.restaurant_id,
        table_number=data['table_number'],
        notes=data.get('notes'),
        order_source='api',
        order_type=data.get('order_type', 'dine_in')
    )

    # Add items
    total = 0
    for item_data in data['items']:
        menu_item = MenuItem.query.get(item_data.get('menu_item_id'))
        if not menu_item:
            raise ValidationError(f"Menu item not found: {item_data.get('menu_item_id')}")

        quantity = item_data.get('quantity', 1)
        order_item = OrderItem(
            menu_item_id=menu_item.id,
            quantity=quantity,
            unit_price=menu_item.price,
            subtotal=menu_item.price * quantity,
            notes=item_data.get('notes')
        )
        order.items.append(order_item)
        total += order_item.subtotal

    order.total_price = total

    db.session.add(order)
    db.session.flush()

    # Allocate display number
    order.allocate_display_number()

    db.session.commit()

    logger.info(f"Order created via API: {order.internal_order_id}")

    return api_response(
        data=order.to_dict(),
        message="Order created successfully",
        status_code=201
    )


@api_v1_bp.route('/orders/<order_id>/status', methods=['PATCH'])
@api_version(API_VERSION_1)
@api_key_required
def update_order_status(order_id):
    """Update order status"""
    from app.models import Order

    order = Order.query.filter_by(
        internal_order_id=order_id,
        restaurant_id=g.restaurant_id
    ).first()

    if not order:
        raise NotFoundError('Order', order_id)

    data = request.get_json()
    if not data or 'status' not in data:
        raise ValidationError("Status field required", field='status')

    valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'served', 'completed', 'cancelled']
    if data['status'] not in valid_statuses:
        raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}", field='status')

    old_status = order.status
    order.status = data['status']

    # Release display number if order is completed/cancelled
    if data['status'] in ['completed', 'cancelled']:
        order.release_display_number()

    db.session.commit()

    logger.info(f"Order {order_id} status changed: {old_status} -> {data['status']}")

    return api_response(data=order.to_dict(), message="Order status updated")


# =============================================================================
# MENU ENDPOINTS
# =============================================================================

@api_v1_bp.route('/categories', methods=['GET'])
@api_version(API_VERSION_1)
@api_key_required
def list_categories():
    """List menu categories"""
    from app.models import Category

    page, per_page = PaginatedResponse.get_pagination_params()

    query = Category.query.filter_by(
        restaurant_id=g.restaurant_id
    ).order_by(Category.sort_order)

    result = PaginatedResponse.paginate(query, page, per_page)
    return api_response(data=result['data'], meta={'pagination': result['pagination']})


@api_v1_bp.route('/menu-items', methods=['GET'])
@api_version(API_VERSION_1)
@api_key_required
def list_menu_items():
    """List menu items with pagination"""
    from app.models import MenuItem, Category

    page, per_page = PaginatedResponse.get_pagination_params()

    query = MenuItem.query.join(Category).filter(
        Category.restaurant_id == g.restaurant_id
    )

    # Apply filters
    category_id = request.args.get('category_id')
    if category_id:
        query = query.filter(MenuItem.category_id == category_id)

    available_only = request.args.get('available', 'true').lower() == 'true'
    if available_only:
        query = query.filter(MenuItem.is_available == True)

    result = PaginatedResponse.paginate(query, page, per_page)
    return api_response(data=result['data'], meta={'pagination': result['pagination']})


@api_v1_bp.route('/menu-items/<int:item_id>', methods=['PATCH'])
@api_version(API_VERSION_1)
@api_key_required
@restaurant_rate_limit('menu_update')
def update_menu_item(item_id):
    """Update a menu item"""
    from app.models import MenuItem, Category

    item = MenuItem.query.join(Category).filter(
        MenuItem.id == item_id,
        Category.restaurant_id == g.restaurant_id
    ).first()

    if not item:
        raise NotFoundError('MenuItem', str(item_id))

    data = request.get_json()
    if not data:
        raise ValidationError("Request body required")

    # Update allowed fields
    allowed_fields = ['name', 'description', 'price', 'is_available', 'image_url']
    for field in allowed_fields:
        if field in data:
            setattr(item, field, data[field])

    db.session.commit()

    return api_response(data=item.to_dict(), message="Menu item updated")


# =============================================================================
# TABLES ENDPOINTS
# =============================================================================

@api_v1_bp.route('/tables', methods=['GET'])
@api_version(API_VERSION_1)
@api_key_required
def list_tables():
    """List restaurant tables"""
    from app.models import Table

    tables = Table.query.filter_by(
        restaurant_id=g.restaurant_id,
        is_active=True
    ).order_by(Table.table_number).all()

    return api_response(data=[t.to_dict() for t in tables])


# =============================================================================
# HEALTH & INFO ENDPOINTS
# =============================================================================

@api_v1_bp.route('/health', methods=['GET'])
@api_version(API_VERSION_1)
def health_check():
    """API health check endpoint"""
    from app.services.observability import HealthCheck

    health = HealthCheck.get_system_health()
    status_code = 200 if health['status'] == 'healthy' else 503

    return jsonify(health), status_code


@api_v1_bp.route('/info', methods=['GET'])
@api_version(API_VERSION_1)
def api_info():
    """API information and version"""
    from app.api.versioning import CURRENT_API_VERSION, SUPPORTED_VERSIONS

    return api_response(data={
        'version': CURRENT_API_VERSION,
        'supported_versions': SUPPORTED_VERSIONS,
        'documentation_url': '/api/v1/docs',
        'rate_limits': {
            'orders': '100/minute',
            'menu_updates': '30/minute',
            'general': '1000/hour'
        }
    })


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@api_v1_bp.errorhandler(APIError)
def handle_api_error(error):
    """Handle API errors"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@api_v1_bp.errorhandler(Exception)
def handle_generic_error(error):
    """Handle unexpected errors"""
    logger.error(f"Unexpected API error: {error}", exc_info=True)
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred',
            'request_id': getattr(g, 'correlation_id', None)
        }
    }), 500

