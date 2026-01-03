from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    csrf.init_app(app)
    limiter.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.owner import owner_bp
    from app.routes.restaurants import restaurants_bp
    from app.routes.menu import menu_bp
    from app.routes.orders import orders_bp
    from app.routes.public import public_bp
    from app.routes.registration import registration_bp
    from app.routes.public_content_api import public_content_api  # Public website content API
    from app.routes.website_content_api import website_content_api  # Admin content management API
    from app.routes.public_admin import public_admin_bp  # Public admin routes

    csrf.exempt(auth_bp)
    csrf.exempt(restaurants_bp)
    csrf.exempt(menu_bp)
    csrf.exempt(orders_bp)
    csrf.exempt(public_bp)
    csrf.exempt(registration_bp)
    csrf.exempt(public_content_api)
    csrf.exempt(owner_bp)  # Exempt owner API routes for kitchen/customer screen

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/rock')
    app.register_blueprint(public_admin_bp, url_prefix='/rock/public')  # Public admin routes
    app.register_blueprint(owner_bp, url_prefix='')
    app.register_blueprint(restaurants_bp, url_prefix='/api/restaurants')
    app.register_blueprint(menu_bp, url_prefix='/api/menu')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(public_bp)
    app.register_blueprint(registration_bp, url_prefix='/api/registration')
    app.register_blueprint(public_content_api)  # Public content API (has /api/public prefix)
    app.register_blueprint(website_content_api)  # Admin content API (has /api/website-content prefix)

    from app.models import User, Restaurant, Table, Category, MenuItem, Order, OrderItem, RegistrationRequest, ModerationLog

    with app.app_context():
        db.create_all()
        create_admin_user(app)

        # Seed default website content on first run
        from app.seed_data import check_if_seeded, seed_all_website_content
        if not check_if_seeded():
            seed_all_website_content()

    # Role permissions mapping
    ROLE_PERMISSIONS = {
        'superadmin': ['dashboard', 'restaurants', 'users', 'orders', 'registrations', 'api_keys', 'settings', 'user_management'],
        'system_admin': ['dashboard', 'restaurants', 'users', 'orders', 'registrations', 'api_keys', 'settings', 'user_management'],
        'admin': ['dashboard', 'restaurants', 'orders', 'registrations'],
        'moderator': ['dashboard', 'registrations'],
    }

    # Context processor to inject admin user, permissions, and pending registrations
    @app.context_processor
    def inject_admin_context():
        from flask import session, has_request_context

        context = {
            'pending_registrations_count': 0,
            'admin_user': None,
            'has_permission': lambda p: False
        }

        # Only access session if we're in a request context
        if not has_request_context():
            return context

        if session.get('admin_logged_in') and session.get('admin_user_id'):
            admin_user = User.query.get(session.get('admin_user_id'))
            if admin_user:
                context['admin_user'] = admin_user
                context['pending_registrations_count'] = RegistrationRequest.query.filter_by(status='pending').count()

                # Create has_permission function for this user
                role = admin_user.role
                if role == 'system_admin':
                    role = 'superadmin'
                user_permissions = ROLE_PERMISSIONS.get(role, [])
                context['has_permission'] = lambda p, perms=user_permissions: p in perms

        return context

    return app

def create_admin_user(app):
    from app.models import User
    admin = User.query.filter_by(role='system_admin').first()
    if not admin:
        admin = User(
            username=app.config['ADMIN_USERNAME'],
            email=app.config['ADMIN_EMAIL'],
            role='system_admin'
        )
        admin.set_password(app.config['ADMIN_PASSWORD'])
        db.session.add(admin)
        db.session.commit()

