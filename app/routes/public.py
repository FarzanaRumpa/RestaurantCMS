"""
Public Routes Module
Handles all public-facing routes (no authentication required)

Routes:
- Homepage and marketing website
- Restaurant menu viewing (QR code access)
- Contact form submission
- Health check endpoint
"""
from flask import Blueprint, render_template, request, abort, jsonify
from app import db, limiter
from app.models import Restaurant, Table, Category, Order
from app.models.contact_models import ContactMessage
from app.validation.contact_validation import ContactFormValidator
from datetime import datetime, timedelta

# Initialize blueprint
public_bp = Blueprint('public', __name__)


# ============================================================================
# MARKETING WEBSITE ROUTES
# ============================================================================

@public_bp.route('/')
def homepage():
    """
    Public homepage - SaaS marketing website

    Displays dynamic content from website content APIs including:
    - Hero sections
    - Features
    - How it works
    - Pricing plans
    - Testimonials
    - FAQs
    - Contact form

    Returns:
        Rendered homepage template
    """
    return render_template('public/index.html')


@public_bp.route('/api/contact', methods=['POST'])
@limiter.limit("3 per hour")
def submit_contact_form():
    """
    Submit contact form from public website

    Rate limited to 3 submissions per hour per IP to prevent spam.
    Includes validation, spam detection, and duplicate prevention.

    Request Body (JSON or Form):
        name (str): Contact name (required, 2-100 chars)
        email (str): Email address (required, valid format)
        phone (str): Phone number (optional)
        subject (str): Message subject (optional, max 200 chars)
        message (str): Message content (required, 10-5000 chars)

    Returns:
        201: Contact message created successfully
        400: Validation failed
        429: Rate limit exceeded or duplicate submission
        500: Server error
    """
    try:
        # Parse request data
        data = request.get_json() if request.is_json else request.form.to_dict()

        # Sanitize all inputs to prevent XSS
        data['name'] = ContactFormValidator.sanitize_input(data.get('name', ''))
        data['email'] = ContactFormValidator.sanitize_input(data.get('email', ''))
        data['phone'] = ContactFormValidator.sanitize_input(data.get('phone', ''))
        data['subject'] = ContactFormValidator.sanitize_input(data.get('subject', ''))
        data['message'] = ContactFormValidator.sanitize_input(data.get('message', ''))

        # Validate input fields
        is_valid, errors = ContactFormValidator.validate_contact_form(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }), 400

        # Check for spam patterns
        is_spam, spam_reason = ContactFormValidator.check_spam(data)

        # Prevent duplicate submissions (same email within 1 hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_submission = ContactMessage.query.filter(
            ContactMessage.email == data['email'],
            ContactMessage.created_at >= one_hour_ago
        ).first()

        if recent_submission:
            return jsonify({
                'success': False,
                'message': 'You have already submitted a message recently. Please wait before submitting again.'
            }), 429

        # Create contact message record
        contact = ContactMessage(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            subject=data.get('subject'),
            message=data['message'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500],
            referrer=request.headers.get('Referer', '')[:500],
            is_spam=is_spam,
            status='spam' if is_spam else 'new'
        )

        db.session.add(contact)
        db.session.commit()

        # Return success response (same message for spam to avoid revealing detection)
        return jsonify({
            'success': True,
            'message': 'Thank you for contacting us! We will get back to you soon.',
            'id': contact.id if not is_spam else None
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again later.'
        }), 500


# ============================================================================
# RESTAURANT MENU ROUTES (QR Code Access)
# ============================================================================

@public_bp.route('/menu/<restaurant_id>')
@limiter.limit("60 per minute")
def view_menu(restaurant_id):
    """
    Public restaurant menu page accessed via QR code

    Supports two modes:
    1. Restaurant QR: /menu/{restaurant_id}
    2. Table QR: /menu/{restaurant_id}?table={num}&token={token}

    Args:
        restaurant_id: Public ID of the restaurant
        table (query param): Table number (optional)
        token (query param): Table access token (optional)

    Returns:
        Rendered menu page or 404 if restaurant not found/inactive
    """
    # Find restaurant by public ID
    restaurant = Restaurant.query.filter_by(public_id=restaurant_id).first()
    if not restaurant or not restaurant.is_active:
        abort(404)

    # Check for table-specific access
    table_number = request.args.get('table', type=int)
    token = request.args.get('token')
    table = None

    if table_number and token:
        table = Table.query.filter_by(
            restaurant_id=restaurant.id,
            table_number=table_number
        ).first()
        # Validate table access token
        if table and table.access_token != token:
            table = None  # Invalid token, treat as no table

    # Get active menu categories
    categories = Category.query.filter_by(
        restaurant_id=restaurant.id,
        is_active=True
    ).order_by(Category.sort_order).all()

    return render_template(
        'public/menu.html',
        restaurant=restaurant,
        table=table,
        categories=categories,
        access_token=token if table else None
    )


@public_bp.route('/menu/<restaurant_id>/data')
@limiter.limit("60 per minute")
def get_menu_data(restaurant_id):
    """
    API endpoint to get menu data (for AJAX/frontend integration)

    Returns restaurant info, categories, and menu items as JSON.
    Used by frontend for dynamic menu loading.

    Args:
        restaurant_id: Public ID of the restaurant
        table (query param): Table number (optional)
        token (query param): Table access token (optional)

    Returns:
        JSON response with menu data or error
    """
    # Find restaurant
    restaurant = Restaurant.query.filter_by(public_id=restaurant_id).first()
    if not restaurant or not restaurant.is_active:
        return jsonify({
            'success': False,
            'error': 'Restaurant not found'
        }), 404

    # Check table access
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

    # Get menu categories
    categories = Category.query.filter_by(
        restaurant_id=restaurant.id,
        is_active=True
    ).order_by(Category.sort_order).all()

    return jsonify({
        'success': True,
        'data': {
            'restaurant': restaurant.to_dict(),
            'table_number': table.table_number if table else None,
            'categories': [cat.to_dict() for cat in categories]
        }
    })


# ============================================================================
# PAYMENT ROUTES
# ============================================================================

@public_bp.route('/payment/<order_id>')
def payment_page(order_id):
    """
    Payment page for an order

    Displays order summary and payment options.
    Accessed after customer places an order from menu.

    Args:
        order_id: Order number/ID

    Returns:
        Rendered payment page or 404 if order not found
    """
    order = Order.query.filter_by(order_number=order_id).first()
    if not order:
        abort(404)

    return render_template('public/payment.html', order=order)


# ============================================================================
# UTILITY ROUTES
# ============================================================================

@public_bp.route('/api/health')
def health_check():
    """
    Health check endpoint for monitoring and domain verification

    Used by:
    - Uptime monitoring services
    - Domain SSL verification
    - Load balancers

    Returns:
        JSON with service status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'QR Restaurant Platform',
        'version': '1.0.0'
    })


