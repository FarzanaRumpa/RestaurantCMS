from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import uuid

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='restaurant_owner')
    is_active = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    restaurant = db.relationship('Restaurant', backref='owner', uselist=False, lazy=True, foreign_keys='Restaurant.owner_id')
    created_by = db.relationship('User', remote_side=[id], backref='created_users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.public_id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by.username if self.created_by else None
        }


class Restaurant(db.Model):
    __tablename__ = 'restaurants'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True, default=lambda: str(uuid.uuid4())[:8])
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))  # City
    country = db.Column(db.String(100))  # Country name
    postal_code = db.Column(db.String(20))  # Postal/ZIP code
    category = db.Column(db.String(100))  # Restaurant category (e.g., Fast Food, Fine Dining)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    qr_code_path = db.Column(db.String(255))  # Main restaurant QR code
    logo_path = db.Column(db.String(255))  # Restaurant logo image

    # Tax & Invoice Settings
    sst_enabled = db.Column(db.Boolean, default=False)
    sst_registration_no = db.Column(db.String(50))
    sst_rate = db.Column(db.Float, default=6.0)  # Default 6% SST
    service_tax_enabled = db.Column(db.Boolean, default=False)
    service_tax_rate = db.Column(db.Float, default=10.0)  # Default 10% service tax
    invoice_footer_enabled = db.Column(db.Boolean, default=True)
    invoice_footer_note = db.Column(db.Text, default='Thank you for dining with us!')

    # Currency
    currency_symbol = db.Column(db.String(10), default='$')

    # Operating Hours
    opening_time = db.Column(db.String(5), default='09:00')
    closing_time = db.Column(db.String(5), default='22:00')

    # Ordering Settings
    min_order_amount = db.Column(db.Float, default=0.0)
    enable_takeaway = db.Column(db.Boolean, default=True)
    enable_dine_in = db.Column(db.Boolean, default=True)
    auto_accept_orders = db.Column(db.Boolean, default=False)

    # Notification Settings
    order_notification_email = db.Column(db.String(120))
    order_notification_enabled = db.Column(db.Boolean, default=True)

    # Subscription / Pricing Plan
    pricing_plan_id = db.Column(db.Integer, db.ForeignKey('pricing_plans.id'))
    country_code = db.Column(db.String(5), default='US')  # For tier-based pricing
    subscription_start_date = db.Column(db.DateTime)
    subscription_end_date = db.Column(db.DateTime)
    is_trial = db.Column(db.Boolean, default=False)
    trial_ends_at = db.Column(db.DateTime)

    # Registration/Moderation Status
    # approved, pending_review, rejected
    registration_status = db.Column(db.String(20), default='approved')
    rejection_reason = db.Column(db.Text)  # Reason if rejected
    registration_request_id = db.Column(db.Integer, db.ForeignKey('registration_requests.id'))

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tables = db.relationship('Table', backref='restaurant', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='restaurant', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='restaurant', lazy=True, cascade='all, delete-orphan')

    # Add late import to avoid circular imports
    @property
    def pricing_plan(self):
        """Get the pricing plan for this restaurant"""
        if self.pricing_plan_id:
            from app.models.website_content_models import PricingPlan
            return PricingPlan.query.get(self.pricing_plan_id)
        return None

    def has_feature(self, feature_name):
        """Check if restaurant has access to a specific feature based on plan"""
        plan = self.pricing_plan
        if not plan:
            return False  # No plan = no features

        feature_map = {
            'kitchen_display': plan.has_kitchen_display,
            'customer_display': plan.has_customer_display,
            'owner_dashboard': plan.has_owner_dashboard,
            'advanced_analytics': plan.has_advanced_analytics,
            'qr_ordering': plan.has_qr_ordering,
            'table_management': plan.has_table_management,
            'order_history': plan.has_order_history,
            'customer_feedback': plan.has_customer_feedback,
            'inventory_management': plan.has_inventory_management,
            'staff_management': plan.has_staff_management,
            'multi_language': plan.has_multi_language,
            'custom_branding': plan.has_custom_branding,
            'email_notifications': plan.has_email_notifications,
            'sms_notifications': plan.has_sms_notifications,
            'api_access': plan.has_api_access,
            'priority_support': plan.has_priority_support,
            'white_label': plan.has_white_label,
            'reports_export': plan.has_reports_export,
            'pos_integration': plan.has_pos_integration,
            'payment_integration': plan.has_payment_integration
        }
        return feature_map.get(feature_name, False)

    def get_limit(self, limit_name):
        """Get a specific limit from the plan"""
        plan = self.pricing_plan
        if not plan:
            return None

        limit_map = {
            'max_tables': plan.max_tables,
            'max_menu_items': plan.max_menu_items,
            'max_categories': plan.max_categories,
            'max_orders_per_month': plan.max_orders_per_month,
            'max_restaurants': plan.max_restaurants,
            'max_staff_accounts': plan.max_staff_accounts
        }
        return limit_map.get(limit_name)

    def can_add_table(self):
        """Check if restaurant can add more tables"""
        max_tables = self.get_limit('max_tables')
        if max_tables is None:
            return True  # Unlimited
        return len(self.tables) < max_tables

    def can_add_menu_item(self):
        """Check if restaurant can add more menu items"""
        max_items = self.get_limit('max_menu_items')
        if max_items is None:
            return True  # Unlimited
        # Use the Category relationship to count menu items
        total_items = 0
        for category in self.categories:
            total_items += len(category.items)
        return total_items < max_items

    def to_dict(self):
        return {
            'id': self.public_id,
            'name': self.name,
            'description': self.description,
            'address': self.address,
            'phone': self.phone,
            'is_active': self.is_active,
            'table_count': len(self.tables),
            'qr_code_url': f'/static/qrcodes/{self.qr_code_path}' if self.qr_code_path else None,
            'created_at': self.created_at.isoformat()
        }


class Table(db.Model):
    __tablename__ = 'tables'

    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False)
    table_name = db.Column(db.String(50))  # Optional custom name like "Patio 1", "Window Seat"
    access_token = db.Column(db.String(50), unique=True, default=lambda: str(uuid.uuid4())[:12])
    qr_code_path = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    capacity = db.Column(db.Integer, default=4)  # Number of seats
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('restaurant_id', 'table_number', name='unique_table_per_restaurant'),)

    def to_dict(self):
        return {
            'id': self.id,
            'table_number': self.table_number,
            'table_name': self.table_name,
            'access_token': self.access_token,
            'qr_code_url': f'/static/qrcodes/{self.qr_code_path}' if self.qr_code_path else None,
            'is_active': self.is_active,
            'capacity': self.capacity
        }


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('MenuItem', backref='category', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'items': [item.to_dict() for item in self.items if item.is_available]
        }


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'is_available': self.is_available,
            'image_url': self.image_url,
            'category_id': self.category_id
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)

    # ==== DUAL ORDER NUMBER SYSTEM ====
    # 1. Internal Order ID - Globally unique, immutable, for system use
    #    Used for: database relations, billing, refunds, webhooks, audits
    internal_order_id = db.Column(db.String(50), unique=True, nullable=False,
                                   default=lambda: str(uuid.uuid4()))

    # 2. Display Order Number - 4-digit, restaurant-scoped, for human use
    #    Used for: kitchen screens, customer confirmation, staff communication
    #    Range: 1-9999 (formatted as 0001-9999)
    display_order_number = db.Column(db.Integer, nullable=True, index=True)

    # Legacy field - kept for backward compatibility during migration
    # TODO: Remove after full migration to dual system
    order_number = db.Column(db.String(20), unique=True)
    # =====================================

    table_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    total_price = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # POS-specific fields
    order_source = db.Column(db.String(20), default='qr')  # 'qr', 'pos', 'online'
    order_type = db.Column(db.String(20), default='dine_in')  # 'dine_in', 'takeaway', 'delivery'
    payment_status = db.Column(db.String(20), default='unpaid')  # 'unpaid', 'partial', 'paid'
    payment_method = db.Column(db.String(20))  # 'cash', 'card', 'split', 'online'
    cash_received = db.Column(db.Float, default=0.0)
    change_given = db.Column(db.Float, default=0.0)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    is_held = db.Column(db.Boolean, default=False)  # For held orders in POS
    discount_amount = db.Column(db.Float, default=0.0)
    discount_type = db.Column(db.String(20))  # 'percentage', 'fixed'
    tax_amount = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, default=0.0)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    # Index for efficient restaurant + display number lookups
    __table_args__ = (
        db.Index('ix_order_restaurant_display', 'restaurant_id', 'display_order_number'),
        db.Index('ix_order_restaurant_status', 'restaurant_id', 'status'),
    )

    def generate_order_number(self):
        """
        DEPRECATED: Use allocate_display_number() instead.

        This method is kept for backward compatibility during migration.
        It still sets the legacy order_number field.
        """
        # Generate sequential order number for the restaurant
        # Format: #XXXX (4-digit sequential number per restaurant)
        from sqlalchemy import func

        # Get the count of orders for this restaurant (including this one)
        order_count = db.session.query(func.count(Order.id)).filter_by(restaurant_id=self.restaurant_id).scalar() or 0

        # Generate 4-digit sequential number (resets after 9999)
        sequential_num = (order_count % 10000) + 1
        self.order_number = f"#{sequential_num:04d}"

        # Also set display_order_number for dual system compatibility
        self.display_order_number = sequential_num

    def allocate_display_number(self) -> bool:
        """
        Allocate a display order number using the new OrderNumberService.

        This method:
        1. Generates the internal_order_id if not already set
        2. Allocates a display number from the slot pool
        3. Sets both the new fields and legacy order_number for compatibility

        Returns:
            True if successful, False otherwise
        """
        from app.services.order_number_service import OrderNumberService

        # Ensure internal order ID is set
        if not self.internal_order_id:
            self.internal_order_id = OrderNumberService.generate_internal_order_id()

        # Allocate display number
        success, display_num, error = OrderNumberService.allocate_display_number(
            self.restaurant_id,
            self.id
        )

        if success and display_num:
            self.display_order_number = display_num
            # Set legacy field with restaurant-scoped format for global uniqueness
            # Format: R{restaurant_id}-{display_number:04d}
            # This ensures no collision across restaurants while keeping the display portion readable
            self.order_number = f"R{self.restaurant_id}-{display_num:04d}"
            return True

        return False

    def release_display_number(self, immediate: bool = False) -> bool:
        """
        Release this order's display number back to the pool.

        Should be called when order status changes to completed or cancelled.

        Args:
            immediate: If True, make the number immediately available

        Returns:
            True if successful, False otherwise
        """
        from app.services.order_number_service import OrderNumberService
        return OrderNumberService.release_display_number(self.id, immediate)

    @property
    def display_number_formatted(self) -> str:
        """Get the display order number in human-readable format (e.g., '0042')"""
        from app.services.order_number_service import OrderNumberService
        return OrderNumberService.format_display_number(self.display_order_number)

    @classmethod
    def find_by_display_number(cls, restaurant_id: int, display_number: int) -> 'Order':
        """
        Find the current active order with a given display number.

        Args:
            restaurant_id: The restaurant's database ID
            display_number: The 4-digit display number

        Returns:
            The Order object or None
        """
        from app.services.order_number_service import OrderNumberService
        return OrderNumberService.lookup_by_display_number(restaurant_id, display_number)

    @classmethod
    def find_by_internal_id(cls, internal_id: str) -> 'Order':
        """
        Find an order by its internal order ID (UUID).

        Args:
            internal_id: The UUID internal order ID

        Returns:
            The Order object or None
        """
        return cls.query.filter_by(internal_order_id=internal_id).first()

    def calculate_total(self):
        self.total_price = sum(item.subtotal for item in self.items)

    def to_dict(self):
        return {
            'id': self.id,
            # New dual order number system
            'internal_order_id': self.internal_order_id,
            'display_order_number': self.display_order_number,
            'display_order_number_formatted': self.display_number_formatted,
            # Legacy field (for backward compatibility)
            'order_number': self.order_number,
            'table_number': self.table_number,
            'status': self.status,
            'total_price': self.total_price,
            'notes': self.notes,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            # POS fields
            'order_source': self.order_source,
            'order_type': self.order_type,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'cash_received': self.cash_received,
            'change_given': self.change_given,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'is_held': self.is_held,
            'discount_amount': self.discount_amount,
            'discount_type': self.discount_type,
            'tax_amount': self.tax_amount,
            'subtotal': self.subtotal
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    menu_item = db.relationship('MenuItem')

    def to_dict(self):
        return {
            'id': self.id,
            'menu_item_id': self.menu_item_id,
            'menu_item_name': self.menu_item.name if self.menu_item else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal,
            'notes': self.notes
        }


class ApiKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    restaurant = db.relationship('Restaurant')

    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token,
            'name': self.name,
            'is_active': self.is_active,
            'restaurant_id': self.restaurant_id,
            'restaurant_name': self.restaurant.name if self.restaurant else None,
            'created_at': self.created_at.isoformat()
        }


class RegistrationRequest(db.Model):
    """Restaurant registration requests from mobile app users"""
    __tablename__ = 'registration_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(50), unique=True, default=lambda: f"REQ-{uuid.uuid4().hex[:8].upper()}")

    # Applicant Info
    applicant_name = db.Column(db.String(100), nullable=False)
    applicant_email = db.Column(db.String(120), nullable=False)
    applicant_phone = db.Column(db.String(20))

    # Restaurant Info
    restaurant_name = db.Column(db.String(100), nullable=False)
    restaurant_description = db.Column(db.Text)
    restaurant_address = db.Column(db.String(255))
    restaurant_phone = db.Column(db.String(20))
    restaurant_type = db.Column(db.String(50))  # e.g., cafe, restaurant, bar, fast-food

    # Documents/Verification
    business_license = db.Column(db.String(255))  # File path
    id_document = db.Column(db.String(255))  # File path
    additional_docs = db.Column(db.Text)  # JSON array of file paths

    # Status: pending, under_review, approved, rejected, more_info_needed
    status = db.Column(db.String(20), default='pending')
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent

    # Moderation
    moderator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    moderator_notes = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    # After approval, link to created user/restaurant
    approved_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=True)

    moderator = db.relationship('User', foreign_keys=[moderator_id], backref='moderated_requests')
    approved_user = db.relationship('User', foreign_keys=[approved_user_id])
    approved_restaurant = db.relationship('Restaurant', foreign_keys=[approved_restaurant_id])

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'applicant_name': self.applicant_name,
            'applicant_email': self.applicant_email,
            'applicant_phone': self.applicant_phone,
            'restaurant_name': self.restaurant_name,
            'restaurant_description': self.restaurant_description,
            'restaurant_address': self.restaurant_address,
            'restaurant_phone': self.restaurant_phone,
            'restaurant_type': self.restaurant_type,
            'status': self.status,
            'priority': self.priority,
            'moderator_notes': self.moderator_notes,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }


class ModerationLog(db.Model):
    """Log of all moderation actions for audit trail"""
    __tablename__ = 'moderation_logs'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('registration_requests.id'), nullable=False)
    moderator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # viewed, approved, rejected, requested_info, assigned, note_added
    previous_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    request = db.relationship('RegistrationRequest', backref='logs')
    moderator = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'moderator': self.moderator.username if self.moderator else None,
            'action': self.action,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class QRTemplateSettings(db.Model):
    """Global QR template settings managed by admin"""
    __tablename__ = 'qr_template_settings'

    id = db.Column(db.Integer, primary_key=True)
    saas_name = db.Column(db.String(100), default='RestaurantCMS')
    saas_logo_path = db.Column(db.String(255))
    primary_color = db.Column(db.String(7), default='#6366f1')
    secondary_color = db.Column(db.String(7), default='#1a1a2e')
    scan_text = db.Column(db.String(100), default='Scan to View Menu')
    powered_by_text = db.Column(db.String(100), default='Powered by')
    show_powered_by = db.Column(db.Boolean, default=True)
    template_style = db.Column(db.String(20), default='modern')  # modern, minimal, classic
    qr_size = db.Column(db.Integer, default=200)  # QR code size in pixels
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_settings(cls):
        """Get or create default settings"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings


class SystemSettings(db.Model):
    """Global system settings managed by admin"""
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)

    # Registration Moderation
    moderation_enabled = db.Column(db.Boolean, default=False)  # If True, new registrations need approval
    auto_approve_free_plans = db.Column(db.Boolean, default=True)  # Auto-approve free plan signups

    # Other system settings can be added here
    maintenance_mode = db.Column(db.Boolean, default=False)
    allow_new_registrations = db.Column(db.Boolean, default=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @classmethod
    def get_settings(cls):
        """Get or create default settings"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    @classmethod
    def is_moderation_enabled(cls):
        """Check if moderation is enabled"""
        settings = cls.get_settings()
        return settings.moderation_enabled


# Import public models
from app.models.public_models import PublicView, PublicFeedback, PublicMenuClick, PublicSearchLog

# Import website content models
from app.models.website_content_models import (
    HeroSection, Feature, HowItWorksStep, PricingPlan,
    Testimonial, FAQ, ContactInfo, FooterLink, FooterContent, SocialMediaLink,
    PaymentGateway, PaymentTransaction, Subscription, SubscriptionEvent,
    ScheduledBillingJob, SubscriptionStatus
)

# Import contact form models
from app.models.contact_models import ContactMessage

# Import order number service models
from app.services.order_number_service import DisplayOrderSlot, OrderNumberService, OrderNumberConfig

# Import onboarding models
from app.models.onboarding_models import RestaurantOnboarding, OnboardingStep, FeatureVisibility

# Import background job models
from app.models.background_job_models import BackgroundJob, JobExecutionLog, IdempotencyRecord, JobStatus, JobType

# Import tax models
from app.models.tax_models import TaxRule, OrderTaxSnapshot, TaxDefaults

# Import white-label models
from app.models.white_label_models import CustomDomain, WhiteLabelBranding

# Import compliance models
from app.models.compliance_models import (
    AuditLog, AuditLogCategory, AuditLogAction,
    DataExportRequest, DataDeletionRequest, PIIMaskingConfig
)

# Import operational safety models
from app.services.operational_safety import FeatureFlagModel
