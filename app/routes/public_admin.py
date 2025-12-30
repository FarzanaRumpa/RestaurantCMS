"""
Public Module Routes
Handles all public-facing routes for the admin panel
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from app.routes.admin import admin_required, get_current_admin_user, has_permission
from app.services.public_service import PublicService
from app.controllers.public_controller import PublicController
from app.validation.public_validation import PublicValidator

public_admin_bp = Blueprint('public_admin', __name__, url_prefix='/public')

@public_admin_bp.route('/')
@admin_required
def index():
    """Public section dashboard"""
    user = get_current_admin_user()

    # Use service layer to get data
    stats = PublicService.get_public_stats()
    recent_restaurants = PublicService.get_recent_active_restaurants(limit=10)

    return render_template('admin/public.html',
        total_restaurants=stats['total_restaurants'],
        total_menu_items=stats['total_menu_items'],
        total_categories=stats['total_categories'],
        recent_active_restaurants=recent_restaurants
    )

@public_admin_bp.route('/restaurants')
@admin_required
def list_restaurants():
    """List all public restaurants with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')

    result = PublicController.list_public_restaurants(page, per_page, search)

    return render_template('admin/public/restaurants.html', **result)

@public_admin_bp.route('/restaurants/<int:restaurant_id>')
@admin_required
def restaurant_detail(restaurant_id):
    """View public restaurant details"""
    restaurant = PublicController.get_restaurant_detail(restaurant_id)

    if not restaurant:
        return jsonify({'error': 'Restaurant not found'}), 404

    return render_template('admin/public/restaurant_detail.html', restaurant=restaurant)

@public_admin_bp.route('/analytics')
@admin_required
def analytics():
    """Public analytics and statistics"""
    analytics_data = PublicService.get_public_analytics()

    return render_template('admin/public/analytics.html', analytics=analytics_data)

@public_admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for public statistics"""
    stats = PublicService.get_public_stats()
    return jsonify(stats)

@public_admin_bp.route('/api/trending')
@admin_required
def api_trending():
    """API endpoint for trending items"""
    trending = PublicService.get_trending_items(limit=10)
    return jsonify(trending)

@public_admin_bp.route('/api/search', methods=['POST'])
@admin_required
def api_search():
    """API endpoint for public search"""
    data = request.get_json()

    # Validate request
    is_valid, errors = PublicValidator.validate_search_request(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    results = PublicController.search_public_content(
        query=data.get('query'),
        filters=data.get('filters', {})
    )

    return jsonify(results)

