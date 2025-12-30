"""
Public Website Content Models
Database models for storing and managing public-facing website content
"""
from datetime import datetime
from app import db

class HeroSection(db.Model):
    """Hero section content for homepage"""
    __tablename__ = 'hero_sections'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.Text)
    cta_text = db.Column(db.String(100))  # Call to Action button text
    cta_link = db.Column(db.String(500))  # Call to Action link
    background_image = db.Column(db.String(500))  # Image URL or path
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)  # For multiple hero sections
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='hero_sections')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subtitle': self.subtitle,
            'cta_text': self.cta_text,
            'cta_link': self.cta_link,
            'background_image': self.background_image,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Feature(db.Model):
    """Features section for showcasing platform capabilities"""
    __tablename__ = 'features'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100))  # Icon class name (e.g., 'bi-shop', 'fa-qrcode')
    icon_image = db.Column(db.String(500))  # Alternative: icon image URL
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    link = db.Column(db.String(500))  # Optional link to feature details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='features')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'icon_image': self.icon_image,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'link': self.link,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class HowItWorksStep(db.Model):
    """Steps explaining how the platform works"""
    __tablename__ = 'how_it_works_steps'

    id = db.Column(db.Integer, primary_key=True)
    step_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100))
    icon_image = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='how_it_works_steps')

    def to_dict(self):
        return {
            'id': self.id,
            'step_number': self.step_number,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'icon_image': self.icon_image,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PricingPlan(db.Model):
    """Pricing plans for the platform"""
    __tablename__ = 'pricing_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Monthly price
    price_period = db.Column(db.String(50), default='month')  # month, year, one-time
    currency = db.Column(db.String(10), default='USD')
    features = db.Column(db.Text, nullable=False)  # JSON or newline-separated list
    is_highlighted = db.Column(db.Boolean, default=False)  # Popular/recommended plan
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    cta_text = db.Column(db.String(100), default='Get Started')
    cta_link = db.Column(db.String(500))
    max_restaurants = db.Column(db.Integer)  # Plan limits
    max_menu_items = db.Column(db.Integer)
    max_orders_per_month = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='pricing_plans')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0,
            'price_period': self.price_period,
            'currency': self.currency,
            'features': self.features,
            'is_highlighted': self.is_highlighted,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'cta_text': self.cta_text,
            'cta_link': self.cta_link,
            'limits': {
                'max_restaurants': self.max_restaurants,
                'max_menu_items': self.max_menu_items,
                'max_orders_per_month': self.max_orders_per_month
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Testimonial(db.Model):
    """Customer testimonials and reviews"""
    __tablename__ = 'testimonials'

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_role = db.Column(db.String(100))  # e.g., "Restaurant Owner", "Manager"
    company_name = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-5 stars
    avatar_url = db.Column(db.String(500))  # Customer photo
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)  # Featured on homepage
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='testimonials')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_role': self.customer_role,
            'company_name': self.company_name,
            'message': self.message,
            'rating': self.rating,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FAQ(db.Model):
    """Frequently Asked Questions"""
    __tablename__ = 'faqs'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))  # e.g., "General", "Pricing", "Technical"
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)  # Track popular questions
    helpful_count = db.Column(db.Integer, default=0)  # User feedback
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='faqs')

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'view_count': self.view_count,
            'helpful_count': self.helpful_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ContactInfo(db.Model):
    """Contact information and business details"""
    __tablename__ = 'contact_info'

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))  # e.g., "Support Email", "Sales Phone"
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    website = db.Column(db.String(500))
    support_hours = db.Column(db.String(200))  # e.g., "Mon-Fri 9AM-5PM"
    is_primary = db.Column(db.Boolean, default=False)  # Primary contact
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='contact_info')

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'website': self.website,
            'support_hours': self.support_hours,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FooterLink(db.Model):
    """Footer navigation links"""
    __tablename__ = 'footer_links'

    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(100))  # e.g., "Company", "Resources", "Legal"
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    icon = db.Column(db.String(100))
    target = db.Column(db.String(20), default='_self')  # _self, _blank
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='footer_links')

    def to_dict(self):
        return {
            'id': self.id,
            'section': self.section,
            'title': self.title,
            'url': self.url,
            'icon': self.icon,
            'target': self.target,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FooterContent(db.Model):
    """Footer content (copyright, social links, etc.)"""
    __tablename__ = 'footer_content'

    id = db.Column(db.Integer, primary_key=True)
    copyright_text = db.Column(db.Text)
    tagline = db.Column(db.String(500))
    logo_url = db.Column(db.String(500))

    # Social media links
    facebook_url = db.Column(db.String(500))
    twitter_url = db.Column(db.String(500))
    instagram_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))
    youtube_url = db.Column(db.String(500))

    # App store links
    app_store_url = db.Column(db.String(500))
    play_store_url = db.Column(db.String(500))

    # Additional content
    about_text = db.Column(db.Text)
    newsletter_text = db.Column(db.String(500))

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='footer_content')

    def to_dict(self):
        return {
            'id': self.id,
            'copyright_text': self.copyright_text,
            'tagline': self.tagline,
            'logo_url': self.logo_url,
            'social_media': {
                'facebook': self.facebook_url,
                'twitter': self.twitter_url,
                'instagram': self.instagram_url,
                'linkedin': self.linkedin_url,
                'youtube': self.youtube_url
            },
            'app_stores': {
                'app_store': self.app_store_url,
                'play_store': self.play_store_url
            },
            'about_text': self.about_text,
            'newsletter_text': self.newsletter_text,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SocialMediaLink(db.Model):
    """Social media links (flexible alternative to hardcoded fields)"""
    __tablename__ = 'social_media_links'

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, etc.
    url = db.Column(db.String(500), nullable=False)
    icon = db.Column(db.String(100))  # Icon class
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='social_media_links')

    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'url': self.url,
            'icon': self.icon,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

