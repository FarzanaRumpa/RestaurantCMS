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
        self.password_hash = generate_password_hash(password)

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
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    qr_code_path = db.Column(db.String(255))  # Main restaurant QR code
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tables = db.relationship('Table', backref='restaurant', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='restaurant', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='restaurant', lazy=True, cascade='all, delete-orphan')

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
    access_token = db.Column(db.String(50), unique=True, default=lambda: str(uuid.uuid4())[:12])
    qr_code_path = db.Column(db.String(255))
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('restaurant_id', 'table_number', name='unique_table_per_restaurant'),)

    def to_dict(self):
        return {
            'id': self.id,
            'table_number': self.table_number,
            'access_token': self.access_token,
            'qr_code_url': f'/static/qrcodes/{self.qr_code_path}' if self.qr_code_path else None
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
    order_number = db.Column(db.String(20), unique=True)
    table_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    total_price = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def generate_order_number(self):
        self.order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{self.id or uuid.uuid4().hex[:4].upper()}"

    def calculate_total(self):
        self.total_price = sum(item.subtotal for item in self.items)

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'table_number': self.table_number,
            'status': self.status,
            'total_price': self.total_price,
            'notes': self.notes,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
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


# Import public models
from app.models.public_models import PublicView, PublicFeedback, PublicMenuClick, PublicSearchLog

# Import website content models
from app.models.website_content_models import (
    HeroSection, Feature, HowItWorksStep, PricingPlan,
    Testimonial, FAQ, ContactInfo, FooterLink, FooterContent, SocialMediaLink
)

# Import contact form models
from app.models.contact_models import ContactMessage

