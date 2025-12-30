"""
Restaurant Owner Routes - Completely separate from admin system
URL Pattern: /<restaurant_id>/* for each restaurant
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from functools import wraps
from app import db
from app.models import User, Restaurant, Order, Category, Table, MenuItem
from datetime import datetime

owner_bp = Blueprint('owner', __name__)


def get_current_owner():
    """Get the current logged in restaurant owner"""
    if session.get('owner_logged_in') and session.get('owner_user_id'):
        user = User.query.get(session.get('owner_user_id'))
        if user and user.role == 'restaurant_owner' and user.is_active:
            return user
    return None


def owner_required(f):
    """Decorator for owner-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('owner_logged_in'):
            flash('Please login to access your restaurant', 'info')
            return redirect(url_for('owner.login'))
        user = get_current_owner()
        if not user:
            session.pop('owner_logged_in', None)
            session.pop('owner_user_id', None)
            flash('Session expired. Please login again', 'info')
            return redirect(url_for('owner.login'))
        g.owner = user

        # Verify restaurant ID if provided in URL
        restaurant_id = kwargs.get('restaurant_id')
        if restaurant_id and user.restaurant:
            if str(user.restaurant.id) != str(restaurant_id):
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
            return render_template('owner/login.html')

        # Only allow restaurant_owner role
        user = User.query.filter_by(username=username, role='restaurant_owner').first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been disabled. Please contact administrator.', 'error')
                return render_template('owner/login.html')

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

    return render_template('owner/login.html')


@owner_bp.route('/owner/logout')
def logout():
    """Restaurant owner logout"""
    session.pop('owner_logged_in', None)
    session.pop('owner_user_id', None)
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('owner.login'))


@owner_bp.route('/owner/signup', methods=['POST'])
def signup():
    """Restaurant owner signup"""
    try:
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        restaurant_name = request.form.get('restaurant_name', '').strip()
        address = request.form.get('address', '').strip()
        description = request.form.get('description', '').strip()

        # Validation
        if not all([username, email, phone, password, restaurant_name]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('owner.login') + '?signup=1')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('owner.login') + '?signup=1')

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('owner.login') + '?signup=1')

        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another one.', 'error')
            return redirect(url_for('owner.login') + '?signup=1')

        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use another email.', 'error')
            return redirect(url_for('owner.login') + '?signup=1')

        # Create new user
        new_user = User(
            username=username,
            email=email,
            phone=phone,
            role='restaurant_owner',
            is_active=True  # Auto-activate for now, you can set to False for admin approval
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()  # To get the user ID

        # Create restaurant
        new_restaurant = Restaurant(
            name=restaurant_name,
            address=address,
            description=description,
            phone=phone,
            owner_id=new_user.id,
            is_active=True
        )
        db.session.add(new_restaurant)
        db.session.commit()

        flash('Account created successfully! You can now login.', 'success')
        return redirect(url_for('owner.login'))

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

    # Get restaurant statistics
    total_orders = Order.query.filter_by(restaurant_id=restaurant.id).count()
    pending_orders = Order.query.filter_by(restaurant_id=restaurant.id, status='pending').count()
    today = datetime.utcnow().date()
    today_orders = Order.query.filter(
        Order.restaurant_id == restaurant.id,
        db.func.date(Order.created_at) == today
    ).count()

    # Calculate today's revenue
    today_orders_list = Order.query.filter(
        Order.restaurant_id == restaurant.id,
        db.func.date(Order.created_at) == today
    ).all()
    today_revenue = sum(order.total_price for order in today_orders_list)

    # Get categories and menu items
    categories = Category.query.filter_by(restaurant_id=restaurant.id).order_by(Category.sort_order).all()
    total_items = sum(len(cat.items) for cat in categories)

    # Get tables
    tables = Table.query.filter_by(restaurant_id=restaurant.id).all()

    # Get recent orders
    recent_orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).limit(5).all()

    return render_template('owner/dashboard.html',
        user=user,
        restaurant=restaurant,
        total_orders=total_orders,
        pending_orders=pending_orders,
        today_orders=today_orders,
        today_revenue=today_revenue,
        categories=categories,
        total_items=total_items,
        tables=tables,
        recent_orders=recent_orders
    )


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

    if new_status not in ['pending', 'preparing', 'completed', 'cancelled']:
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

    return render_template('owner/menu_management.html',
        user=user,
        restaurant=user.restaurant,
        categories=categories
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

    if not name:
        flash('Category name is required', 'error')
        return redirect(url_for('owner.menu'))

    category = Category(
        name=name,
        description=description,
        restaurant_id=user.restaurant.id,
        sort_order=Category.query.filter_by(restaurant_id=user.restaurant.id).count() + 1
    )

    db.session.add(category)
    db.session.commit()

    flash('Category added successfully', 'success')
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


@owner_bp.route('/profile')
@owner_required
def profile():
    """View owner profile"""
    user = get_current_owner()

    return render_template('owner/profile.html',
        user=user,
        restaurant=user.restaurant
    )


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

