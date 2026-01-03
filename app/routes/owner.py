"""
Restaurant Owner Routes - Completely separate from admin system
URL Pattern: /<restaurant_id>/* for each restaurant
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify, current_app
from functools import wraps
from app import db
from app.models import User, Restaurant, Order, Category, Table, MenuItem
from app.services.qr_service import generate_restaurant_qr_code
from datetime import datetime, timedelta

owner_bp = Blueprint('owner', __name__)


def get_current_owner():
    """Get the current logged in restaurant owner or admin viewing as owner"""
    # Check if admin is accessing with admin_access flag
    if request.args.get('admin_access') == 'true' and session.get('admin_logged_in'):
        admin_user = User.query.get(session.get('admin_user_id'))
        if admin_user and admin_user.role in ['admin', 'superadmin', 'system_admin']:
            # Get restaurant from URL parameter
            restaurant_id = request.args.get('restaurant_id') or request.view_args.get('restaurant_id')
            if restaurant_id:
                restaurant = Restaurant.query.get(restaurant_id)
                if restaurant and restaurant.owner:
                    # Return the restaurant owner for this session
                    return restaurant.owner

    # Check for admin viewing kitchen screen
    if request.args.get('admin_restaurant_id') and session.get('admin_logged_in'):
        admin_user = User.query.get(session.get('admin_user_id'))
        if admin_user and admin_user.role in ['admin', 'superadmin', 'system_admin']:
            restaurant_id = request.args.get('admin_restaurant_id')
            restaurant = Restaurant.query.get(restaurant_id)
            if restaurant and restaurant.owner:
                return restaurant.owner

    # Normal owner login check
    if session.get('owner_logged_in') and session.get('owner_user_id'):
        user = User.query.get(session.get('owner_user_id'))
        if user and user.role == 'restaurant_owner' and user.is_active:
            return user
    return None


def is_admin_accessing():
    """Check if current request is from admin accessing owner features"""
    return (request.args.get('admin_access') == 'true' or request.args.get('admin_restaurant_id')) and session.get('admin_logged_in')


def feature_required(feature_name):
    """Decorator to check if restaurant has access to a specific feature based on pricing plan"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_owner()

            if not user or not user.restaurant:
                flash('Please login to access your restaurant', 'info')
                return redirect(url_for('owner.login'))

            # Check if feature is enabled in pricing plan
            if not user.restaurant.has_feature(feature_name):
                # If admin is accessing, redirect back with message
                if is_admin_accessing():
                    flash(f'This feature ({feature_name.replace("_", " ").title()}) is not enabled in this restaurant\'s plan. Please upgrade their plan first.', 'warning')
                    return redirect(url_for('admin.restaurant_detail', restaurant_id=user.restaurant.id))

                # For owners, show upgrade page
                return render_template('owner/feature_locked.html',
                    user=user,
                    restaurant=user.restaurant,
                    feature_name=feature_name,
                    feature_display_name=feature_name.replace('_', ' ').title(),
                    current_plan=user.restaurant.pricing_plan
                )

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_owner():
    """Get the current logged in restaurant owner or admin viewing as owner"""
    # Check if admin is accessing with admin_access flag
    if request.args.get('admin_access') == 'true' and session.get('admin_logged_in'):
        admin_user = User.query.get(session.get('admin_user_id'))
        if admin_user and admin_user.role in ['admin', 'superadmin', 'system_admin']:
            # Get restaurant from URL parameter
            restaurant_id = request.args.get('restaurant_id') or request.view_args.get('restaurant_id')
            if restaurant_id:
                restaurant = Restaurant.query.get(restaurant_id)
                if restaurant and restaurant.owner:
                    # Return the restaurant owner for this session
                    return restaurant.owner

    # Check for admin viewing kitchen screen
    if request.args.get('admin_restaurant_id') and session.get('admin_logged_in'):
        admin_user = User.query.get(session.get('admin_user_id'))
        if admin_user and admin_user.role in ['admin', 'superadmin', 'system_admin']:
            restaurant_id = request.args.get('admin_restaurant_id')
            restaurant = Restaurant.query.get(restaurant_id)
            if restaurant and restaurant.owner:
                return restaurant.owner

    # Normal owner login check
    if session.get('owner_logged_in') and session.get('owner_user_id'):
        user = User.query.get(session.get('owner_user_id'))
        if user and user.role == 'restaurant_owner' and user.is_active:
            return user
    return None


def owner_required(f):
    """Decorator for owner-only routes - allows admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if this is an AJAX/API request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                  request.content_type == 'application/json' or \
                  request.accept_mimetypes.best == 'application/json' or \
                  '/api/' in request.path

        # Check for admin access
        is_admin_access = (request.args.get('admin_access') == 'true' or request.args.get('admin_restaurant_id')) and session.get('admin_logged_in')

        if not session.get('owner_logged_in') and not is_admin_access:
            if is_ajax:
                return jsonify({'success': False, 'message': 'Please login to access your restaurant'}), 401
            flash('Please login to access your restaurant', 'info')
            return redirect(url_for('owner.login'))

        user = get_current_owner()
        if not user:
            if not is_admin_access:
                session.pop('owner_logged_in', None)
                session.pop('owner_user_id', None)
            if is_ajax:
                return jsonify({'success': False, 'message': 'Session expired. Please login again'}), 401
            flash('Session expired. Please login again', 'info')
            return redirect(url_for('owner.login'))
        g.owner = user

        # Verify restaurant ID if provided in URL
        restaurant_id = kwargs.get('restaurant_id')
        if restaurant_id and user.restaurant:
            if str(user.restaurant.id) != str(restaurant_id):
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Access denied'}), 403
                flash('Access denied. You can only access your own restaurant.', 'error')
                return redirect(url_for('owner.dashboard', restaurant_id=user.restaurant.id))

        return f(*args, **kwargs)
    return decorated_function


@owner_bp.route('/owner/login', methods=['GET', 'POST'])
def login():
    """Restaurant owner login - completely separate from admin"""
    # If already logged in, redirect to dashboard
    if session.get('owner_logged_in'):
        user = get_current_owner()
        if user and user.restaurant:
            return redirect(url_for('owner.dashboard', restaurant_id=user.restaurant.id))
        elif user:
            return redirect(url_for('owner.no_restaurant'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('admin/owner_login_new.html')

        # Only allow restaurant_owner role
        user = User.query.filter_by(username=username, role='restaurant_owner').first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been disabled. Please contact administrator.', 'error')
                return render_template('admin/owner_login_new.html')

            # Clear any existing session and set owner session
            session.clear()
            session['owner_logged_in'] = True
            session['owner_user_id'] = user.id

            flash(f'Welcome back, {user.username}!', 'success')

            # Redirect to restaurant-specific dashboard
            if user.restaurant:
                return redirect(url_for('owner.dashboard', restaurant_id=user.restaurant.id))
            else:
                return redirect(url_for('owner.no_restaurant'))

        flash('Invalid username or password', 'error')

    return render_template('admin/owner_login_new.html')


@owner_bp.route('/owner/logout')
def logout():
    """Restaurant owner logout"""
    session.pop('owner_logged_in', None)
    session.pop('owner_user_id', None)
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('owner.login'))


@owner_bp.route('/owner/signup', methods=['POST'])
def signup():
    """Restaurant owner signup with package selection"""
    try:
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        restaurant_name = request.form.get('restaurant_name', '').strip()
        owner_name = request.form.get('owner_name', '').strip()
        pricing_plan_id = request.form.get('pricing_plan_id', '')

        # Validation
        if not all([username, email, password, restaurant_name, owner_name, pricing_plan_id]):
            flash('Please fill in all required fields and select a pricing plan', 'error')
            return redirect(url_for('owner.login'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('owner.login'))

        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another one.', 'error')
            return redirect(url_for('owner.login'))

        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use another email.', 'error')
            return redirect(url_for('owner.login'))

        # Create new user
        new_user = User(
            username=username,
            email=email,
            phone=phone,
            role='restaurant_owner',
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()  # To get the user ID

        # Create restaurant
        new_restaurant = Restaurant(
            name=restaurant_name,
            phone=phone,
            owner_id=new_user.id,
            is_active=True
        )
        db.session.add(new_restaurant)
        db.session.commit()

        # Auto-login the user
        session.clear()
        session['owner_logged_in'] = True
        session['owner_user_id'] = new_user.id

        flash(f'Welcome to RestaurantPro, {owner_name}! Your account has been created successfully.', 'success')

        # Redirect to restaurant dashboard
        if new_restaurant:
            return redirect(url_for('owner.dashboard', restaurant_id=new_restaurant.id))
        else:
            return redirect(url_for('owner.no_restaurant'))

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during registration: {str(e)}', 'error')
        return redirect(url_for('owner.login') + '?signup=1')


@owner_bp.route('/owner/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()

        if username and email:
            user = User.query.filter_by(username=username, email=email, role='restaurant_owner').first()
            # Always show same message for security
            flash('If your account exists, the administrator will contact you to reset your password.', 'info')
            return redirect(url_for('owner.login'))
        else:
            flash('Please enter both username and email', 'error')

    return render_template('owner/forgot_password.html')


@owner_bp.route('/owner/no-restaurant')
@owner_required
def no_restaurant():
    """Show message when owner has no restaurant assigned"""
    user = get_current_owner()
    return render_template('owner/no_restaurant.html', user=user)


@owner_bp.route('/<int:restaurant_id>/dashboard')
@owner_required
def dashboard(restaurant_id):
    """Restaurant owner dashboard - view only their own restaurant"""
    user = get_current_owner()

    # Check if user has a restaurant
    if not user.restaurant:
        return render_template('owner/no_restaurant.html', user=user)

    restaurant = user.restaurant

    # Get date filter parameters
    filter_type = request.args.get('filter', 'today')  # today, week, month, custom
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    today = datetime.utcnow().date()

    # Calculate date range based on filter
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif filter_type == 'month':
        start_date = today - timedelta(days=30)
        end_date = today
    elif filter_type == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today
            end_date = today
    else:
        start_date = today
        end_date = today

    # Get filtered orders
    filtered_orders = Order.query.filter(
        Order.restaurant_id == restaurant.id,
        db.func.date(Order.created_at) >= start_date,
        db.func.date(Order.created_at) <= end_date
    ).all()

    # Calculate statistics for the filtered period
    filtered_order_count = len(filtered_orders)
    filtered_revenue = sum(order.total_price for order in filtered_orders)
    filtered_completed = len([o for o in filtered_orders if o.status == 'completed'])
    filtered_pending = len([o for o in filtered_orders if o.status == 'pending'])
    filtered_preparing = len([o for o in filtered_orders if o.status == 'preparing'])
    filtered_cancelled = len([o for o in filtered_orders if o.status == 'cancelled'])

    # Calculate average order value
    avg_order_value = filtered_revenue / filtered_order_count if filtered_order_count > 0 else 0

    # Get top selling items for the period
    item_sales = {}
    for order in filtered_orders:
        for item in order.items:
            item_id = item.menu_item_id
            if item_id not in item_sales:
                item_sales[item_id] = {'name': item.menu_item.name if item.menu_item else 'Unknown', 'quantity': 0, 'revenue': 0}
            item_sales[item_id]['quantity'] += item.quantity
            item_sales[item_id]['revenue'] += item.subtotal

    top_items = sorted(item_sales.values(), key=lambda x: x['quantity'], reverse=True)[:5]

    # Get daily revenue data for chart (last 7 days or filtered period)
    chart_days = min((end_date - start_date).days + 1, 30)
    daily_data = []
    for i in range(chart_days):
        day = end_date - timedelta(days=chart_days - 1 - i)
        day_orders = [o for o in filtered_orders if o.created_at.date() == day]
        day_revenue = sum(o.total_price for o in day_orders)
        daily_data.append({
            'date': day.strftime('%b %d'),
            'revenue': round(day_revenue, 2),
            'orders': len(day_orders)
        })

    # Get overall restaurant statistics
    total_orders = Order.query.filter_by(restaurant_id=restaurant.id).count()
    pending_orders = Order.query.filter_by(restaurant_id=restaurant.id, status='pending').count()

    # Get categories and menu items
    categories = Category.query.filter_by(restaurant_id=restaurant.id).order_by(Category.sort_order).all()
    total_items = sum(len(cat.items) for cat in categories)

    # Get tables
    tables = Table.query.filter_by(restaurant_id=restaurant.id).all()

    # Get recent orders (last 10)
    recent_orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).limit(10).all()

    return render_template('owner/dashboard.html',
        user=user,
        restaurant=restaurant,
        # Filter info
        filter_type=filter_type,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        # Filtered statistics
        filtered_orders=filtered_order_count,
        filtered_revenue=filtered_revenue,
        filtered_completed=filtered_completed,
        filtered_pending=filtered_pending,
        filtered_preparing=filtered_preparing,
        filtered_cancelled=filtered_cancelled,
        avg_order_value=avg_order_value,
        # Chart data
        daily_data=daily_data,
        top_items=top_items,
        # Overall stats
        total_orders=total_orders,
        pending_orders=pending_orders,
        today_orders=len([o for o in filtered_orders if o.created_at.date() == today]),
        today_revenue=sum(o.total_price for o in filtered_orders if o.created_at.date() == today),
        categories=categories,
        total_items=total_items,
        tables=tables,
        recent_orders=recent_orders
    )


@owner_bp.route('/<int:restaurant_id>/generate-qr', methods=['POST'])
@owner_required
def generate_qr(restaurant_id):
    """Generate QR code for the restaurant"""
    user = get_current_owner()

    if not user.restaurant or user.restaurant.id != restaurant_id:
        flash('Access denied', 'error')
        return redirect(url_for('owner.login'))

    restaurant = user.restaurant
    try:
        qr_filename = generate_restaurant_qr_code(restaurant.public_id, restaurant.name)
        restaurant.qr_code_path = qr_filename
        db.session.commit()
        flash('QR code generated successfully!', 'success')
    except Exception as e:
        flash(f'Error generating QR code: {str(e)}', 'error')

    return redirect(url_for('owner.dashboard', restaurant_id=restaurant_id))


@owner_bp.route('/order/<order_number>/invoice')
@owner_required
def order_invoice(order_number):
    """Generate invoice for an order"""
    user = get_current_owner()

    if not user.restaurant:
        flash('Restaurant not found', 'error')
        return redirect(url_for('owner.orders'))

    order = Order.query.filter_by(
        order_number=order_number,
        restaurant_id=user.restaurant.id
    ).first()

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('owner.orders'))

    return render_template('owner/invoice.html',
        order=order,
        restaurant=user.restaurant,
        user=user
    )


@owner_bp.route('/upload-logo', methods=['POST'])
@owner_required
def upload_logo():
    """Upload restaurant logo"""
    user = get_current_owner()

    if not user.restaurant:
        flash('Restaurant not found', 'error')
        return redirect(url_for('owner.profile'))

    if 'logo' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('owner.profile'))

    file = request.files['logo']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('owner.profile'))

    if file:
        from werkzeug.utils import secure_filename
        import os

        # Allowed extensions
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        if not allowed_file(file.filename):
            flash('Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP', 'error')
            return redirect(url_for('owner.profile'))

        # Create upload directory if not exists
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'logos')
        os.makedirs(upload_dir, exist_ok=True)

        # Delete old logo if exists
        if user.restaurant.logo_path:
            old_logo = os.path.join(upload_dir, user.restaurant.logo_path)
            if os.path.exists(old_logo):
                os.remove(old_logo)

        # Save new logo
        filename = f"restaurant_{user.restaurant.id}_{secure_filename(file.filename)}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        # Update database
        user.restaurant.logo_path = filename
        db.session.commit()

        flash('Logo uploaded successfully!', 'success')

    return redirect(url_for('owner.profile'))


@owner_bp.route('/delete-logo', methods=['POST'])
@owner_required
def delete_logo():
    """Delete restaurant logo"""
    user = get_current_owner()

    if not user.restaurant:
        flash('Restaurant not found', 'error')
        return redirect(url_for('owner.profile'))

    if user.restaurant.logo_path:
        import os
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'logos')
        logo_path = os.path.join(upload_dir, user.restaurant.logo_path)

        if os.path.exists(logo_path):
            os.remove(logo_path)

        user.restaurant.logo_path = None
        db.session.commit()

        flash('Logo deleted successfully!', 'success')
    else:
        flash('No logo to delete', 'error')

    return redirect(url_for('owner.profile'))


@owner_bp.route('/orders')
@owner_required
def orders():
    """View orders for owner's restaurant"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    status_filter = request.args.get('status')
    query = Order.query.filter_by(restaurant_id=user.restaurant.id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    orders = query.order_by(Order.created_at.desc()).limit(50).all()

    # Stats
    all_orders = Order.query.filter_by(restaurant_id=user.restaurant.id).all()
    stats = {
        'total': len(all_orders),
        'pending': sum(1 for o in all_orders if o.status == 'pending'),
        'preparing': sum(1 for o in all_orders if o.status == 'preparing'),
        'completed': sum(1 for o in all_orders if o.status == 'completed'),
    }

    return render_template('owner/orders.html',
        user=user,
        restaurant=user.restaurant,
        orders=orders,
        stats=stats,
        current_status=status_filter
    )


@owner_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@owner_required
def update_order_status(order_id):
    """Update order status"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    # Verify order belongs to this restaurant
    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant.id).first()

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('owner.orders'))

    new_status = request.form.get('status')

    if new_status not in ['pending', 'preparing', 'ready', 'completed', 'cancelled']:
        flash('Invalid status', 'error')
        return redirect(url_for('owner.orders'))

    order.status = new_status
    db.session.commit()

    flash(f'Order #{order.order_number} updated to {new_status}', 'success')
    return redirect(url_for('owner.orders'))


@owner_bp.route('/menu')
@owner_required
def menu():
    """View and manage menu for owner's restaurant"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    categories = Category.query.filter_by(restaurant_id=user.restaurant.id).order_by(Category.sort_order).all()

    # Calculate total items and available items
    total_items = sum(len(cat.items) for cat in categories)
    available_items = sum(len([item for item in cat.items if item.is_available]) for cat in categories)

    return render_template('owner/menu.html',
        user=user,
        restaurant=user.restaurant,
        categories=categories,
        total_items=total_items,
        available_items=available_items
    )


@owner_bp.route('/menu/category/add', methods=['POST'])
@owner_required
def add_category():
    """Add new category"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    name = request.form.get('name')
    description = request.form.get('description', '')
    sort_order = request.form.get('sort_order', 0, type=int)

    if not name:
        flash('Category name is required', 'error')
        return redirect(url_for('owner.menu'))

    category = Category(
        name=name,
        description=description,
        restaurant_id=user.restaurant.id,
        sort_order=sort_order or Category.query.filter_by(restaurant_id=user.restaurant.id).count() + 1
    )

    db.session.add(category)
    db.session.commit()

    flash('Category added successfully', 'success')
    return redirect(url_for('owner.menu'))


@owner_bp.route('/menu/category/<int:category_id>/edit', methods=['POST'])
@owner_required
def edit_category(category_id):
    """Edit category"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    category = Category.query.filter_by(id=category_id, restaurant_id=user.restaurant.id).first()
    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('owner.menu'))

    category.name = request.form.get('name', category.name)
    category.description = request.form.get('description', category.description)
    category.sort_order = request.form.get('sort_order', category.sort_order, type=int)

    db.session.commit()
    flash('Category updated successfully', 'success')
    return redirect(url_for('owner.menu'))


@owner_bp.route('/menu/category/<int:category_id>/delete', methods=['POST'])
@owner_required
def delete_category(category_id):
    """Delete category and all its items"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    category = Category.query.filter_by(id=category_id, restaurant_id=user.restaurant.id).first()
    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('owner.menu'))

    # Delete all items in category first
    MenuItem.query.filter_by(category_id=category.id).delete()
    db.session.delete(category)
    db.session.commit()

    flash('Category deleted successfully', 'success')
    return redirect(url_for('owner.menu'))


@owner_bp.route('/menu/item/add', methods=['POST'])
@owner_required
def add_menu_item():
    """Add new menu item"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    name = request.form.get('name')
    description = request.form.get('description', '')
    price = request.form.get('price')
    category_id = request.form.get('category_id')

    if not all([name, price, category_id]):
        flash('Name, price, and category are required', 'error')
        return redirect(url_for('owner.menu'))

    # Verify category belongs to this restaurant
    category = Category.query.filter_by(id=category_id, restaurant_id=user.restaurant.id).first()
    if not category:
        flash('Invalid category', 'error')
        return redirect(url_for('owner.menu'))

    try:
        price_float = float(price)
    except ValueError:
        flash('Invalid price format', 'error')
        return redirect(url_for('owner.menu'))

    # Handle image upload
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            from werkzeug.utils import secure_filename
            import uuid
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
            upload_folder = 'app/static/uploads/menu_images'
            import os
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, unique_filename))
            image_url = f'/static/uploads/menu_images/{unique_filename}'

    menu_item = MenuItem(
        name=name,
        description=description,
        price=price_float,
        category_id=category_id,
        image_url=image_url,
        is_available=True
    )

    db.session.add(menu_item)
    db.session.commit()

    flash('Menu item added successfully', 'success')
    return redirect(url_for('owner.menu'))


@owner_bp.route('/menu/item/<int:item_id>/edit', methods=['POST'])
@owner_required
def edit_menu_item(item_id):
    """Edit menu item"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    # Verify item belongs to this restaurant
    item = MenuItem.query.join(Category).filter(
        MenuItem.id == item_id,
        Category.restaurant_id == user.restaurant.id
    ).first()

    if not item:
        flash('Menu item not found', 'error')
        return redirect(url_for('owner.menu'))

    name = request.form.get('name')
    description = request.form.get('description', '')
    price = request.form.get('price')
    category_id = request.form.get('category_id')

    if not all([name, price, category_id]):
        flash('Name, price, and category are required', 'error')
        return redirect(url_for('owner.menu'))

    # Verify new category belongs to this restaurant
    category = Category.query.filter_by(id=category_id, restaurant_id=user.restaurant.id).first()
    if not category:
        flash('Invalid category', 'error')
        return redirect(url_for('owner.menu'))

    try:
        price_float = float(price)
    except ValueError:
        flash('Invalid price format', 'error')
        return redirect(url_for('owner.menu'))

    item.name = name
    item.description = description
    item.price = price_float
    item.category_id = category_id

    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            from werkzeug.utils import secure_filename
            import uuid
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
            upload_folder = 'app/static/uploads/menu_images'
            import os
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, unique_filename))
            item.image_url = f'/static/uploads/menu_images/{unique_filename}'

    db.session.commit()

    flash('Menu item updated successfully', 'success')
    return redirect(url_for('owner.menu'))


@owner_bp.route('/menu/item/<int:item_id>/toggle', methods=['POST'])
@owner_required
def toggle_menu_item(item_id):
    """Toggle menu item availability"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    # Verify item belongs to this restaurant
    item = MenuItem.query.join(Category).filter(
        MenuItem.id == item_id,
        Category.restaurant_id == user.restaurant.id
    ).first()

    if not item:
        flash('Menu item not found', 'error')
        return redirect(url_for('owner.menu'))

    item.is_available = not item.is_available
    db.session.commit()

    status = 'available' if item.is_available else 'unavailable'
    flash(f'Menu item marked as {status}', 'success')
    return redirect(url_for('owner.menu'))


@owner_bp.route('/menu/item/<int:item_id>/delete', methods=['POST'])
@owner_required
def delete_menu_item(item_id):
    """Delete menu item"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    # Verify item belongs to this restaurant
    item = MenuItem.query.join(Category).filter(
        MenuItem.id == item_id,
        Category.restaurant_id == user.restaurant.id
    ).first()

    if not item:
        flash('Menu item not found', 'error')
        return redirect(url_for('owner.menu'))

    db.session.delete(item)
    db.session.commit()

    flash('Menu item deleted successfully', 'success')
    return redirect(url_for('owner.menu'))


@owner_bp.route('/menu/import-csv', methods=['POST'])
@owner_required
def import_menu_csv():
    """Import menu items from CSV file"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    if 'csv_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('owner.menu'))

    file = request.files['csv_file']

    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('owner.menu'))

    try:
        import csv
        import io

        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        added_count = 0
        error_count = 0

        for row in csv_reader:
            try:
                # Get or create category
                category_name = row.get('category', '').strip()
                if not category_name:
                    continue

                category = Category.query.filter_by(
                    name=category_name,
                    restaurant_id=user.restaurant.id
                ).first()

                if not category:
                    category = Category(
                        name=category_name,
                        restaurant_id=user.restaurant.id,
                        sort_order=Category.query.filter_by(restaurant_id=user.restaurant.id).count() + 1
                    )
                    db.session.add(category)
                    db.session.flush()

                # Create menu item
                name = row.get('name', '').strip()
                price = float(row.get('price', 0))
                description = row.get('description', '').strip()

                if not name or price <= 0:
                    continue

                menu_item = MenuItem(
                    name=name,
                    description=description,
                    price=price,
                    category_id=category.id,
                    is_available=True
                )

                db.session.add(menu_item)
                added_count += 1

            except Exception as e:
                error_count += 1
                continue

        db.session.commit()

        if added_count > 0:
            flash(f'Successfully imported {added_count} menu items', 'success')
        if error_count > 0:
            flash(f'{error_count} items had errors and were skipped', 'error')

    except Exception as e:
        flash(f'Error importing CSV: {str(e)}', 'error')

    return redirect(url_for('owner.menu'))


@owner_bp.route('/profile', methods=['GET', 'POST'])
@owner_required
def profile():
    """View and edit restaurant profile"""
    user = get_current_owner()
    from app.services.geo_service import get_all_countries_for_selector
    from app.models.website_content_models import PricingPlan

    if request.method == 'POST':
        if not user.restaurant:
            flash('No restaurant found', 'error')
            return redirect(url_for('owner.profile'))

        # Update restaurant info
        user.restaurant.name = request.form.get('name', user.restaurant.name)
        user.restaurant.description = request.form.get('description', user.restaurant.description)
        user.restaurant.address = request.form.get('address', user.restaurant.address)
        user.restaurant.city = request.form.get('city', user.restaurant.city)
        user.restaurant.postal_code = request.form.get('postal_code', user.restaurant.postal_code)
        user.restaurant.category = request.form.get('category', user.restaurant.category)
        user.restaurant.phone = request.form.get('phone', user.restaurant.phone)
        user.restaurant.email = request.form.get('email', user.restaurant.email)
        user.restaurant.website = request.form.get('website', user.restaurant.website)

        # Update country (also updates country_code for pricing tier)
        new_country = request.form.get('country', '')
        if new_country:
            user.restaurant.country = new_country
            # Update country_code based on country selection
            country_code = request.form.get('country_code', '')
            if country_code:
                user.restaurant.country_code = country_code

        db.session.commit()
        flash('Restaurant profile updated successfully!', 'success')
        return redirect(url_for('owner.profile'))

    # Get countries list for dropdown
    countries = get_all_countries_for_selector()

    # Restaurant categories
    categories = [
        'Fast Food', 'Fine Dining', 'Casual Dining', 'Cafe', 'Bakery',
        'Bar & Grill', 'Pizzeria', 'Seafood', 'Steakhouse', 'Asian',
        'Indian', 'Mexican', 'Italian', 'Japanese', 'Chinese',
        'Thai', 'Vietnamese', 'Mediterranean', 'Middle Eastern', 'American',
        'Vegetarian', 'Vegan', 'Food Truck', 'Buffet', 'Other'
    ]

    # Currency options
    currencies = [
        {'symbol': '$', 'name': 'US Dollar (USD)'},
        {'symbol': '€', 'name': 'Euro (EUR)'},
        {'symbol': '£', 'name': 'British Pound (GBP)'},
        {'symbol': '¥', 'name': 'Japanese Yen (JPY)'},
        {'symbol': '₹', 'name': 'Indian Rupee (INR)'},
        {'symbol': '৳', 'name': 'Bangladeshi Taka (BDT)'},
        {'symbol': 'A$', 'name': 'Australian Dollar (AUD)'},
        {'symbol': 'C$', 'name': 'Canadian Dollar (CAD)'},
        {'symbol': 'RM', 'name': 'Malaysian Ringgit (MYR)'},
        {'symbol': 'S$', 'name': 'Singapore Dollar (SGD)'},
        {'symbol': '₱', 'name': 'Philippine Peso (PHP)'},
        {'symbol': '฿', 'name': 'Thai Baht (THB)'},
        {'symbol': 'R', 'name': 'South African Rand (ZAR)'},
        {'symbol': 'AED', 'name': 'UAE Dirham (AED)'},
        {'symbol': 'SAR', 'name': 'Saudi Riyal (SAR)'},
    ]

    return render_template('owner/profile.html',
        user=user,
        restaurant=user.restaurant,
        countries=countries,
        categories=categories
    )


@owner_bp.route('/settings', methods=['GET', 'POST'])
@owner_required
def settings():
    """Restaurant settings - Tax, Invoice, etc."""
    user = get_current_owner()

    if not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))

    if request.method == 'POST':
        # Tax Settings
        user.restaurant.sst_enabled = request.form.get('sst_enabled') == 'on'
        user.restaurant.sst_registration_no = request.form.get('sst_registration_no', '')
        user.restaurant.sst_rate = float(request.form.get('sst_rate', 6.0) or 6.0)

        user.restaurant.service_tax_enabled = request.form.get('service_tax_enabled') == 'on'
        user.restaurant.service_tax_rate = float(request.form.get('service_tax_rate', 10.0) or 10.0)

        # Invoice Settings
        user.restaurant.invoice_footer_enabled = request.form.get('invoice_footer_enabled') == 'on'
        user.restaurant.invoice_footer_note = request.form.get('invoice_footer_note', '')
        user.restaurant.currency_symbol = request.form.get('currency_symbol', '$')

        # Operating Hours
        user.restaurant.opening_time = request.form.get('opening_time', '09:00')
        user.restaurant.closing_time = request.form.get('closing_time', '22:00')

        # Ordering Settings
        user.restaurant.min_order_amount = float(request.form.get('min_order_amount', 0.0) or 0.0)
        user.restaurant.enable_takeaway = request.form.get('enable_takeaway') == 'on'
        user.restaurant.enable_dine_in = request.form.get('enable_dine_in') == 'on'
        user.restaurant.auto_accept_orders = request.form.get('auto_accept_orders') == 'on'

        # Notification Settings
        user.restaurant.order_notification_email = request.form.get('order_notification_email', '')
        user.restaurant.order_notification_enabled = request.form.get('order_notification_enabled') == 'on'

        db.session.commit()
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('owner.settings'))

    return render_template('owner/settings.html',
        user=user,
        restaurant=user.restaurant
    )


# ============= PLAN MANAGEMENT =============

@owner_bp.route('/upgrade-plan')
@owner_required
def upgrade_plan():
    """View available plans and request upgrade/downgrade"""
    user = get_current_owner()
    
    if not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))
    
    # Get all active pricing plans
    from app.models.website_content_models import PricingPlan
    from app.services.geo_service import get_country_info

    plans = PricingPlan.query.filter_by(is_active=True).order_by(PricingPlan.price).all()
    current_plan = user.restaurant.pricing_plan
    
    # Determine user's country: prefer restaurant's country_code, then IP detection
    if user.restaurant.country_code:
        user_country = user.restaurant.country_code
        tier = PricingPlan.get_tier_for_country(user_country)
        country_name = PricingPlan.get_country_name(user_country)

        tier_info = {
            'tier1': {'name': 'Premium', 'discount': 0},
            'tier2': {'name': 'Standard', 'discount': 20},
            'tier3': {'name': 'Economy', 'discount': 40},
            'tier4': {'name': 'Budget', 'discount': 60}
        }

        country_info = {
            'country_code': user_country,
            'country_name': country_name,
            'tier': tier,
            'tier_name': tier_info.get(tier, {}).get('name', 'Premium'),
            'discount_percent': tier_info.get(tier, {}).get('discount', 0)
        }
    else:
        # Fall back to IP-based detection
        country_info = get_country_info()
        user_country = country_info['country_code']
        tier = country_info['tier']

    return render_template('owner/upgrade_plan.html',
        user=user,
        restaurant=user.restaurant,
        plans=plans,
        current_plan=current_plan,
        country_info=country_info,
        user_country=user_country,
        current_tier=tier
    )


@owner_bp.route('/change-plan/<int:plan_id>', methods=['POST'])
@owner_required
def change_plan(plan_id):
    """Request to change to a different plan"""
    user = get_current_owner()
    
    if not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))
    
    from app.models.website_content_models import PricingPlan
    new_plan = PricingPlan.query.get_or_404(plan_id)
    current_plan = user.restaurant.pricing_plan
    
    # If plan has a price > 0, redirect to checkout
    if float(new_plan.price) > 0:
        return redirect(url_for('owner.checkout', plan_id=plan_id))

    # Free plan - process immediately
    user.restaurant.pricing_plan_id = new_plan.id
    
    from datetime import datetime, timedelta
    user.restaurant.subscription_start_date = datetime.utcnow()
    user.restaurant.subscription_end_date = datetime.utcnow() + timedelta(days=30 if new_plan.price_period == 'monthly' else 365)
    user.restaurant.is_trial = False
    
    db.session.commit()
    
    if current_plan:
        if float(new_plan.price) > float(current_plan.price):
            flash(f'Successfully upgraded to {new_plan.name} plan!', 'success')
        elif float(new_plan.price) < float(current_plan.price):
            flash(f'Successfully downgraded to {new_plan.name} plan. Some features may no longer be available.', 'info')
        else:
            flash(f'Successfully changed to {new_plan.name} plan!', 'success')
    else:
        flash(f'Successfully subscribed to {new_plan.name} plan!', 'success')
    
    return redirect(url_for('owner.settings'))


@owner_bp.route('/checkout/<int:plan_id>')
@owner_required
def checkout(plan_id):
    """Checkout page for paid plans"""
    user = get_current_owner()

    if not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))

    from app.models.website_content_models import PricingPlan, PaymentGateway
    from app.services.geo_service import get_country_info

    plan = PricingPlan.query.get_or_404(plan_id)
    country_info = get_country_info()

    # Get the price for user's country
    user_country = user.restaurant.country if hasattr(user.restaurant, 'country') and user.restaurant.country else country_info['country_code']
    plan_price = plan.get_price_for_country(user_country)

    # Get active payment gateways
    gateways = PaymentGateway.query.filter_by(is_active=True).order_by(PaymentGateway.display_order).all()

    return render_template('owner/checkout.html',
                         user=user,
                         restaurant=user.restaurant,
                         plan=plan,
                         plan_price=plan_price,
                         country_info=country_info,
                         user_country=user_country,
                         gateways=gateways)


@owner_bp.route('/process-payment/<int:plan_id>', methods=['POST'])
@owner_required
def process_payment(plan_id):
    """Process payment for plan upgrade"""
    user = get_current_owner()

    if not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))

    from app.models.website_content_models import PricingPlan, PaymentGateway, PaymentTransaction
    from app.services.geo_service import get_country_info
    from datetime import datetime, timedelta
    import uuid
    import json

    plan = PricingPlan.query.get_or_404(plan_id)
    gateway_name = request.form.get('gateway')

    # Get country-based price
    country_info = get_country_info()
    user_country = user.restaurant.country if hasattr(user.restaurant, 'country') and user.restaurant.country else country_info['country_code']
    plan_price = plan.get_price_for_country(user_country)

    gateway = PaymentGateway.query.filter_by(name=gateway_name, is_active=True).first()
    if not gateway:
        flash('Payment gateway not available', 'error')
        return redirect(url_for('owner.checkout', plan_id=plan_id))

    # Create transaction record with tier-based price
    transaction = PaymentTransaction(
        transaction_id=str(uuid.uuid4()),
        gateway_name=gateway_name,
        user_id=user.id,
        restaurant_id=user.restaurant.id,
        amount=plan_price,
        currency=plan.currency,
        status='pending',
        pricing_plan_id=plan.id,
        subscription_months=1 if plan.price_period == 'monthly' else 12
    )
    db.session.add(transaction)
    db.session.commit()

    # Check if this is first purchase (restaurant profile incomplete)
    is_first_purchase = not user.restaurant.country or not user.restaurant.address

    # For demo/sandbox mode, simulate successful payment
    if gateway.is_sandbox:
        # Simulate successful payment
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        transaction.gateway_response = json.dumps({'sandbox': True, 'message': 'Simulated payment'})

        # Update restaurant plan
        user.restaurant.pricing_plan_id = plan.id
        user.restaurant.subscription_start_date = datetime.utcnow()
        user.restaurant.subscription_end_date = datetime.utcnow() + timedelta(days=30 if plan.price_period == 'monthly' else 365)
        user.restaurant.is_trial = False

        db.session.commit()

        flash(f'Payment successful! You are now on the {plan.name} plan.', 'success')

        # Redirect to profile page for first-time users to complete details
        if is_first_purchase:
            flash('Please complete your restaurant profile to get started.', 'info')
            return redirect(url_for('owner.profile'))
        return redirect(url_for('owner.settings'))

    # For live mode, redirect to actual payment gateway
    credentials = gateway.get_active_credentials()

    if gateway_name == 'stripe':
        # Stripe checkout session would be created here
        # For now, simulate success
        flash('Stripe integration coming soon. Payment simulated.', 'info')
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        user.restaurant.pricing_plan_id = plan.id
        user.restaurant.subscription_start_date = datetime.utcnow()
        user.restaurant.subscription_end_date = datetime.utcnow() + timedelta(days=30 if plan.price_period == 'monthly' else 365)
        db.session.commit()
        if is_first_purchase:
            flash('Please complete your restaurant profile to get started.', 'info')
            return redirect(url_for('owner.profile'))
        return redirect(url_for('owner.settings'))

    elif gateway_name == 'paypal':
        # PayPal order would be created here
        flash('PayPal integration coming soon. Payment simulated.', 'info')
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        user.restaurant.pricing_plan_id = plan.id
        user.restaurant.subscription_start_date = datetime.utcnow()
        user.restaurant.subscription_end_date = datetime.utcnow() + timedelta(days=30 if plan.price_period == 'monthly' else 365)
        db.session.commit()
        if is_first_purchase:
            flash('Please complete your restaurant profile to get started.', 'info')
            return redirect(url_for('owner.profile'))
        return redirect(url_for('owner.settings'))

    flash('Unknown payment gateway', 'error')
    return redirect(url_for('owner.checkout', plan_id=plan_id))


# ============= TABLE MANAGEMENT =============

@owner_bp.route('/tables')
@owner_required
def tables():
    """Table management page"""
    user = get_current_owner()
    if not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=1))

    tables = Table.query.filter_by(restaurant_id=user.restaurant.id).order_by(Table.table_number).all()
    return render_template('owner/tables.html', user=user, restaurant=user.restaurant, tables=tables)


@owner_bp.route('/tables/add', methods=['POST'])
@owner_required
def add_table():
    """Add a new table"""
    from app.services.qr_service import generate_printable_table_qr

    user = get_current_owner()
    if not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.tables'))

    table_number = request.form.get('table_number')
    table_name = request.form.get('table_name', '').strip() or None
    capacity = request.form.get('capacity', 4)

    try:
        table_number = int(table_number)
        capacity = int(capacity)
    except (ValueError, TypeError):
        flash('Invalid table number or capacity', 'error')
        return redirect(url_for('owner.tables'))

    # Check if table number already exists
    existing = Table.query.filter_by(restaurant_id=user.restaurant.id, table_number=table_number).first()
    if existing:
        flash(f'Table {table_number} already exists', 'error')
        return redirect(url_for('owner.tables'))

    # Create table
    table = Table(
        table_number=table_number,
        table_name=table_name,
        capacity=capacity,
        restaurant_id=user.restaurant.id
    )
    db.session.add(table)
    db.session.flush()  # Get the table ID

    # Generate QR code
    try:
        qr_filename = generate_printable_table_qr(user.restaurant, table)
        table.qr_code_path = qr_filename
    except Exception as e:
        current_app.logger.error(f'QR generation error: {e}')

    db.session.commit()
    flash(f'Table {table_number} added successfully!', 'success')
    return redirect(url_for('owner.tables'))


@owner_bp.route('/tables/<int:table_id>/edit', methods=['POST'])
@owner_required
def edit_table(table_id):
    """Edit a table"""
    user = get_current_owner()
    table = Table.query.filter_by(id=table_id, restaurant_id=user.restaurant.id).first()

    if not table:
        flash('Table not found', 'error')
        return redirect(url_for('owner.tables'))

    table_name = request.form.get('table_name', '').strip() or None
    capacity = request.form.get('capacity', 4)
    is_active = request.form.get('is_active') == 'on'

    try:
        table.capacity = int(capacity)
    except (ValueError, TypeError):
        table.capacity = 4

    table.table_name = table_name
    table.is_active = is_active
    db.session.commit()

    flash(f'Table {table.table_number} updated!', 'success')
    return redirect(url_for('owner.tables'))


@owner_bp.route('/tables/<int:table_id>/delete', methods=['POST'])
@owner_required
def delete_table(table_id):
    """Delete a table"""
    user = get_current_owner()
    table = Table.query.filter_by(id=table_id, restaurant_id=user.restaurant.id).first()

    if not table:
        flash('Table not found', 'error')
        return redirect(url_for('owner.tables'))

    # Delete QR code file
    if table.qr_code_path:
        import os
        qr_path = os.path.join(current_app.config['QR_CODE_FOLDER'], table.qr_code_path)
        if os.path.exists(qr_path):
            os.remove(qr_path)

    db.session.delete(table)
    db.session.commit()
    flash(f'Table {table.table_number} deleted!', 'success')
    return redirect(url_for('owner.tables'))


@owner_bp.route('/tables/<int:table_id>/regenerate-qr', methods=['POST'])
@owner_required
def regenerate_table_qr(table_id):
    """Regenerate QR code for a table"""
    from app.services.qr_service import generate_printable_table_qr

    user = get_current_owner()
    table = Table.query.filter_by(id=table_id, restaurant_id=user.restaurant.id).first()

    if not table:
        flash('Table not found', 'error')
        return redirect(url_for('owner.tables'))

    try:
        qr_filename = generate_printable_table_qr(user.restaurant, table)
        table.qr_code_path = qr_filename
        db.session.commit()
        flash(f'QR code regenerated for Table {table.table_number}!', 'success')
    except Exception as e:
        flash(f'Error generating QR: {str(e)}', 'error')

    return redirect(url_for('owner.tables'))


@owner_bp.route('/tables/regenerate-all', methods=['POST'])
@owner_required
def regenerate_all_qrs():
    """Regenerate QR codes for all tables"""
    from app.services.qr_service import generate_all_table_qrs

    user = get_current_owner()
    if not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.tables'))

    try:
        generated = generate_all_table_qrs(user.restaurant)
        db.session.commit()
        flash(f'Regenerated QR codes for {len(generated)} tables!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('owner.tables'))


@owner_bp.route('/tables/<int:table_id>/qr')
@owner_required
def download_table_qr(table_id):
    """Download printable QR code for a table"""
    from flask import send_file
    import os

    user = get_current_owner()
    table = Table.query.filter_by(id=table_id, restaurant_id=user.restaurant.id).first()

    if not table or not table.qr_code_path:
        flash('QR code not found', 'error')
        return redirect(url_for('owner.tables'))

    qr_path = os.path.join(current_app.config['QR_CODE_FOLDER'], table.qr_code_path)
    if os.path.exists(qr_path):
        return send_file(
            qr_path,
            as_attachment=True,
            download_name=f'{user.restaurant.name}_Table_{table.table_number}_QR.png'
        )

    flash('QR file not found', 'error')
    return redirect(url_for('owner.tables'))


@owner_bp.route('/tables/add-bulk', methods=['POST'])
@owner_required
def add_bulk_tables():
    """Add multiple tables at once"""
    from app.services.qr_service import generate_printable_table_qr

    user = get_current_owner()
    if not user.restaurant:
        flash('No restaurant found', 'error')
        return redirect(url_for('owner.tables'))

    count = request.form.get('count', 0)
    start_from = request.form.get('start_from', 1)
    capacity = request.form.get('capacity', 4)

    try:
        count = int(count)
        start_from = int(start_from)
        capacity = int(capacity)
    except (ValueError, TypeError):
        flash('Invalid input', 'error')
        return redirect(url_for('owner.tables'))

    if count < 1 or count > 100:
        flash('Count must be between 1 and 100', 'error')
        return redirect(url_for('owner.tables'))

    added = 0
    for i in range(count):
        table_num = start_from + i
        existing = Table.query.filter_by(restaurant_id=user.restaurant.id, table_number=table_num).first()
        if not existing:
            table = Table(
                table_number=table_num,
                capacity=capacity,
                restaurant_id=user.restaurant.id
            )
            db.session.add(table)
            db.session.flush()

            try:
                qr_filename = generate_printable_table_qr(user.restaurant, table)
                table.qr_code_path = qr_filename
            except:
                pass

            added += 1

    db.session.commit()
    flash(f'Added {added} tables!', 'success')
    return redirect(url_for('owner.tables'))


@owner_bp.route('/change-password', methods=['GET', 'POST'])
@owner_required
def change_password():
    """Change owner password"""
    user = get_current_owner()

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not user.check_password(current_password):
            flash('Current password is incorrect', 'error')
        elif len(new_password) < 6:
            flash('New password must be at least 6 characters', 'error')
        elif new_password != confirm_password:
            flash('New passwords do not match', 'error')
        else:
            user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully', 'success')
            return redirect(url_for('owner.profile'))

    return render_template('owner/change_password.html', user=user)


@owner_bp.route('/kitchen')
@owner_required
@feature_required('kitchen_display')
def kitchen_screen():
    """Kitchen dashboard for managing all orders"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    # Get all active orders (pending, preparing, ready) and recent completed
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()

    orders = Order.query.filter(
        Order.restaurant_id == user.restaurant.id,
        db.or_(
            Order.status.in_(['pending', 'preparing', 'ready']),
            db.and_(
                Order.status.in_(['completed', 'cancelled']),
                db.func.date(Order.created_at) == today
            )
        )
    ).order_by(Order.created_at.asc()).all()

    # Stats for kitchen dashboard
    stats = {
        'pending': Order.query.filter_by(restaurant_id=user.restaurant.id, status='pending').count(),
        'preparing': Order.query.filter_by(restaurant_id=user.restaurant.id, status='preparing').count(),
        'ready': Order.query.filter_by(restaurant_id=user.restaurant.id, status='ready').count(),
        'completed': Order.query.filter(
            Order.restaurant_id == user.restaurant.id,
            Order.status == 'completed',
            db.func.date(Order.created_at) == today
        ).count(),
        'cancelled': Order.query.filter(
            Order.restaurant_id == user.restaurant.id,
            Order.status == 'cancelled',
            db.func.date(Order.created_at) == today
        ).count(),
    }

    return render_template('owner/kitchen_screen.html',
        user=user,
        restaurant=user.restaurant,
        orders=orders,
        stats=stats
    )


@owner_bp.route('/api/kitchen/orders')
@owner_required
def api_kitchen_orders():
    """API endpoint for kitchen to fetch all orders with full details"""
    user = get_current_owner()

    if not user.restaurant:
        return jsonify({'success': False, 'message': 'No restaurant found'}), 400

    # Get all orders: active ones (pending, preparing, ready) and today's completed/cancelled
    from datetime import datetime
    today = datetime.utcnow().date()

    orders = Order.query.filter(
        Order.restaurant_id == user.restaurant.id,
        db.or_(
            Order.status.in_(['pending', 'preparing', 'ready']),
            db.and_(
                Order.status.in_(['completed', 'cancelled']),
                db.func.date(Order.created_at) == today
            )
        )
    ).order_by(Order.created_at.asc()).all()

    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'table_number': order.table_number,
            'status': order.status,
            'created_at': order.created_at.strftime('%H:%M'),
            'created_at_full': order.created_at.isoformat(),
            'items': [
                {
                    'name': item.menu_item.name if item.menu_item else 'Unknown',
                    'quantity': item.quantity,
                    'notes': item.notes
                }
                for item in order.items
            ]
        })

    stats = {
        'pending': sum(1 for o in orders if o.status == 'pending'),
        'preparing': sum(1 for o in orders if o.status == 'preparing'),
        'ready': sum(1 for o in orders if o.status == 'ready'),
        'completed': sum(1 for o in orders if o.status == 'completed'),
        'cancelled': sum(1 for o in orders if o.status == 'cancelled'),
    }

    return jsonify({'success': True, 'orders': orders_data, 'stats': stats})


@owner_bp.route('/api/kitchen/orders/<int:order_id>/status', methods=['POST'])
@owner_required
def api_kitchen_update_status(order_id):
    """API endpoint to update order status from kitchen screen"""
    user = get_current_owner()

    if not user.restaurant:
        return jsonify({'success': False, 'message': 'No restaurant found'}), 400

    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant.id).first()

    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    data = request.get_json() if request.is_json else None
    new_status = data.get('status') if data else request.form.get('status')

    if new_status not in ['pending', 'preparing', 'ready', 'completed', 'cancelled']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    order.status = new_status
    db.session.commit()

    return jsonify({'success': True, 'message': f'Order updated to {new_status}', 'new_status': new_status})


@owner_bp.route('/kitchen/orders/<int:order_id>/status', methods=['POST'])
@owner_required
def kitchen_update_status(order_id):
    """Update order status from kitchen screen (form submission fallback)"""
    user = get_current_owner()

    if not user.restaurant:
        return {'success': False, 'message': 'No restaurant found'}, 400

    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant.id).first()

    if not order:
        return {'success': False, 'message': 'Order not found'}, 404

    new_status = request.form.get('status')

    if new_status not in ['pending', 'preparing', 'ready', 'completed', 'cancelled']:
        return {'success': False, 'message': 'Invalid status'}, 400

    order.status = new_status
    db.session.commit()

    # If this is a regular form submission
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        flash(f'Order #{order.order_number} updated to {new_status}', 'success')
        return redirect(url_for('owner.kitchen_screen'))

    return {'success': True, 'message': f'Order updated to {new_status}'}


@owner_bp.route('/customer-display')
@owner_required
def customer_display():
    """Customer display screen showing order statuses - accessible from dashboard"""
    user = get_current_owner()

    if not user.restaurant:
        return redirect(url_for('owner.dashboard'))

    return render_template('owner/customer_display_launcher.html',
        user=user,
        restaurant=user.restaurant
    )


@owner_bp.route('/<int:restaurant_id>/customer-screen')
def customer_screen(restaurant_id):
    """Public customer display screen showing order statuses"""
    restaurant = Restaurant.query.get_or_404(restaurant_id)

    if not restaurant.is_active:
        return "Restaurant not available", 404

    # Check if customer display feature is enabled
    if not restaurant.has_feature('customer_display'):
        # Check if admin is accessing
        if session.get('admin_logged_in'):
            flash('Customer Display feature is not enabled for this restaurant. Please upgrade their plan.', 'warning')
            return redirect(url_for('admin.restaurant_detail', restaurant_id=restaurant_id))
        return render_template('owner/feature_locked_public.html',
            restaurant=restaurant,
            feature_name='Customer Display',
            message='This feature is not available in the current plan.'
        )

    # Get orders in progress (pending, preparing, ready)
    orders = Order.query.filter(
        Order.restaurant_id == restaurant.id,
        Order.status.in_(['pending', 'preparing', 'ready'])
    ).order_by(Order.created_at.asc()).all()

    # Group orders by status
    pending_orders = [o for o in orders if o.status == 'pending']
    preparing_orders = [o for o in orders if o.status == 'preparing']
    ready_orders = [o for o in orders if o.status == 'ready']

    return render_template('owner/customer_screen_v2.html',
        restaurant=restaurant,
        pending_orders=pending_orders,
        preparing_orders=preparing_orders,
        ready_orders=ready_orders
    )


@owner_bp.route('/api/<int:restaurant_id>/orders-status')
def api_orders_status(restaurant_id):
    """API endpoint for customer screen to fetch live order updates"""
    restaurant = Restaurant.query.get_or_404(restaurant_id)

    if not restaurant.is_active:
        return jsonify({'success': False, 'message': 'Restaurant not available'}), 404

    # Get orders in progress
    orders = Order.query.filter(
        Order.restaurant_id == restaurant.id,
        Order.status.in_(['pending', 'preparing', 'ready'])
    ).order_by(Order.created_at.asc()).all()

    return jsonify({
        'success': True,
        'orders': {
            'pending': [{'id': o.id, 'order_number': o.order_number, 'table_number': o.table_number} for o in orders if o.status == 'pending'],
            'preparing': [{'id': o.id, 'order_number': o.order_number, 'table_number': o.table_number} for o in orders if o.status == 'preparing'],
            'ready': [{'id': o.id, 'order_number': o.order_number, 'table_number': o.table_number} for o in orders if o.status == 'ready']
        }
    })


