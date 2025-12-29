from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, g, send_file
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
            session['admin_logged_in'] = True
            session['admin_user_id'] = user.id
            session['admin_role'] = user.role
            flash(f'Welcome, {user.username}!', 'success')
            return redirect(url_for('admin.restaurant_owner_view'))
        flash('Invalid username or password', 'error')
    return render_template('admin/owner_login.html')

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
    reg_request = RegistrationRequest.query.get_or_404(request_id)

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

    return render_template('admin/registration_detail.html', request=reg_request)


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

