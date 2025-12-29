from flask import Blueprint, render_template, request, abort, jsonify
from app import db, limiter
from app.models import Restaurant, Table, Category

public_bp = Blueprint('public', __name__)


@public_bp.route('/api/health')
def health_check():
    """Health check endpoint for domain verification"""
    return jsonify({
        'status': 'healthy',
        'service': 'QR Restaurant Platform',
        'version': '1.0.0'
    })


@public_bp.route('/menu/<restaurant_id>')
@limiter.limit("60 per minute")
def view_menu(restaurant_id):
    """
    Public menu page - handles both:
    - Main QR code: /menu/{restaurant_id}
    - Table QR code: /menu/{restaurant_id}?table={num}&token={token}
    """
    restaurant = Restaurant.query.filter_by(public_id=restaurant_id).first()
    if not restaurant or not restaurant.is_active:
        abort(404)

    # Check if this is a table-specific request
    table_number = request.args.get('table', type=int)
    token = request.args.get('token')
    table = None

    if table_number and token:
        table = Table.query.filter_by(
            restaurant_id=restaurant.id,
            table_number=table_number
        ).first()
        if table and table.access_token != token:
            table = None  # Invalid token, treat as no table

    categories = Category.query.filter_by(
        restaurant_id=restaurant.id,
        is_active=True
    ).order_by(Category.sort_order).all()

    return render_template('public/menu.html',
        restaurant=restaurant,
        table=table,
        categories=categories,
        access_token=token if table else None
    )


@public_bp.route('/menu/<restaurant_id>/data')
@limiter.limit("60 per minute")
def get_menu_data(restaurant_id):
    """API endpoint to get menu data (for frontend integration)"""
    restaurant = Restaurant.query.filter_by(public_id=restaurant_id).first()
    if not restaurant or not restaurant.is_active:
        return {'success': False, 'error': 'Restaurant not found'}, 404

    table_number = request.args.get('table', type=int)
    token = request.args.get('token')
    table = None

    if table_number and token:
        table = Table.query.filter_by(
            restaurant_id=restaurant.id,
            table_number=table_number
        ).first()
        if table and table.access_token != token:
            table = None

    categories = Category.query.filter_by(
        restaurant_id=restaurant.id,
        is_active=True
    ).order_by(Category.sort_order).all()

    return {
        'success': True,
        'data': {
            'restaurant': restaurant.to_dict(),
            'table_number': table.table_number if table else None,
            'categories': [cat.to_dict() for cat in categories]
        }
    }


@public_bp.route('/payment/<order_id>')
def payment_page(order_id):
    """Payment page for an order"""
    from app.models import Order
    order = Order.query.filter_by(order_number=order_id).first()
    if not order:
        abort(404)

    return render_template('public/payment.html', order=order)


