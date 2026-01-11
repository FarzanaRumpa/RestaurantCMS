"""
White-Label & Custom Domain Models
==================================
Database models for enterprise white-label support.

Features:
- Custom domain mapping per restaurant
- SSL certificate tracking
- Branding configuration
- Plan-gated white-label access
"""

from datetime import datetime
from app import db
import json


class CustomDomain(db.Model):
    """
    Custom domain configuration for white-label tenants.

    Each restaurant can optionally have a custom domain for customer-facing pages.
    Admin/owner dashboards remain on the SaaS domain.
    """
    __tablename__ = 'custom_domains'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, unique=True)

    # Domain configuration
    domain = db.Column(db.String(255), nullable=False, unique=True, index=True)
    subdomain = db.Column(db.String(100), nullable=True)  # If using subdomain of SaaS domain

    # Verification status
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    verification_method = db.Column(db.String(20), default='dns')  # dns, file, cname
    verified_at = db.Column(db.DateTime, nullable=True)

    # SSL certificate status
    ssl_enabled = db.Column(db.Boolean, default=False)
    ssl_issued_at = db.Column(db.DateTime, nullable=True)
    ssl_expires_at = db.Column(db.DateTime, nullable=True)
    ssl_provider = db.Column(db.String(50), default='letsencrypt')
    ssl_auto_renew = db.Column(db.Boolean, default=True)
    ssl_last_renewal_attempt = db.Column(db.DateTime, nullable=True)
    ssl_renewal_error = db.Column(db.Text, nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=False, index=True)
    status = db.Column(db.String(20), default='pending')  # pending, verifying, active, error, suspended

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    restaurant = db.relationship('Restaurant', backref=db.backref('custom_domain', uselist=False, lazy=True))

    def generate_verification_token(self):
        """Generate a unique verification token"""
        import uuid
        self.verification_token = f"rcms-verify-{uuid.uuid4().hex[:16]}"
        return self.verification_token

    def to_dict(self):
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'domain': self.domain,
            'subdomain': self.subdomain,
            'is_verified': self.is_verified,
            'verification_method': self.verification_method,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'ssl_enabled': self.ssl_enabled,
            'ssl_expires_at': self.ssl_expires_at.isoformat() if self.ssl_expires_at else None,
            'is_active': self.is_active,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WhiteLabelBranding(db.Model):
    """
    White-label branding configuration.

    Allows complete SaaS branding removal for enterprise tenants.
    Applies to: ordering pages, QR codes, invoices/receipts.
    """
    __tablename__ = 'white_label_branding'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, unique=True)

    # Branding enabled
    is_enabled = db.Column(db.Boolean, default=False)

    # Logo and colors
    logo_url = db.Column(db.String(500), nullable=True)
    logo_dark_url = db.Column(db.String(500), nullable=True)  # For dark backgrounds
    favicon_url = db.Column(db.String(500), nullable=True)
    primary_color = db.Column(db.String(7), default='#6366f1')
    secondary_color = db.Column(db.String(7), default='#1a1a2e')
    accent_color = db.Column(db.String(7), nullable=True)

    # Typography
    heading_font = db.Column(db.String(100), nullable=True)
    body_font = db.Column(db.String(100), nullable=True)

    # Text content
    company_name = db.Column(db.String(200), nullable=True)
    tagline = db.Column(db.String(500), nullable=True)
    footer_text = db.Column(db.Text, nullable=True)
    copyright_text = db.Column(db.String(500), nullable=True)

    # Contact
    support_email = db.Column(db.String(120), nullable=True)
    support_phone = db.Column(db.String(20), nullable=True)
    support_url = db.Column(db.String(500), nullable=True)

    # Legal links
    privacy_policy_url = db.Column(db.String(500), nullable=True)
    terms_of_service_url = db.Column(db.String(500), nullable=True)

    # SaaS branding visibility
    hide_powered_by = db.Column(db.Boolean, default=False)
    hide_saas_logo = db.Column(db.Boolean, default=False)
    hide_saas_links = db.Column(db.Boolean, default=False)

    # Custom CSS/JS (advanced)
    custom_css = db.Column(db.Text, nullable=True)
    custom_head_html = db.Column(db.Text, nullable=True)  # For analytics, etc.

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    restaurant = db.relationship('Restaurant', backref=db.backref('white_label_branding', uselist=False, lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'is_enabled': self.is_enabled,
            'logo_url': self.logo_url,
            'favicon_url': self.favicon_url,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'company_name': self.company_name,
            'tagline': self.tagline,
            'hide_powered_by': self.hide_powered_by,
            'hide_saas_logo': self.hide_saas_logo,
            'support_email': self.support_email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_css_variables(self):
        """Get CSS custom properties for theming"""
        return {
            '--brand-primary': self.primary_color or '#6366f1',
            '--brand-secondary': self.secondary_color or '#1a1a2e',
            '--brand-accent': self.accent_color or self.primary_color or '#6366f1'
        }

