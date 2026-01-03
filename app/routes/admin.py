from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, g, send_file, make_response
from functools import wraps
from app import db
from app.models import User, Restaurant, Order, Category, Table, MenuItem, ApiKey, RegistrationRequest, ModerationLog
from app.services.qr_service import generate_restaurant_qr_code, generate_qr_code
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import uuid

admin_bp = Blueprint('admin', __name__)

# Role hierarchy: superadmin > admin > moderator
ADMIN_ROLES = ['superadmin', 'admin', 'moderator', 'system_admin']  # system_admin is legacy, treated as superadmin

# Role permissions mapping
ROLE_PERMISSIONS = {
    'superadmin': ['dashboard', 'restaurants', 'users', 'orders', 'registrations', 'api_keys', 'settings', 'user_management'],
    'system_admin': ['dashboard', 'restaurants', 'users', 'orders', 'registrations', 'api_keys', 'settings', 'user_management'],  # Legacy
    'admin': ['dashboard', 'restaurants', 'orders', 'registrations'],
    'moderator': ['dashboard', 'registrations'],
}

def get_current_admin_user():
    """Get the current logged in admin user - ADMIN ONLY"""
    if session.get('admin_logged_in') and session.get('admin_user_id'):
        user = User.query.get(session.get('admin_user_id'))
        # Only return if user is actually an admin role
        if user and user.role in ADMIN_ROLES:
            return user
    return None

def get_current_owner():
    """Get the current logged in restaurant owner - OWNER ONLY"""
    if session.get('owner_logged_in') and session.get('owner_user_id'):
        user = User.query.get(session.get('owner_user_id'))
        # Only return if user is actually a restaurant owner
        if user and user.role == 'restaurant_owner' and user.is_active:
            return user
    return None

def has_permission(permission):
    """Check if current user has a specific permission"""
    user = get_current_admin_user()
    if not user:
        return False
    role = user.role
    # Legacy system_admin is treated as superadmin
    if role == 'system_admin':
        role = 'superadmin'
    return permission in ROLE_PERMISSIONS.get(role, [])

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        user = get_current_admin_user()
        if not user or user.role not in ADMIN_ROLES:
            flash('Access denied', 'error')
            return redirect(url_for('admin.login'))
        g.admin_user = user
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    """Decorator for restaurant owner-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('owner_logged_in'):
            flash('Please login to access your restaurant', 'error')
            return redirect(url_for('admin.owner_login'))
        user = get_current_owner()
        if not user:
            session.clear()
            flash('Session expired. Please login again', 'error')
            return redirect(url_for('admin.owner_login'))
        g.owner_user = user
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """Decorator to check for specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logged_in'):
                return redirect(url_for('admin.login'))
            user = get_current_admin_user()
            if not user or user.role not in ADMIN_ROLES:
                flash('Access denied', 'error')
                return redirect(url_for('admin.login'))

            role = user.role
            if role == 'system_admin':
                role = 'superadmin'

            if permission not in ROLE_PERMISSIONS.get(role, []):
                flash('You do not have permission to access this page', 'error')
                return redirect(url_for('admin.dashboard'))

            g.admin_user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def superadmin_required(f):
    """Only superadmin/system_admin can access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        user = get_current_admin_user()
        if not user or user.role not in ['superadmin', 'system_admin']:
            flash('Only superadmin can access this page', 'error')
            return redirect(url_for('admin.dashboard'))
        g.admin_user = user
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login - for superadmin, admin, moderator only"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Only allow admin roles (not restaurant_owner)
        user = User.query.filter_by(username=username).filter(User.role.in_(['superadmin', 'system_admin', 'admin', 'moderator'])).first()
        if user and user.check_password(password) and user.is_active:
            session['admin_logged_in'] = True
            session['admin_user_id'] = user.id
            session['admin_role'] = user.role
            flash(f'Welcome, {user.username}!', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Invalid credentials or account disabled', 'error')
    return render_template('admin/login.html')

@admin_bp.route('/owner-login', methods=['GET', 'POST'])
def owner_login():
    """Restaurant owner login - separate from admin login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Only allow restaurant_owner role
        user = User.query.filter_by(username=username, role='restaurant_owner').first()
        if user and user.check_password(password) and user.is_active:
            session['owner_logged_in'] = True
            session['admin_logged_in'] = True
            session['admin_user_id'] = user.id
            session['admin_role'] = user.role
            session['owner_user_id'] = user.id
            flash(f'Welcome, {user.username}!', 'success')
            return redirect(url_for('admin.restaurant_owner_view'))
        flash('Invalid username or password', 'error')
    return render_template('admin/owner_login_new.html')

@admin_bp.route('/owner-signup', methods=['POST'])
def owner_signup():
    """Restaurant owner signup with package selection"""
    from datetime import datetime, timedelta
    try:
        # Get form data
        restaurant_name = request.form.get('restaurant_name')
        owner_name = request.form.get('owner_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        username = request.form.get('username')
        password = request.form.get('password')
        pricing_plan_id = request.form.get('pricing_plan_id')
        country_code = request.form.get('country_code', 'US')

        # Validation
        if not all([restaurant_name, owner_name, email, username, password, pricing_plan_id]):
            flash('All required fields must be filled', 'error')
            return redirect(url_for('admin.owner_login'))

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('admin.owner_login'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('admin.owner_login'))

        # Create user
        user = User(
            username=username,
            email=email,
            phone=phone,
            role='restaurant_owner',
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user ID

        # Create restaurant with pricing plan
        restaurant = Restaurant(
            name=restaurant_name,
            phone=phone,
            owner_id=user.id,
            is_active=True,
            pricing_plan_id=int(pricing_plan_id),
            country_code=country_code.upper() if country_code else 'US',
            subscription_start_date=datetime.utcnow(),
            is_trial=True,
            trial_ends_at=datetime.utcnow() + timedelta(days=14)  # 14-day trial
        )
        db.session.add(restaurant)
        db.session.commit()

        # Log them in automatically
        session['owner_logged_in'] = True
        session['admin_logged_in'] = True
        session['admin_user_id'] = user.id
        session['admin_role'] = user.role
        session['owner_user_id'] = user.id

        flash(f'Welcome to RestaurantPro, {owner_name}! Your account has been created successfully.', 'success')
        return redirect(url_for('admin.restaurant_owner_view'))

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during signup: {str(e)}', 'error')
        return redirect(url_for('admin.owner_login'))

@admin_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page for restaurant owners"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        user = User.query.filter_by(username=username, email=email, role='restaurant_owner').first()
        if user:
            flash('Password reset request received. Administrator will contact you shortly.', 'success')
        else:
            flash('If your account exists, administrator will contact you.', 'info')
        return redirect(url_for('admin.owner_login'))
    return render_template('admin/forgot_password.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_user_id', None)
    session.pop('admin_role', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/owner-logout')
def owner_logout():
    """Restaurant owner logout"""
    session.pop('owner_logged_in', None)
    session.pop('owner_user_id', None)
    session.pop('owner_role', None)
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('admin.owner_login'))

@admin_bp.route('/restaurant')
@admin_required
def restaurant_owner_view():
    """Restaurant owner view - read-only access to their restaurant"""
    user = get_current_admin_user()

    # Only restaurant owners can access this
    if user.role != 'restaurant_owner':
        flash('This page is for restaurant owners only', 'error')
        return redirect(url_for('admin.dashboard'))

    # Check if user has a restaurant
    if not user.restaurant:
        flash('You do not have a restaurant yet. Please contact admin.', 'error')
        return redirect(url_for('admin.dashboard'))

    restaurant = user.restaurant

    # Get restaurant statistics
    total_orders = Order.query.filter_by(restaurant_id=restaurant.id).count()
    pending_orders = Order.query.filter_by(restaurant_id=restaurant.id, status='pending').count()
    today = datetime.utcnow().date()
    today_orders = Order.query.filter(
        Order.restaurant_id == restaurant.id,
        db.func.date(Order.created_at) == today
    ).count()

    # Get categories and menu items
    categories = Category.query.filter_by(restaurant_id=restaurant.id).order_by(Category.sort_order).all()
    total_items = sum(len(cat.items) for cat in categories)

    # Get tables
    tables = Table.query.filter_by(restaurant_id=restaurant.id).all()

    return render_template('admin/restaurant_owner.html',
        user=user,
        restaurant=restaurant,
        total_orders=total_orders,
        pending_orders=pending_orders,
        today_orders=today_orders,
        categories=categories,
        total_items=total_items,
        tables=tables
    )

@admin_bp.route('/')
@admin_required
def dashboard():
    user = get_current_admin_user()

    # Redirect restaurant owners to their restaurant page
    if user.role == 'restaurant_owner':
        return redirect(url_for('admin.restaurant_owner_view'))

    today = datetime.utcnow().date()
    total_restaurants = Restaurant.query.count()
    active_restaurants = Restaurant.query.filter_by(is_active=True).count()
    total_orders = Order.query.count()
    today_orders = Order.query.filter(db.func.date(Order.created_at) == today).count()
    pending_orders = Order.query.filter_by(status='pending').count()
    total_users = User.query.filter_by(role='restaurant_owner').count()
    total_tables = Table.query.count()
    pending_registrations = RegistrationRequest.query.filter_by(status='pending').count()

    recent_restaurants = Restaurant.query.order_by(Restaurant.created_at.desc()).limit(5).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
        total_restaurants=total_restaurants,
        active_restaurants=active_restaurants,
        total_orders=total_orders,
        today_orders=today_orders,
        pending_orders=pending_orders,
        total_users=total_users,
        total_tables=total_tables,
        pending_registrations=pending_registrations,
        recent_restaurants=recent_restaurants,
        recent_orders=recent_orders
    )

@admin_bp.route('/public')
@admin_required
def public():
    """Public section - accessible to all admin roles"""
    user = get_current_admin_user()

    # Redirect restaurant owners to their restaurant page
    if user.role == 'restaurant_owner':
        return redirect(url_for('admin.restaurant_owner_view'))

    # Get contact messages stats
    from app.models.contact_models import ContactMessage
    new_messages = ContactMessage.query.filter_by(status='new').count()

    return render_template('admin/public.html',
        new_messages=new_messages
    )

@admin_bp.route('/contact-messages')
@admin_required
def contact_messages():
    """View and manage contact form submissions"""
    from app.models.contact_models import ContactMessage

    # Get filter parameters
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Build query
    query = ContactMessage.query

    if status == 'new':
        query = query.filter_by(status='new')
    elif status == 'read':
        query = query.filter_by(status='read')
    elif status == 'replied':
        query = query.filter_by(status='replied')
    elif status == 'spam':
        query = query.filter_by(is_spam=True)
    elif status == 'not_spam':
        query = query.filter_by(is_spam=False)

    # Paginate
    pagination = query.order_by(ContactMessage.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Get stats
    stats = {
        'total': ContactMessage.query.count(),
        'new': ContactMessage.query.filter_by(status='new').count(),
        'read': ContactMessage.query.filter_by(status='read').count(),
        'replied': ContactMessage.query.filter_by(status='replied').count(),
        'spam': ContactMessage.query.filter_by(is_spam=True).count()
    }

    return render_template('admin/contact_messages.html',
        messages=pagination.items,
        pagination=pagination,
        stats=stats,
        current_status=status
    )

@admin_bp.route('/contact-messages/<int:id>')
@admin_required
def view_contact_message(id):
    """View single contact message"""
    from app.models.contact_models import ContactMessage

    message = ContactMessage.query.get_or_404(id)

    # Mark as read if it's new
    if message.status == 'new':
        message.status = 'read'
        db.session.commit()

    return render_template('admin/contact_message_detail.html', message=message)

@admin_bp.route('/contact-messages/<int:id>/update-status', methods=['POST'])
@admin_required
def update_message_status(id):
    """Update contact message status"""
    from app.models.contact_models import ContactMessage

    message = ContactMessage.query.get_or_404(id)
    new_status = request.form.get('status')

    if new_status in ['new', 'read', 'replied', 'archived', 'spam']:
        message.status = new_status

        if new_status == 'replied':
            user = get_current_admin_user()
            message.replied_at = datetime.utcnow()
            message.replied_by_id = user.id

        db.session.commit()
        flash(f'Message status updated to {new_status}', 'success')
    else:
        flash('Invalid status', 'error')

    return redirect(url_for('admin.view_contact_message', id=id))

@admin_bp.route('/contact-messages/<int:id>/add-note', methods=['POST'])
@admin_required
def add_message_note(id):
    """Add admin note to contact message"""
    from app.models.contact_models import ContactMessage

    message = ContactMessage.query.get_or_404(id)
    note = request.form.get('note')

    if note and note.strip():
        message.admin_notes = note.strip()
        db.session.commit()
        flash('Note added successfully', 'success')
    else:
        flash('Note cannot be empty', 'error')

    return redirect(url_for('admin.view_contact_message', id=id))

@admin_bp.route('/contact-messages/<int:id>/mark-spam', methods=['POST'])
@admin_required
def mark_message_spam(id):
    """Mark/unmark message as spam"""
    from app.models.contact_models import ContactMessage

    message = ContactMessage.query.get_or_404(id)
    message.is_spam = not message.is_spam

    if message.is_spam:
        message.status = 'spam'
        flash('Message marked as spam', 'success')
    else:
        message.status = 'read'
        flash('Message unmarked as spam', 'success')

    db.session.commit()
    return redirect(url_for('admin.view_contact_message', id=id))

@admin_bp.route('/contact-messages/<int:id>/delete', methods=['POST'])
@admin_required
def delete_contact_message(id):
    """Delete contact message"""
    from app.models.contact_models import ContactMessage

    message = ContactMessage.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()

    flash('Message deleted successfully', 'success')
    return redirect(url_for('admin.contact_messages'))

# ============================================================================
# WEBSITE CONTENT MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route('/hero-sections')
@admin_required
def hero_sections():
    """Manage hero sections"""
    from app.models.website_content_models import HeroSection
    hero_sections = HeroSection.query.order_by(HeroSection.display_order, HeroSection.created_at.desc()).all()
    return render_template('admin/website_content/hero_sections.html', hero_sections=hero_sections)

@admin_bp.route('/hero-sections/create', methods=['POST'])
@admin_required
def create_hero_section():
    """Create new hero section"""
    from app.models.website_content_models import HeroSection
    user = get_current_admin_user()

    hero = HeroSection(
        title=request.form.get('title'),
        subtitle=request.form.get('subtitle'),
        cta_text=request.form.get('cta_text'),
        cta_link=request.form.get('cta_link'),
        background_image=request.form.get('background_image'),
        display_order=int(request.form.get('display_order', 0)),
        is_active=request.form.get('is_active') == '1',
        created_by_id=user.id
    )
    db.session.add(hero)
    db.session.commit()
    flash('Hero section created successfully', 'success')
    return redirect(url_for('admin.hero_sections'))

@admin_bp.route('/hero-sections/<int:id>/edit', methods=['POST'])
@admin_required
def edit_hero_section(id):
    """Edit hero section"""
    from app.models.website_content_models import HeroSection
    hero = HeroSection.query.get_or_404(id)

    hero.title = request.form.get('title')
    hero.subtitle = request.form.get('subtitle')
    hero.cta_text = request.form.get('cta_text')
    hero.cta_link = request.form.get('cta_link')
    hero.display_order = int(request.form.get('display_order', 0))
    hero.is_active = request.form.get('is_active') == '1'

    # Handle file upload
    if 'background_image_file' in request.files:
        file = request.files['background_image_file']
        if file and file.filename:
            # Validate file extension
            allowed_extensions = {'jpg', 'jpeg', 'png', 'webp'}
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

            if ext in allowed_extensions:
                # Create unique filename
                unique_filename = f"hero_{uuid.uuid4().hex}_{filename}"

                # Ensure upload directory exists
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'hero')
                os.makedirs(upload_dir, exist_ok=True)

                # Save file
                filepath = os.path.join(upload_dir, unique_filename)
                file.save(filepath)

                # Set background_image to the URL path
                hero.background_image = f"/static/uploads/hero/{unique_filename}"

    # If URL is provided and no file uploaded, use URL
    if not hero.background_image or (request.form.get('background_image') and 'background_image_file' not in request.files):
        url_image = request.form.get('background_image')
        if url_image:
            hero.background_image = url_image

    db.session.commit()
    flash('Hero section updated successfully', 'success')
    return redirect(url_for('admin.hero_sections'))

@admin_bp.route('/hero-sections/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_hero_section(id):
    """Toggle hero section status"""
    from app.models.website_content_models import HeroSection
    hero = HeroSection.query.get_or_404(id)
    hero.is_active = not hero.is_active
    db.session.commit()
    flash(f'Hero section {"activated" if hero.is_active else "deactivated"}', 'success')
    return redirect(url_for('admin.hero_sections'))

@admin_bp.route('/features')
@admin_required
def features():
    """Manage features"""
    from app.models.website_content_models import Feature
    features = Feature.query.order_by(Feature.display_order, Feature.created_at.desc()).all()
    return render_template('admin/website_content/features.html', features=features)

@admin_bp.route('/features/create', methods=['POST'])
@admin_required
def create_feature():
    """Create new feature"""
    from app.models.website_content_models import Feature
    user = get_current_admin_user()

    feature = Feature(
        title=request.form.get('title'),
        description=request.form.get('description'),
        icon=request.form.get('icon'),
        link=request.form.get('link'),
        display_order=int(request.form.get('display_order', 0)),
        is_active=request.form.get('is_active') == '1',
        created_by_id=user.id
    )
    db.session.add(feature)
    db.session.commit()
    flash('Feature created successfully', 'success')
    return redirect(url_for('admin.features'))

@admin_bp.route('/features/<int:id>/edit', methods=['POST'])
@admin_required
def edit_feature(id):
    """Edit feature"""
    from app.models.website_content_models import Feature
    feature = Feature.query.get_or_404(id)

    feature.title = request.form.get('title')
    feature.description = request.form.get('description')
    feature.icon = request.form.get('icon')
    feature.link = request.form.get('link')
    feature.display_order = int(request.form.get('display_order', 0))
    feature.is_active = request.form.get('is_active') == '1'

    db.session.commit()
    flash('Feature updated successfully', 'success')
    return redirect(url_for('admin.features'))

@admin_bp.route('/features/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_feature(id):
    """Toggle feature status"""
    from app.models.website_content_models import Feature
    feature = Feature.query.get_or_404(id)
    feature.is_active = not feature.is_active
    db.session.commit()
    flash(f'Feature {"activated" if feature.is_active else "deactivated"}', 'success')
    return redirect(url_for('admin.features'))

# ============================================================================
# PRICING PLANS MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route('/pricing-plans')
@admin_required
def pricing_plans():
    """Manage pricing plans"""
    from app.models.website_content_models import PricingPlan
    import json
    import time

    plans = PricingPlan.query.order_by(PricingPlan.display_order, PricingPlan.created_at.desc()).all()

    # Parse features JSON for display - use a separate list to avoid ORM modification
    plans_data = []
    for plan in plans:
        features_list = []
        if plan.features and isinstance(plan.features, str):
            try:
                features_list = json.loads(plan.features)
            except:
                # If JSON parsing fails, try splitting by newline
                features_list = [f.strip() for f in plan.features.split('\n') if f.strip()]

        plans_data.append({
            'plan': plan,
            'features_list': features_list,
            'features_json': plan.features  # Keep original for edit form
        })

    # Add cache-busting timestamp
    cache_buster = int(time.time())

    # Get all countries by tier for display
    countries_by_tier = PricingPlan.get_all_countries_by_tier()

    response = make_response(render_template('admin/website_content/pricing_plans.html',
                         plans_data=plans_data,
                         countries_by_tier=countries_by_tier,
                         cache_version=cache_buster))

    # Disable all caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response

@admin_bp.route('/pricing-plans/create', methods=['POST'])
@admin_required
def create_pricing_plan():
    """Create new pricing plan"""
    from app.models.website_content_models import PricingPlan
    import json
    user = get_current_admin_user()

    # Get features as JSON array
    features_list = request.form.getlist('features[]')
    features_json = json.dumps(features_list) if features_list else '[]'

    plan = PricingPlan(
        name=request.form.get('name'),
        description=request.form.get('description'),
        price=float(request.form.get('price', 0)),
        price_tier2=float(request.form.get('price_tier2')) if request.form.get('price_tier2') else None,
        price_tier3=float(request.form.get('price_tier3')) if request.form.get('price_tier3') else None,
        price_tier4=float(request.form.get('price_tier4')) if request.form.get('price_tier4') else None,
        price_period=request.form.get('price_period', 'month'),
        currency=request.form.get('currency', 'USD'),
        features=features_json,
        is_highlighted=request.form.get('is_highlighted') == '1',
        display_order=int(request.form.get('display_order', 0)),
        badge_text=request.form.get('badge_text') or None,
        cta_text=request.form.get('cta_text', 'Get Started'),
        cta_link=request.form.get('cta_link', '/owner/login'),
        # Limits
        max_tables=int(request.form.get('max_tables')) if request.form.get('max_tables') else None,
        max_menu_items=int(request.form.get('max_menu_items')) if request.form.get('max_menu_items') else None,
        max_categories=int(request.form.get('max_categories')) if request.form.get('max_categories') else None,
        max_orders_per_month=int(request.form.get('max_orders_per_month')) if request.form.get('max_orders_per_month') else None,
        max_restaurants=int(request.form.get('max_restaurants')) if request.form.get('max_restaurants') else None,
        max_staff_accounts=int(request.form.get('max_staff_accounts')) if request.form.get('max_staff_accounts') else None,
        # Feature toggles
        has_kitchen_display=request.form.get('has_kitchen_display') == '1',
        has_customer_display=request.form.get('has_customer_display') == '1',
        has_owner_dashboard=request.form.get('has_owner_dashboard') == '1',
        has_advanced_analytics=request.form.get('has_advanced_analytics') == '1',
        has_qr_ordering=request.form.get('has_qr_ordering') == '1',
        has_table_management=request.form.get('has_table_management') == '1',
        has_order_history=request.form.get('has_order_history') == '1',
        has_customer_feedback=request.form.get('has_customer_feedback') == '1',
        has_inventory_management=request.form.get('has_inventory_management') == '1',
        has_staff_management=request.form.get('has_staff_management') == '1',
        has_multi_language=request.form.get('has_multi_language') == '1',
        has_custom_branding=request.form.get('has_custom_branding') == '1',
        has_email_notifications=request.form.get('has_email_notifications') == '1',
        has_sms_notifications=request.form.get('has_sms_notifications') == '1',
        has_api_access=request.form.get('has_api_access') == '1',
        has_priority_support=request.form.get('has_priority_support') == '1',
        has_white_label=request.form.get('has_white_label') == '1',
        has_reports_export=request.form.get('has_reports_export') == '1',
        has_pos_integration=request.form.get('has_pos_integration') == '1',
        has_payment_integration=request.form.get('has_payment_integration') == '1',
        is_active=request.form.get('is_active') == '1',
        created_by_id=user.id
    )
    db.session.add(plan)
    db.session.commit()
    flash('Pricing plan created successfully', 'success')
    return redirect(url_for('admin.pricing_plans'))

@admin_bp.route('/pricing-plans/<int:id>/edit', methods=['POST'])
@admin_required
def edit_pricing_plan(id):
    """Edit pricing plan"""
    from app.models.website_content_models import PricingPlan
    import json
    plan = PricingPlan.query.get_or_404(id)

    features_list = request.form.getlist('features[]')
    features_json = json.dumps(features_list) if features_list else '[]'

    plan.name = request.form.get('name')
    plan.description = request.form.get('description')
    plan.price = float(request.form.get('price', 0))
    plan.price_tier2 = float(request.form.get('price_tier2')) if request.form.get('price_tier2') else None
    plan.price_tier3 = float(request.form.get('price_tier3')) if request.form.get('price_tier3') else None
    plan.price_tier4 = float(request.form.get('price_tier4')) if request.form.get('price_tier4') else None
    plan.price_period = request.form.get('price_period', 'month')
    plan.currency = request.form.get('currency', 'USD')
    plan.features = features_json
    plan.is_highlighted = request.form.get('is_highlighted') == '1'
    plan.display_order = int(request.form.get('display_order', 0))
    plan.badge_text = request.form.get('badge_text') or None
    plan.cta_text = request.form.get('cta_text', 'Get Started')
    plan.cta_link = request.form.get('cta_link', '/owner/login')
    # Limits
    plan.max_tables = int(request.form.get('max_tables')) if request.form.get('max_tables') else None
    plan.max_menu_items = int(request.form.get('max_menu_items')) if request.form.get('max_menu_items') else None
    plan.max_categories = int(request.form.get('max_categories')) if request.form.get('max_categories') else None
    plan.max_orders_per_month = int(request.form.get('max_orders_per_month')) if request.form.get('max_orders_per_month') else None
    plan.max_restaurants = int(request.form.get('max_restaurants')) if request.form.get('max_restaurants') else None
    plan.max_staff_accounts = int(request.form.get('max_staff_accounts')) if request.form.get('max_staff_accounts') else None
    # Feature toggles
    plan.has_kitchen_display = request.form.get('has_kitchen_display') == '1'
    plan.has_customer_display = request.form.get('has_customer_display') == '1'
    plan.has_owner_dashboard = request.form.get('has_owner_dashboard') == '1'
    plan.has_advanced_analytics = request.form.get('has_advanced_analytics') == '1'
    plan.has_qr_ordering = request.form.get('has_qr_ordering') == '1'
    plan.has_table_management = request.form.get('has_table_management') == '1'
    plan.has_order_history = request.form.get('has_order_history') == '1'
    plan.has_customer_feedback = request.form.get('has_customer_feedback') == '1'
    plan.has_inventory_management = request.form.get('has_inventory_management') == '1'
    plan.has_staff_management = request.form.get('has_staff_management') == '1'
    plan.has_multi_language = request.form.get('has_multi_language') == '1'
    plan.has_custom_branding = request.form.get('has_custom_branding') == '1'
    plan.has_email_notifications = request.form.get('has_email_notifications') == '1'
    plan.has_sms_notifications = request.form.get('has_sms_notifications') == '1'
    plan.has_api_access = request.form.get('has_api_access') == '1'
    plan.has_priority_support = request.form.get('has_priority_support') == '1'
    plan.has_white_label = request.form.get('has_white_label') == '1'
    plan.has_reports_export = request.form.get('has_reports_export') == '1'
    plan.has_pos_integration = request.form.get('has_pos_integration') == '1'
    plan.has_payment_integration = request.form.get('has_payment_integration') == '1'
    plan.is_active = request.form.get('is_active') == '1'

    db.session.commit()
    flash('Pricing plan updated successfully', 'success')
    return redirect(url_for('admin.pricing_plans'))

@admin_bp.route('/pricing-plans/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_pricing_plan(id):
    """Toggle pricing plan status"""
    from app.models.website_content_models import PricingPlan
    plan = PricingPlan.query.get_or_404(id)
    plan.is_active = not plan.is_active
    db.session.commit()
    flash(f'Pricing plan {"activated" if plan.is_active else "deactivated"}', 'success')
    return redirect(url_for('admin.pricing_plans'))

@admin_bp.route('/pricing-plans/<int:id>/delete', methods=['POST'])
@admin_required
def delete_pricing_plan(id):
    """Delete pricing plan"""
    from app.models.website_content_models import PricingPlan
    plan = PricingPlan.query.get_or_404(id)
    db.session.delete(plan)
    db.session.commit()
    flash('Pricing plan deleted successfully', 'success')
    return redirect(url_for('admin.pricing_plans'))


# ============================================================================
# PAYMENT GATEWAY MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route('/payment-gateways')
@admin_required
def payment_gateways():
    """Manage payment gateways"""
    from app.models.website_content_models import PaymentGateway, PaymentTransaction
    gateways = PaymentGateway.query.order_by(PaymentGateway.display_order).all()

    # Get recent transactions
    recent_transactions = PaymentTransaction.query.order_by(
        PaymentTransaction.created_at.desc()
    ).limit(10).all()

    # Get transaction stats
    from sqlalchemy import func
    stats = {
        'total_transactions': PaymentTransaction.query.count(),
        'successful_transactions': PaymentTransaction.query.filter_by(status='completed').count(),
        'total_revenue': db.session.query(func.sum(PaymentTransaction.amount)).filter_by(status='completed').scalar() or 0
    }

    return render_template('admin/website_content/payment_gateways.html',
                         gateways=gateways,
                         recent_transactions=recent_transactions,
                         stats=stats)


@admin_bp.route('/payment-gateways/init', methods=['POST'])
@admin_required
def init_payment_gateways():
    """Initialize default payment gateways (PayPal and Stripe)"""
    from app.models.website_content_models import PaymentGateway
    user = get_current_admin_user()

    # Create PayPal if not exists
    if not PaymentGateway.query.filter_by(name='paypal').first():
        paypal = PaymentGateway(
            name='paypal',
            display_name='PayPal',
            description='Pay securely with PayPal. Credit cards, debit cards, and PayPal balance accepted.',
            icon='bi-paypal',
            is_sandbox=True,
            is_active=False,
            display_order=1,
            supported_currencies='USD,EUR,GBP,CAD,AUD',
            created_by_id=user.id
        )
        db.session.add(paypal)

    # Create Stripe if not exists
    if not PaymentGateway.query.filter_by(name='stripe').first():
        stripe = PaymentGateway(
            name='stripe',
            display_name='Stripe',
            description='Pay securely with credit or debit card via Stripe.',
            icon='bi-credit-card-2-front',
            is_sandbox=True,
            is_active=False,
            display_order=2,
            supported_currencies='USD,EUR,GBP,CAD,AUD,JPY,SGD',
            created_by_id=user.id
        )
        db.session.add(stripe)

    db.session.commit()
    flash('Payment gateways initialized successfully', 'success')
    return redirect(url_for('admin.payment_gateways'))


@admin_bp.route('/payment-gateways/<int:id>/update', methods=['POST'])
@admin_required
def update_payment_gateway(id):
    """Update payment gateway settings"""
    from app.models.website_content_models import PaymentGateway
    gateway = PaymentGateway.query.get_or_404(id)

    # Update basic info
    gateway.display_name = request.form.get('display_name', gateway.display_name)
    gateway.description = request.form.get('description', gateway.description)
    gateway.is_sandbox = request.form.get('is_sandbox') == '1'
    gateway.is_active = request.form.get('is_active') == '1'
    gateway.supported_currencies = request.form.get('supported_currencies', 'USD')
    gateway.transaction_fee_percent = float(request.form.get('transaction_fee_percent', 0) or 0)

    # Update gateway-specific credentials
    if gateway.name == 'paypal':
        gateway.paypal_client_id = request.form.get('paypal_client_id', '')
        gateway.paypal_client_secret = request.form.get('paypal_client_secret', '')
        gateway.paypal_sandbox_client_id = request.form.get('paypal_sandbox_client_id', '')
        gateway.paypal_sandbox_client_secret = request.form.get('paypal_sandbox_client_secret', '')
    elif gateway.name == 'stripe':
        gateway.stripe_publishable_key = request.form.get('stripe_publishable_key', '')
        gateway.stripe_secret_key = request.form.get('stripe_secret_key', '')
        gateway.stripe_sandbox_publishable_key = request.form.get('stripe_sandbox_publishable_key', '')
        gateway.stripe_sandbox_secret_key = request.form.get('stripe_sandbox_secret_key', '')

    gateway.webhook_secret = request.form.get('webhook_secret', '')

    db.session.commit()
    flash(f'{gateway.display_name} settings updated successfully', 'success')
    return redirect(url_for('admin.payment_gateways'))


@admin_bp.route('/payment-gateways/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_payment_gateway(id):
    """Toggle payment gateway active status"""
    from app.models.website_content_models import PaymentGateway
    gateway = PaymentGateway.query.get_or_404(id)
    gateway.is_active = not gateway.is_active
    db.session.commit()
    flash(f'{gateway.display_name} {"enabled" if gateway.is_active else "disabled"}', 'success')
    return redirect(url_for('admin.payment_gateways'))


@admin_bp.route('/payment-gateways/<int:id>/delete', methods=['POST'])
@admin_required
def delete_payment_gateway(id):
    """Delete payment gateway"""
    from app.models.website_content_models import PaymentGateway
    gateway = PaymentGateway.query.get_or_404(id)
    name = gateway.display_name
    db.session.delete(gateway)
    db.session.commit()
    flash(f'{name} deleted successfully', 'success')
    return redirect(url_for('admin.payment_gateways'))


# ============================================================================
# TESTIMONIALS MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route('/testimonials')
@admin_required
def testimonials():
    """Manage testimonials"""
    from app.models.website_content_models import Testimonial
    testimonials = Testimonial.query.order_by(Testimonial.display_order, Testimonial.created_at.desc()).all()
    return render_template('admin/website_content/testimonials.html', testimonials=testimonials)

@admin_bp.route('/testimonials/create', methods=['POST'])
@admin_required
def create_testimonial():
    """Create new testimonial"""
    from app.models.website_content_models import Testimonial
    user = get_current_admin_user()

    testimonial = Testimonial(
        customer_name=request.form.get('customer_name'),
        customer_role=request.form.get('customer_role'),
        company_name=request.form.get('company_name'),
        message=request.form.get('message'),
        rating=int(request.form.get('rating', 5)),
        avatar_url=request.form.get('avatar_url'),
        is_featured=request.form.get('is_featured') == '1',
        display_order=int(request.form.get('display_order', 0)),
        is_active=request.form.get('is_active') == '1',
        created_by_id=user.id
    )
    db.session.add(testimonial)
    db.session.commit()
    flash('Testimonial created successfully', 'success')
    return redirect(url_for('admin.testimonials'))

@admin_bp.route('/testimonials/<int:id>/edit', methods=['POST'])
@admin_required
def edit_testimonial(id):
    """Edit testimonial"""
    from app.models.website_content_models import Testimonial
    testimonial = Testimonial.query.get_or_404(id)

    testimonial.customer_name = request.form.get('customer_name')
    testimonial.customer_role = request.form.get('customer_role')
    testimonial.company_name = request.form.get('company_name')
    testimonial.message = request.form.get('message')
    testimonial.rating = int(request.form.get('rating', 5))
    testimonial.avatar_url = request.form.get('avatar_url')
    testimonial.is_featured = request.form.get('is_featured') == '1'
    testimonial.display_order = int(request.form.get('display_order', 0))
    testimonial.is_active = request.form.get('is_active') == '1'

    db.session.commit()
    flash('Testimonial updated successfully', 'success')
    return redirect(url_for('admin.testimonials'))

@admin_bp.route('/testimonials/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_testimonial(id):
    """Toggle testimonial status"""
    from app.models.website_content_models import Testimonial
    testimonial = Testimonial.query.get_or_404(id)
    testimonial.is_active = not testimonial.is_active
    db.session.commit()
    flash(f'Testimonial {"activated" if testimonial.is_active else "deactivated"}', 'success')
    return redirect(url_for('admin.testimonials'))

@admin_bp.route('/testimonials/<int:id>/delete', methods=['POST'])
@admin_required
def delete_testimonial(id):
    """Delete testimonial"""
    from app.models.website_content_models import Testimonial
    testimonial = Testimonial.query.get_or_404(id)
    db.session.delete(testimonial)
    db.session.commit()
    flash('Testimonial deleted successfully', 'success')
    return redirect(url_for('admin.testimonials'))

# ============================================================================
# HOW IT WORKS MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route('/how-it-works')
@admin_required
def how_it_works():
    """Manage how it works steps"""
    from app.models.website_content_models import HowItWorksStep
    steps = HowItWorksStep.query.order_by(HowItWorksStep.step_number).all()
    return render_template('admin/website_content/how_it_works.html', steps=steps)

@admin_bp.route('/how-it-works/create', methods=['POST'])
@admin_required
def create_how_it_works_step():
    """Create new how it works step"""
    from app.models.website_content_models import HowItWorksStep
    user = get_current_admin_user()

    step = HowItWorksStep(
        step_number=int(request.form.get('step_number', 1)),
        title=request.form.get('title'),
        description=request.form.get('description'),
        icon=request.form.get('icon'),
        is_active=request.form.get('is_active') == '1',
        created_by_id=user.id
    )
    db.session.add(step)
    db.session.commit()
    flash('Step created successfully', 'success')
    return redirect(url_for('admin.how_it_works'))

@admin_bp.route('/how-it-works/<int:id>/edit', methods=['POST'])
@admin_required
def edit_how_it_works_step(id):
    """Edit how it works step"""
    from app.models.website_content_models import HowItWorksStep
    step = HowItWorksStep.query.get_or_404(id)

    step.step_number = int(request.form.get('step_number', 1))
    step.title = request.form.get('title')
    step.description = request.form.get('description')
    step.icon = request.form.get('icon')
    step.is_active = request.form.get('is_active') == '1'

    db.session.commit()
    flash('Step updated successfully', 'success')
    return redirect(url_for('admin.how_it_works'))

@admin_bp.route('/how-it-works/<int:id>/delete', methods=['POST'])
@admin_required
def delete_how_it_works_step(id):
    """Delete how it works step"""
    from app.models.website_content_models import HowItWorksStep
    step = HowItWorksStep.query.get_or_404(id)
    db.session.delete(step)
    db.session.commit()
    flash('Step deleted successfully', 'success')
    return redirect(url_for('admin.how_it_works'))

@admin_bp.route('/restaurants')
@permission_required('restaurants')
def restaurants():
    restaurants = Restaurant.query.order_by(Restaurant.created_at.desc()).all()
    return render_template('admin/restaurants.html', restaurants=restaurants)

@admin_bp.route('/restaurants/create', methods=['POST'])
@admin_required
def create_restaurant():
    # Get owner details
    owner_username = request.form.get('owner_username')
    owner_email = request.form.get('owner_email')
    owner_phone = request.form.get('owner_phone')
    owner_password = request.form.get('owner_password')
    owner_password_confirm = request.form.get('owner_password_confirm')

    # Get restaurant details
    restaurant_name = request.form.get('restaurant_name')
    restaurant_phone = request.form.get('restaurant_phone')
    restaurant_address = request.form.get('restaurant_address')
    restaurant_description = request.form.get('restaurant_description')

    # Validation
    if owner_password != owner_password_confirm:
        flash('Passwords do not match', 'error')
        return redirect(url_for('admin.restaurants'))

    if len(owner_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('admin.restaurants'))

    if User.query.filter_by(username=owner_username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('admin.restaurants'))

    if User.query.filter_by(email=owner_email).first():
        flash('Email already exists', 'error')
        return redirect(url_for('admin.restaurants'))

    current_admin = get_current_admin_user()

    # Create owner
    owner = User(
        username=owner_username,
        email=owner_email,
        phone=owner_phone,
        role='restaurant_owner',
        created_by_id=current_admin.id
    )
    owner.set_password(owner_password)
    db.session.add(owner)
    db.session.flush()

    # Create restaurant
    restaurant = Restaurant(
        name=restaurant_name,
        phone=restaurant_phone,
        address=restaurant_address,
        description=restaurant_description,
        owner_id=owner.id
    )
    db.session.add(restaurant)
    db.session.commit()

    flash(f'Restaurant "{restaurant_name}" created successfully with owner "{owner_username}"', 'success')
    return redirect(url_for('admin.restaurants'))

@admin_bp.route('/restaurants/<int:restaurant_id>/toggle', methods=['POST'])
@admin_required
def toggle_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    restaurant.is_active = not restaurant.is_active
    db.session.commit()
    flash(f'Restaurant {"enabled" if restaurant.is_active else "disabled"}', 'success')
    return redirect(url_for('admin.restaurants'))

@admin_bp.route('/restaurants/<int:restaurant_id>/generate-qr', methods=['POST'])
@admin_required
def generate_restaurant_qr_admin(restaurant_id):
    """Generate or regenerate QR code for a restaurant"""
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    qr_filename = generate_restaurant_qr_code(restaurant.public_id, restaurant.name)
    restaurant.qr_code_path = qr_filename
    db.session.commit()
    flash('QR code generated successfully', 'success')
    return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

@admin_bp.route('/restaurants/<int:restaurant_id>/qr-code')
@admin_required
def download_restaurant_qr(restaurant_id):
    """Download the restaurant QR code"""
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    if not restaurant.qr_code_path:
        flash('No QR code available. Please generate one first.', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

    qr_path = os.path.join(current_app.config['QR_CODE_FOLDER'], restaurant.qr_code_path)
    if os.path.exists(qr_path):
        return send_file(qr_path, as_attachment=True, download_name=f'{restaurant.name}_qr_code.png')

    flash('QR code file not found. Please regenerate.', 'error')
    return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

@admin_bp.route('/restaurants/<int:restaurant_id>')
@admin_required
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    orders = Order.query.filter_by(restaurant_id=restaurant_id).order_by(Order.created_at.desc()).limit(20).all()
    categories = Category.query.filter_by(restaurant_id=restaurant_id).all()
    total_menu_items = sum(len(cat.items) for cat in categories)
    return render_template('admin/restaurant_detail.html', restaurant=restaurant, orders=orders, categories=categories, total_menu_items=total_menu_items)

@admin_bp.route('/restaurants/<int:restaurant_id>/categories/create', methods=['POST'])
@admin_required
def create_restaurant_category(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    name = request.form.get('name')
    description = request.form.get('description')
    sort_order = request.form.get('sort_order')
    is_active = True if request.form.get('is_active') == 'on' else False

    if not name:
        flash('Category name is required', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

    try:
        sort_order = int(sort_order) if sort_order else 0
    except ValueError:
        sort_order = 0

    category = Category(
        name=name,
        description=description,
        sort_order=sort_order,
        is_active=is_active,
        restaurant_id=restaurant.id
    )
    db.session.add(category)
    db.session.commit()
    flash('Category created', 'success')
    return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

@admin_bp.route('/restaurants/<int:restaurant_id>/items/create', methods=['POST'])
@admin_required
def create_restaurant_item(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    category_id = request.form.get('category_id')
    is_available = True if request.form.get('is_available') == 'on' else False

    if not name or not price or not category_id:
        flash('Name, price and category are required', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

    # Ensure category belongs to this restaurant
    category = Category.query.filter_by(id=category_id, restaurant_id=restaurant.id).first()
    if not category:
        flash('Selected category not found for this restaurant', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

    try:
        price = float(price)
    except ValueError:
        flash('Invalid price', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

    image_url = None
    image = request.files.get('image')
    if image and image.filename:
        filename = secure_filename(image.filename)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        allowed = {'png', 'jpg', 'jpeg', 'gif'}
        if ext not in allowed:
            flash('Invalid image format', 'error')
            return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))
        # ensure upload folder exists
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'menu_images')
        os.makedirs(upload_folder, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex[:8]}.{ext}"
        save_path = os.path.join(upload_folder, unique_name)
        image.save(save_path)
        image_url = f"/static/uploads/menu_images/{unique_name}"

    item = MenuItem(
        name=name,
        description=description,
        price=price,
        is_available=is_available,
        image_url=image_url,
        category_id=category.id
    )
    db.session.add(item)
    db.session.commit()
    flash('Menu item created', 'success')
    return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

@admin_bp.route('/restaurants/<int:restaurant_id>/categories/<int:category_id>/toggle', methods=['POST'])
@admin_required
def toggle_category(restaurant_id, category_id):
    category = Category.query.filter_by(id=category_id, restaurant_id=restaurant_id).first_or_404()
    category.is_active = not category.is_active
    db.session.commit()
    flash(f'Category {"enabled" if category.is_active else "disabled"}', 'success')
    return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

@admin_bp.route('/restaurants/<int:restaurant_id>/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(restaurant_id, category_id):
    category = Category.query.filter_by(id=category_id, restaurant_id=restaurant_id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted', 'success')
    return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

@admin_bp.route('/restaurants/<int:restaurant_id>/items/<int:item_id>/toggle', methods=['POST'])
@admin_required
def toggle_item(restaurant_id, item_id):
    item = MenuItem.query.get_or_404(item_id)
    # Verify item belongs to restaurant
    if item.category.restaurant_id != restaurant_id:
        flash('Item not found', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))
    item.is_available = not item.is_available
    db.session.commit()
    flash(f'Item {"enabled" if item.is_available else "disabled"}', 'success')
    return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

@admin_bp.route('/restaurants/<int:restaurant_id>/items/<int:item_id>/delete', methods=['POST'])
@admin_required
def delete_item(restaurant_id, item_id):
    item = MenuItem.query.get_or_404(item_id)
    # Verify item belongs to restaurant
    if item.category.restaurant_id != restaurant_id:
        flash('Item not found', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted', 'success')
    return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))


@admin_bp.route('/restaurants/<int:restaurant_id>/import-menu', methods=['POST'])
@admin_required
def import_menu_csv(restaurant_id):
    """
    Import menu items from CSV file.
    Expected CSV format: category,name,description,price,is_available
    """
    import csv
    import io

    restaurant = Restaurant.query.get_or_404(restaurant_id)

    if 'csv_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

    file = request.files['csv_file']

    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        csv_reader = csv.DictReader(stream)

        # Validate required headers
        required_headers = ['category', 'name', 'price']
        headers = csv_reader.fieldnames or []
        missing_headers = [h for h in required_headers if h.lower() not in [x.lower() for x in headers]]

        if missing_headers:
            flash(f'Missing required columns: {", ".join(missing_headers)}. Required: category, name, price', 'error')
            return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))

        # Normalize headers (case-insensitive)
        header_map = {h.lower(): h for h in headers}

        items_imported = 0
        categories_created = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Get values (case-insensitive column matching)
                category_name = row.get(header_map.get('category', 'category'), '').strip()
                item_name = row.get(header_map.get('name', 'name'), '').strip()
                description = row.get(header_map.get('description', 'description'), '').strip() if 'description' in header_map else ''
                price_str = row.get(header_map.get('price', 'price'), '0').strip()
                is_available_str = row.get(header_map.get('is_available', 'is_available'), 'true').strip().lower() if 'is_available' in header_map else 'true'
                image_url = row.get(header_map.get('image_url', 'image_url'), '').strip() if 'image_url' in header_map else ''

                # Skip empty rows
                if not category_name or not item_name:
                    continue

                # Parse price
                try:
                    price = float(price_str.replace('$', '').replace(',', ''))
                except ValueError:
                    errors.append(f'Row {row_num}: Invalid price "{price_str}"')
                    continue

                # Parse is_available
                is_available = is_available_str in ['true', 'yes', '1', 'available', 'y']

                # Get or create category
                category = Category.query.filter_by(
                    restaurant_id=restaurant.id,
                    name=category_name
                ).first()

                if not category:
                    category = Category(
                        name=category_name,
                        restaurant_id=restaurant.id,
                        is_active=True,
                        sort_order=0
                    )
                    db.session.add(category)
                    db.session.flush()  # Get the ID
                    categories_created += 1

                # Check if item already exists in this category
                existing_item = MenuItem.query.filter_by(
                    category_id=category.id,
                    name=item_name
                ).first()

                if existing_item:
                    # Update existing item
                    existing_item.description = description
                    existing_item.price = price
                    existing_item.is_available = is_available
                    if image_url:
                        existing_item.image_url = image_url
                else:
                    # Create new item
                    item = MenuItem(
                        name=item_name,
                        description=description,
                        price=price,
                        is_available=is_available,
                        image_url=image_url if image_url else None,
                        category_id=category.id
                    )
                    db.session.add(item)

                items_imported += 1

            except Exception as e:
                errors.append(f'Row {row_num}: {str(e)}')

        db.session.commit()

        # Build success message
        msg = f'Successfully imported {items_imported} menu items'
        if categories_created > 0:
            msg += f' and created {categories_created} new categories'

        if errors:
            msg += f'. {len(errors)} errors occurred.'
            for error in errors[:5]:  # Show first 5 errors
                flash(error, 'warning')
            if len(errors) > 5:
                flash(f'... and {len(errors) - 5} more errors', 'warning')

        flash(msg, 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error processing CSV file: {str(e)}', 'error')

    return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))


@admin_bp.route('/restaurants/<int:restaurant_id>/export-menu')
@admin_required
def export_menu_csv(restaurant_id):
    """Export menu items to CSV file"""
    import csv
    import io
    from flask import Response

    restaurant = Restaurant.query.get_or_404(restaurant_id)
    categories = Category.query.filter_by(restaurant_id=restaurant_id).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['category', 'name', 'description', 'price', 'is_available', 'image_url'])

    # Write data
    for category in categories:
        for item in category.items:
            writer.writerow([
                category.name,
                item.name,
                item.description or '',
                f'{item.price:.2f}',
                'true' if item.is_available else 'false',
                item.image_url or ''
            ])

    # Prepare response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={restaurant.name.replace(" ", "_")}_menu.csv'
        }
    )


@admin_bp.route('/restaurants/<int:restaurant_id>/download-template')
@admin_required
def download_menu_template(restaurant_id):
    """Download a sample CSV template for menu import"""
    import csv
    import io
    from flask import Response

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header and sample data
    writer.writerow(['category', 'name', 'description', 'price', 'is_available', 'image_url'])
    writer.writerow(['Appetizers', 'Spring Rolls', 'Crispy vegetable spring rolls', '8.99', 'true', ''])
    writer.writerow(['Appetizers', 'Chicken Wings', 'Spicy buffalo wings', '12.99', 'true', ''])
    writer.writerow(['Main Course', 'Grilled Salmon', 'Fresh Atlantic salmon with herbs', '24.99', 'true', ''])
    writer.writerow(['Main Course', 'Beef Steak', 'Premium ribeye steak', '32.99', 'true', ''])
    writer.writerow(['Desserts', 'Chocolate Cake', 'Rich chocolate layer cake', '7.99', 'true', ''])
    writer.writerow(['Beverages', 'Fresh Juice', 'Orange or Apple juice', '4.99', 'true', ''])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=menu_import_template.csv'
        }
    )


@admin_bp.route('/users')
@permission_required('user_management')
def users():
    """Display restaurant owners only"""
    # Only show restaurant owners, not system users (superadmin/admin/moderator)
    users = User.query.filter_by(role='restaurant_owner').order_by(User.created_at.desc()).all()

    # Stats for restaurant owners only
    stats = {
        'total': User.query.filter_by(role='restaurant_owner').count(),
        'active': User.query.filter_by(role='restaurant_owner', is_active=True).count(),
        'inactive': User.query.filter_by(role='restaurant_owner', is_active=False).count(),
        'with_restaurant': User.query.filter(User.role == 'restaurant_owner', User.restaurant != None).count(),
    }

    return render_template('admin/users.html', users=users, stats=stats)

@admin_bp.route('/users/create', methods=['POST'])
@superadmin_required
def create_admin_user():
    """Create a new admin/moderator user"""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')
    role = request.form.get('role')

    # Validation
    if not all([username, email, password, role]):
        flash('All fields are required', 'error')
        return redirect(url_for('admin.users'))

    if password != password_confirm:
        flash('Passwords do not match', 'error')
        return redirect(url_for('admin.users'))

    if len(password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('admin.users'))

    if role not in ['superadmin', 'admin', 'moderator']:
        flash('Invalid role', 'error')
        return redirect(url_for('admin.users'))

    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('admin.users'))

    if User.query.filter_by(email=email).first():
        flash('Email already exists', 'error')
        return redirect(url_for('admin.users'))

    user = User(
        username=username,
        email=email,
        role=role,
        is_active=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash(f'{role.title()} user "{username}" created successfully', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@permission_required('user_management')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    current_user = get_current_admin_user()

    # Cannot toggle own account
    if user.id == current_user.id:
        flash('Cannot disable your own account', 'error')
        return redirect(url_for('admin.users'))

    # Only superadmin can toggle other superadmins
    if user.role in ['superadmin', 'system_admin'] and current_user.role not in ['superadmin', 'system_admin']:
        flash('Only superadmin can manage other superadmins', 'error')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {"enabled" if user.is_active else "disabled"}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_owner_password(user_id):
    """Reset restaurant owner password (admin/superadmin only)"""
    user = User.query.get_or_404(user_id)

    # Only allow resetting restaurant owner passwords
    if user.role != 'restaurant_owner':
        flash('Can only reset restaurant owner passwords from this page', 'error')
        return redirect(url_for('admin.users'))

    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Validation
    if not new_password or not confirm_password:
        flash('Both password fields are required', 'error')
        return redirect(url_for('admin.users'))

    if new_password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('admin.users'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('admin.users'))

    # Reset password
    user.set_password(new_password)
    db.session.commit()

    flash(f'Password reset successfully for "{user.username}"', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@superadmin_required
def change_user_role(user_id):
    """Change a user's role (superadmin only)"""
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    current_user = get_current_admin_user()

    # Cannot change own role
    if user.id == current_user.id:
        flash('Cannot change your own role', 'error')
        return redirect(url_for('admin.users'))

    if new_role not in ['superadmin', 'admin', 'moderator', 'restaurant_owner']:
        flash('Invalid role', 'error')
        return redirect(url_for('admin.users'))

    old_role = user.role
    user.role = new_role
    db.session.commit()

    flash(f'User role changed from {old_role} to {new_role}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@superadmin_required
def delete_user(user_id):
    """Delete a user (superadmin only)"""
    user = User.query.get_or_404(user_id)
    current_user = get_current_admin_user()

    # Cannot delete own account
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('admin.users'))

    # Cannot delete if user has a restaurant
    if user.restaurant:
        flash('Cannot delete user who owns a restaurant. Delete the restaurant first.', 'error')
        return redirect(url_for('admin.users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'User "{username}" deleted', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@superadmin_required
def reset_user_password(user_id):
    """Reset a user's password (superadmin only)"""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')

    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('admin.users'))

    user.set_password(new_password)
    db.session.commit()

    flash(f'Password reset for user "{user.username}"', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/orders')
@permission_required('orders')
def orders():
    status = request.args.get('status')
    restaurant_id = request.args.get('restaurant_id', type=int)
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    if restaurant_id:
        query = query.filter_by(restaurant_id=restaurant_id)
    orders = query.order_by(Order.created_at.desc()).limit(100).all()
    restaurants = Restaurant.query.order_by(Restaurant.name).all()

    # Calculate statistics
    stats_query = Order.query
    if restaurant_id:
        stats_query = stats_query.filter_by(restaurant_id=restaurant_id)
    all_filtered_orders = stats_query.all()
    total_orders = len(all_filtered_orders)
    total_revenue = sum(o.total_price for o in all_filtered_orders)
    pending_orders = sum(1 for o in all_filtered_orders if o.status == 'pending')
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    stats = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'avg_order_value': avg_order_value
    }

    return render_template('admin/orders.html', orders=orders, current_status=status, restaurants=restaurants, current_restaurant=restaurant_id, stats=stats)

@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    valid_statuses = ['pending', 'preparing', 'served', 'completed', 'cancelled']
    if new_status in valid_statuses:
        order.status = new_status
        db.session.commit()
        flash(f'Order status updated to {new_status}', 'success')
    else:
        flash('Invalid status', 'error')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/orders/<int:order_id>/force-complete', methods=['POST'])
@admin_required
def force_complete_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'completed'
    db.session.commit()
    flash('Order force completed', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/settings')
@permission_required('settings')
def settings():
    total_restaurants = Restaurant.query.count()
    total_users = User.query.count()
    total_orders = Order.query.count()
    current_user = get_current_admin_user()

    # Get system users (superadmin, admin, moderators)
    system_users = User.query.filter(User.role.in_(['superadmin', 'system_admin', 'admin', 'moderator'])).order_by(User.created_at.desc()).all()

    # System user stats
    system_stats = {
        'total': len(system_users),
        'superadmins': User.query.filter(User.role.in_(['superadmin', 'system_admin'])).count(),
        'admins': User.query.filter_by(role='admin').count(),
        'moderators': User.query.filter_by(role='moderator').count(),
    }

    return render_template('admin/settings.html',
        total_restaurants=total_restaurants,
        total_users=total_users,
        total_orders=total_orders,
        current_user=current_user,
        system_users=system_users,
        system_stats=system_stats
    )

@admin_bp.route('/settings/password', methods=['POST'])
@admin_required
def update_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    user = User.query.get(session.get('admin_user_id'))

    if not user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('admin.settings'))

    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('admin.settings'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('admin.settings'))

    user.set_password(new_password)
    db.session.commit()
    flash('Password updated successfully', 'success')
    return redirect(url_for('admin.settings'))


@admin_bp.route('/domain')
@permission_required('settings')
def domain_config():
    """Domain configuration page"""
    current_user = get_current_admin_user()
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')
    return render_template('admin/domain.html',
        current_user=current_user,
        base_url=base_url
    )


@admin_bp.route('/domain/update', methods=['POST'])
@superadmin_required
def update_domain():
    """Update the base URL configuration"""
    new_url = request.form.get('base_url', '').strip()
    if not new_url:
        flash('Base URL is required', 'error')
        return redirect(url_for('admin.domain_config'))

    # Remove trailing slash
    if new_url.endswith('/'):
        new_url = new_url[:-1]

    # Update config (in production, this should update environment or config file)
    current_app.config['BASE_URL'] = new_url

    flash(f'Base URL updated to {new_url}. For permanent change, update your environment variables.', 'success')
    return redirect(url_for('admin.domain_config'))


# ============= QR TEMPLATE SETTINGS =============

@admin_bp.route('/qr-settings')
@permission_required('settings')
def qr_settings():
    """QR Template Settings page"""
    from app.models import QRTemplateSettings

    current_user = get_current_admin_user()
    settings = QRTemplateSettings.get_settings()

    return render_template('admin/qr_settings.html',
        current_user=current_user,
        settings=settings
    )


@admin_bp.route('/qr-settings/update', methods=['POST'])
@superadmin_required
def update_qr_settings():
    """Update QR Template Settings"""
    from app.models import QRTemplateSettings

    settings = QRTemplateSettings.get_settings()

    settings.saas_name = request.form.get('saas_name', 'RestaurantCMS')
    settings.primary_color = request.form.get('primary_color', '#6366f1')
    settings.secondary_color = request.form.get('secondary_color', '#1a1a2e')
    settings.scan_text = request.form.get('scan_text', 'Scan to View Menu')
    settings.powered_by_text = request.form.get('powered_by_text', 'Powered by')
    settings.show_powered_by = request.form.get('show_powered_by') == 'on'
    settings.template_style = request.form.get('template_style', 'modern')

    try:
        settings.qr_size = int(request.form.get('qr_size', 200))
    except (ValueError, TypeError):
        settings.qr_size = 200

    # Handle logo upload
    if 'saas_logo' in request.files:
        file = request.files['saas_logo']
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename

            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                logo_filename = f"saas_logo.{ext}"
                logo_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 'logos')
                os.makedirs(logo_folder, exist_ok=True)
                file.save(os.path.join(logo_folder, logo_filename))
                settings.saas_logo_path = logo_filename

    db.session.commit()
    flash('QR Template Settings updated successfully!', 'success')
    return redirect(url_for('admin.qr_settings'))


@admin_bp.route('/api-keys')
@permission_required('api_keys')
def api_keys():
    keys = ApiKey.query.order_by(ApiKey.created_at.desc()).all()
    restaurants = Restaurant.query.order_by(Restaurant.name).all()
    return render_template('admin/api_keys.html', keys=keys, restaurants=restaurants)

@admin_bp.route('/api-keys/create', methods=['POST'])
@permission_required('api_keys')
def create_api_key():
    name = request.form.get('name')
    restaurant_id = request.form.get('restaurant_id')
    if not name or not restaurant_id:
        flash('Name and restaurant are required', 'error')
        return redirect(url_for('admin.api_keys'))
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        flash('Restaurant not found', 'error')
        return redirect(url_for('admin.api_keys'))
    key = ApiKey(name=name, restaurant_id=restaurant.id)
    db.session.add(key)
    db.session.commit()
    flash('API key created', 'success')
    return redirect(url_for('admin.api_keys'))

@admin_bp.route('/api-keys/<int:key_id>/toggle', methods=['POST'])
@permission_required('api_keys')
def toggle_api_key(key_id):
    key = ApiKey.query.get_or_404(key_id)
    key.is_active = not key.is_active
    db.session.commit()
    flash('API key updated', 'success')
    return redirect(url_for('admin.api_keys'))


# ==================== REGISTRATION MANAGEMENT ====================

@admin_bp.route('/registrations')
@permission_required('registrations')
def registrations():
    """Main registration queue dashboard"""
    status_filter = request.args.get('status', 'pending')
    priority_filter = request.args.get('priority')

    query = RegistrationRequest.query

    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)

    # Order by priority (urgent first) then by created date
    priority_order = db.case(
        (RegistrationRequest.priority == 'urgent', 1),
        (RegistrationRequest.priority == 'high', 2),
        (RegistrationRequest.priority == 'normal', 3),
        (RegistrationRequest.priority == 'low', 4),
        else_=5
    )
    requests = query.order_by(priority_order, RegistrationRequest.created_at.asc()).all()

    # Statistics
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)

    stats = {
        'total_pending': RegistrationRequest.query.filter_by(status='pending').count(),
        'total_under_review': RegistrationRequest.query.filter_by(status='under_review').count(),
        'total_approved': RegistrationRequest.query.filter_by(status='approved').count(),
        'total_rejected': RegistrationRequest.query.filter_by(status='rejected').count(),
        'today_new': RegistrationRequest.query.filter(db.func.date(RegistrationRequest.created_at) == today).count(),
        'today_processed': RegistrationRequest.query.filter(
            db.func.date(RegistrationRequest.reviewed_at) == today,
            RegistrationRequest.status.in_(['approved', 'rejected'])
        ).count(),
        'week_approved': RegistrationRequest.query.filter(
            RegistrationRequest.reviewed_at >= week_ago,
            RegistrationRequest.status == 'approved'
        ).count(),
        'week_rejected': RegistrationRequest.query.filter(
            RegistrationRequest.reviewed_at >= week_ago,
            RegistrationRequest.status == 'rejected'
        ).count(),
        'urgent_pending': RegistrationRequest.query.filter_by(status='pending', priority='urgent').count(),
        'high_pending': RegistrationRequest.query.filter_by(status='pending', priority='high').count(),
    }

    # Get moderators for assignment
    moderators = User.query.filter(User.role.in_(['system_admin', 'moderator'])).all()

    return render_template('admin/registrations.html',
        requests=requests,
        stats=stats,
        current_status=status_filter,
        current_priority=priority_filter,
        moderators=moderators
    )


@admin_bp.route('/registrations/<int:request_id>')
@admin_required
def registration_detail(request_id):
    """View detailed registration request"""
    from app.models.website_content_models import PricingPlan

    reg_request = RegistrationRequest.query.get_or_404(request_id)

    # Get active pricing plans for dropdown
    pricing_plans = PricingPlan.query.filter_by(is_active=True).order_by(PricingPlan.display_order).all()

    # Log view action
    moderator_id = session.get('admin_user_id')
    log = ModerationLog(
        request_id=reg_request.id,
        moderator_id=moderator_id,
        action='viewed',
        previous_status=reg_request.status,
        new_status=reg_request.status
    )
    db.session.add(log)
    db.session.commit()

    return render_template('admin/registration_detail.html',
                         request=reg_request,
                         pricing_plans=pricing_plans)


@admin_bp.route('/registrations/<int:request_id>/assign', methods=['POST'])
@admin_required
def assign_registration(request_id):
    """Assign a registration to a moderator"""
    reg_request = RegistrationRequest.query.get_or_404(request_id)
    moderator_id = request.form.get('moderator_id')

    if moderator_id:
        reg_request.moderator_id = int(moderator_id)
        if reg_request.status == 'pending':
            old_status = reg_request.status
            reg_request.status = 'under_review'

            log = ModerationLog(
                request_id=reg_request.id,
                moderator_id=session.get('admin_user_id'),
                action='assigned',
                previous_status=old_status,
                new_status='under_review',
                notes=f'Assigned to moderator ID {moderator_id}'
            )
            db.session.add(log)

        db.session.commit()
        flash('Registration assigned successfully', 'success')

    return redirect(url_for('admin.registration_detail', request_id=request_id))


@admin_bp.route('/registrations/<int:request_id>/approve', methods=['POST'])
@admin_required
def approve_registration(request_id):
    """Approve a registration request and create user/restaurant"""
    reg_request = RegistrationRequest.query.get_or_404(request_id)

    if reg_request.status in ['approved', 'rejected']:
        flash('This request has already been processed', 'error')
        return redirect(url_for('admin.registration_detail', request_id=request_id))

    # Check if email already exists
    if User.query.filter_by(email=reg_request.applicant_email).first():
        flash('A user with this email already exists', 'error')
        return redirect(url_for('admin.registration_detail', request_id=request_id))

    # Generate username from email
    base_username = reg_request.applicant_email.split('@')[0]
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    # Generate random password
    temp_password = uuid.uuid4().hex[:10]

    current_admin_id = session.get('admin_user_id')

    # Create user
    new_user = User(
        username=username,
        email=reg_request.applicant_email,
        phone=reg_request.applicant_phone,
        role='restaurant_owner',
        created_by_id=current_admin_id
    )
    new_user.set_password(temp_password)
    db.session.add(new_user)
    db.session.flush()

    # Create restaurant
    new_restaurant = Restaurant(
        name=reg_request.restaurant_name,
        description=reg_request.restaurant_description,
        address=reg_request.restaurant_address,
        phone=reg_request.restaurant_phone,
        owner_id=new_user.id,
        is_active=True
    )
    db.session.add(new_restaurant)
    db.session.flush()

    # Update request
    old_status = reg_request.status
    reg_request.status = 'approved'
    reg_request.reviewed_at = datetime.utcnow()
    reg_request.moderator_id = session.get('admin_user_id')
    reg_request.approved_user_id = new_user.id
    reg_request.approved_restaurant_id = new_restaurant.id
    reg_request.moderator_notes = request.form.get('notes', '')

    # Log action
    log = ModerationLog(
        request_id=reg_request.id,
        moderator_id=session.get('admin_user_id'),
        action='approved',
        previous_status=old_status,
        new_status='approved',
        notes=f'Created user: {username}, restaurant: {new_restaurant.name}'
    )
    db.session.add(log)
    db.session.commit()

    flash(f'Registration approved! User created: {username} (temp password: {temp_password})', 'success')
    return redirect(url_for('admin.registrations'))


@admin_bp.route('/registrations/<int:request_id>/reject', methods=['POST'])
@admin_required
def reject_registration(request_id):
    """Reject a registration request"""
    reg_request = RegistrationRequest.query.get_or_404(request_id)

    if reg_request.status in ['approved', 'rejected']:
        flash('This request has already been processed', 'error')
        return redirect(url_for('admin.registration_detail', request_id=request_id))

    reason = request.form.get('reason', '')

    old_status = reg_request.status
    reg_request.status = 'rejected'
    reg_request.reviewed_at = datetime.utcnow()
    reg_request.moderator_id = session.get('admin_user_id')
    reg_request.rejection_reason = reason

    log = ModerationLog(
        request_id=reg_request.id,
        moderator_id=session.get('admin_user_id'),
        action='rejected',
        previous_status=old_status,
        new_status='rejected',
        notes=reason
    )
    db.session.add(log)
    db.session.commit()

    flash('Registration rejected', 'success')
    return redirect(url_for('admin.registrations'))


@admin_bp.route('/registrations/<int:request_id>/request-info', methods=['POST'])
@admin_required
def request_more_info(request_id):
    """Request more information from applicant"""
    reg_request = RegistrationRequest.query.get_or_404(request_id)

    message = request.form.get('message', '')

    old_status = reg_request.status
    reg_request.status = 'more_info_needed'
    reg_request.moderator_id = session.get('admin_user_id')
    reg_request.moderator_notes = message

    log = ModerationLog(
        request_id=reg_request.id,
        moderator_id=session.get('admin_user_id'),
        action='requested_info',
        previous_status=old_status,
        new_status='more_info_needed',
        notes=message
    )
    db.session.add(log)
    db.session.commit()

    flash('Information request sent', 'success')
    return redirect(url_for('admin.registrations'))


@admin_bp.route('/registrations/<int:request_id>/priority', methods=['POST'])
@admin_required
def update_priority(request_id):
    """Update registration priority"""
    reg_request = RegistrationRequest.query.get_or_404(request_id)
    new_priority = request.form.get('priority')

    if new_priority in ['low', 'normal', 'high', 'urgent']:
        reg_request.priority = new_priority
        db.session.commit()
        flash(f'Priority updated to {new_priority}', 'success')

    return redirect(url_for('admin.registration_detail', request_id=request_id))


@admin_bp.route('/registrations/<int:request_id>/add-note', methods=['POST'])
@admin_required
def add_registration_note(request_id):
    """Add a note to registration"""
    reg_request = RegistrationRequest.query.get_or_404(request_id)
    note = request.form.get('note', '')

    if note:
        log = ModerationLog(
            request_id=reg_request.id,
            moderator_id=session.get('admin_user_id'),
            action='note_added',
            previous_status=reg_request.status,
            new_status=reg_request.status,
            notes=note
        )
        db.session.add(log)
        db.session.commit()
        flash('Note added', 'success')

    return redirect(url_for('admin.registration_detail', request_id=request_id))


@admin_bp.route('/registrations/stats')
@admin_required
def registration_stats():
    """Detailed moderation statistics page"""
    # Time periods
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    month_ago = datetime.utcnow() - timedelta(days=30)

    # Overall stats
    overall = {
        'total': RegistrationRequest.query.count(),
        'pending': RegistrationRequest.query.filter_by(status='pending').count(),
        'under_review': RegistrationRequest.query.filter_by(status='under_review').count(),
        'approved': RegistrationRequest.query.filter_by(status='approved').count(),
        'rejected': RegistrationRequest.query.filter_by(status='rejected').count(),
        'more_info': RegistrationRequest.query.filter_by(status='more_info_needed').count(),
    }

    # Calculate approval rate
    processed = overall['approved'] + overall['rejected']
    overall['approval_rate'] = (overall['approved'] / processed * 100) if processed > 0 else 0

    # Per moderator stats
    moderator_stats = db.session.query(
        User.username,
        db.func.count(ModerationLog.id).label('total_actions'),
        db.func.sum(db.case((ModerationLog.action == 'approved', 1), else_=0)).label('approved'),
        db.func.sum(db.case((ModerationLog.action == 'rejected', 1), else_=0)).label('rejected')
    ).join(ModerationLog, User.id == ModerationLog.moderator_id)\
     .filter(ModerationLog.created_at >= week_ago)\
     .group_by(User.id).all()

    # Daily stats for the past week
    daily_stats = []
    for i in range(7):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())

        new_requests = RegistrationRequest.query.filter(
            RegistrationRequest.created_at.between(day_start, day_end)
        ).count()

        processed_requests = RegistrationRequest.query.filter(
            RegistrationRequest.reviewed_at.between(day_start, day_end),
            RegistrationRequest.status.in_(['approved', 'rejected'])
        ).count()

        daily_stats.append({
            'date': day.strftime('%Y-%m-%d'),
            'day_name': day.strftime('%A'),
            'new': new_requests,
            'processed': processed_requests
        })

    daily_stats.reverse()

    return render_template('admin/registration_stats.html',
        overall=overall,
        moderator_stats=moderator_stats,
        daily_stats=daily_stats
    )


# ============================================================================
# MEDIA & THEME MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route('/media-theme')
@admin_required
def media_theme():
    """Media and theme management page"""
    from app.models.website_media_models import WebsiteMedia, WebsiteTheme, WebsiteBanner

    try:
        theme = WebsiteTheme.query.filter_by(is_active=True).first()
    except Exception as e:
        # Table doesn't exist yet
        theme = None
        flash('Website theme feature is not yet configured. Database migration may be required.', 'warning')

    try:
        media_items = WebsiteMedia.query.order_by(WebsiteMedia.created_at.desc()).all()
    except:
        media_items = []

    try:
        banners = WebsiteBanner.query.order_by(WebsiteBanner.display_order).all()
    except:
        banners = []

    return render_template('admin/media_theme.html',
        theme=theme,
        media_items=media_items,
        banners=banners
    )


@admin_bp.route('/save-theme', methods=['POST'])
@admin_required
def save_theme():
    """Save theme settings"""
    from app.models.website_media_models import WebsiteTheme

    user = get_current_admin_user()

    try:
        theme = WebsiteTheme.query.filter_by(is_active=True).first()
    except Exception as e:
        flash('Website theme feature is not available. Database tables may need to be created.', 'error')
        return redirect(url_for('admin.dashboard'))

    if not theme:
        theme = WebsiteTheme(name='Default Theme', is_active=True, created_by_id=user.id)
        db.session.add(theme)

    theme.hero_bg_type = request.form.get('hero_bg_type', 'gradient')
    theme.hero_gradient_start = request.form.get('hero_gradient_start', '#6366f1')
    theme.hero_gradient_middle = request.form.get('hero_gradient_middle', '#8b5cf6')
    theme.hero_gradient_end = request.form.get('hero_gradient_end', '#ec4899')
    theme.hero_text_color = request.form.get('hero_text_color', '#ffffff')
    theme.primary_color = request.form.get('primary_color', '#6366f1')
    theme.secondary_color = request.form.get('secondary_color', '#ec4899')
    theme.accent_color = request.form.get('accent_color', '#06b6d4')
    theme.body_bg_color = request.form.get('body_bg_color', '#ffffff')
    theme.section_bg_light = request.form.get('section_bg_light', '#f8fafc')
    theme.section_bg_dark = request.form.get('section_bg_dark', '#1e1b4b')
    theme.text_primary = request.form.get('text_primary', '#334155')
    theme.text_secondary = request.form.get('text_secondary', '#64748b')
    theme.footer_bg_color = request.form.get('footer_bg_color', '#1e1b4b')
    theme.footer_text_color = request.form.get('footer_text_color', '#94a3b8')
    theme.logo_text = request.form.get('logo_text', 'RestaurantPro')

    db.session.commit()
    flash('Theme settings saved successfully!', 'success')
    return redirect(url_for('admin.media_theme'))


@admin_bp.route('/upload-media', methods=['POST'])
@admin_required
def upload_media():
    """Upload media file"""
    from app.models.website_media_models import WebsiteMedia

    if 'file' not in request.files or request.files['file'].filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin.media_theme'))

    file = request.files['file']
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'media')
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    user = get_current_admin_user()
    media = WebsiteMedia(
        name=request.form.get('name', file.filename),
        file_path=f"/static/uploads/media/{filename}",
        file_type='image',
        mime_type=file.content_type,
        file_size=os.path.getsize(filepath),
        alt_text=request.form.get('alt_text', ''),
        category=request.form.get('category', 'gallery'),
        uploaded_by_id=user.id
    )

    db.session.add(media)
    db.session.commit()
    flash('Media uploaded successfully!', 'success')
    return redirect(url_for('admin.media_theme'))


@admin_bp.route('/media/<int:id>/delete', methods=['POST'])
@admin_required
def delete_media(id):
    """Delete media file"""
    from app.models.website_media_models import WebsiteMedia

    media = WebsiteMedia.query.get_or_404(id)
    filepath = os.path.join(current_app.root_path, media.file_path.lstrip('/'))
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(media)
    db.session.commit()
    flash('Media deleted!', 'success')
    return redirect(url_for('admin.media_theme'))


@admin_bp.route('/create-banner', methods=['POST'])
@admin_required
def create_banner():
    """Create a new banner"""
    from app.models.website_media_models import WebsiteBanner

    user = get_current_admin_user()
    banner = WebsiteBanner(
        name=request.form.get('name'),
        section=request.form.get('section'),
        title=request.form.get('title'),
        subtitle=request.form.get('subtitle'),
        cta_text=request.form.get('cta_text'),
        cta_link=request.form.get('cta_link'),
        bg_type=request.form.get('bg_type', 'gradient'),
        bg_gradient_start=request.form.get('bg_gradient_start', '#6366f1'),
        bg_gradient_end=request.form.get('bg_gradient_end', '#ec4899'),
        text_color=request.form.get('text_color', '#ffffff'),
        is_active=True,
        created_by_id=user.id
    )

    db.session.add(banner)
    db.session.commit()
    flash('Banner created successfully!', 'success')
    return redirect(url_for('admin.media_theme'))


@admin_bp.route('/banners/<int:id>/delete', methods=['POST'])
@admin_required
def delete_banner(id):
    """Delete a banner"""
    from app.models.website_media_models import WebsiteBanner

    banner = WebsiteBanner.query.get_or_404(id)
    db.session.delete(banner)
    db.session.commit()
    flash('Banner deleted!', 'success')
    return redirect(url_for('admin.media_theme'))


@admin_bp.route('/api/theme')
def get_active_theme():
    """Get active theme settings (public API)"""
    from app.models.website_media_models import WebsiteTheme

    try:
        theme = WebsiteTheme.query.filter_by(is_active=True).first()
        if theme:
            return jsonify({'success': True, 'data': theme.to_dict()})
    except Exception as e:
        # Table doesn't exist, return default theme
        pass

    return jsonify({
        'success': True,
        'data': {
            'hero_bg_type': 'gradient',
            'hero_gradient_start': '#6366f1',
            'hero_gradient_middle': '#8b5cf6',
            'hero_gradient_end': '#ec4899',
            'primary_color': '#6366f1',
            'logo_text': 'RestaurantPro'
        }
    })


