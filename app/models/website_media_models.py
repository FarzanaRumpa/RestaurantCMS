"""
Website Media & Theme Models
Database models for managing website images, banners, and theme settings
"""
from datetime import datetime
from app import db


class WebsiteMedia(db.Model):
    """Store and manage all website media files"""
    __tablename__ = 'website_media'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))  # image, video, document
    mime_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)  # in bytes
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    alt_text = db.Column(db.String(255))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # hero, banner, logo, background, gallery
    is_active = db.Column(db.Boolean, default=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    uploaded_by = db.relationship('User', backref='uploaded_media', foreign_keys=[uploaded_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'alt_text': self.alt_text,
            'description': self.description,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WebsiteTheme(db.Model):
    """Website theme and color settings"""
    __tablename__ = 'website_themes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Hero Section Colors
    hero_gradient_start = db.Column(db.String(20), default='#6366f1')
    hero_gradient_middle = db.Column(db.String(20), default='#8b5cf6')
    hero_gradient_end = db.Column(db.String(20), default='#ec4899')
    hero_text_color = db.Column(db.String(20), default='#ffffff')
    hero_overlay_opacity = db.Column(db.Float, default=0.5)

    # Primary Colors
    primary_color = db.Column(db.String(20), default='#6366f1')
    secondary_color = db.Column(db.String(20), default='#ec4899')
    accent_color = db.Column(db.String(20), default='#06b6d4')

    # Background Colors
    body_bg_color = db.Column(db.String(20), default='#ffffff')
    section_bg_light = db.Column(db.String(20), default='#f8fafc')
    section_bg_dark = db.Column(db.String(20), default='#1e1b4b')

    # Text Colors
    text_primary = db.Column(db.String(20), default='#334155')
    text_secondary = db.Column(db.String(20), default='#64748b')
    text_light = db.Column(db.String(20), default='#ffffff')

    # Button Colors
    btn_primary_bg = db.Column(db.String(20), default='#6366f1')
    btn_primary_text = db.Column(db.String(20), default='#ffffff')
    btn_secondary_bg = db.Column(db.String(20), default='#ec4899')
    btn_secondary_text = db.Column(db.String(20), default='#ffffff')

    # Footer Colors
    footer_bg_color = db.Column(db.String(20), default='#1e1b4b')
    footer_text_color = db.Column(db.String(20), default='#94a3b8')

    # Hero Background Image
    hero_bg_image_id = db.Column(db.Integer, db.ForeignKey('website_media.id'))
    hero_bg_type = db.Column(db.String(20), default='gradient')  # gradient, image, video

    # Logo
    logo_image_id = db.Column(db.Integer, db.ForeignKey('website_media.id'))
    logo_text = db.Column(db.String(100), default='RestaurantPro')

    # Favicon
    favicon_id = db.Column(db.Integer, db.ForeignKey('website_media.id'))

    is_active = db.Column(db.Boolean, default=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hero_bg_image = db.relationship('WebsiteMedia', foreign_keys=[hero_bg_image_id])
    logo_image = db.relationship('WebsiteMedia', foreign_keys=[logo_image_id])
    favicon = db.relationship('WebsiteMedia', foreign_keys=[favicon_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hero_gradient_start': self.hero_gradient_start,
            'hero_gradient_middle': self.hero_gradient_middle,
            'hero_gradient_end': self.hero_gradient_end,
            'hero_text_color': self.hero_text_color,
            'hero_overlay_opacity': self.hero_overlay_opacity,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'body_bg_color': self.body_bg_color,
            'section_bg_light': self.section_bg_light,
            'section_bg_dark': self.section_bg_dark,
            'text_primary': self.text_primary,
            'text_secondary': self.text_secondary,
            'btn_primary_bg': self.btn_primary_bg,
            'btn_secondary_bg': self.btn_secondary_bg,
            'footer_bg_color': self.footer_bg_color,
            'footer_text_color': self.footer_text_color,
            'hero_bg_type': self.hero_bg_type,
            'hero_bg_image': self.hero_bg_image.to_dict() if self.hero_bg_image else None,
            'logo_image': self.logo_image.to_dict() if self.logo_image else None,
            'logo_text': self.logo_text,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WebsiteBanner(db.Model):
    """Manage website banners for different sections"""
    __tablename__ = 'website_banners'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    section = db.Column(db.String(50), nullable=False)  # hero, promo, cta, footer

    # Content
    title = db.Column(db.String(255))
    subtitle = db.Column(db.Text)
    cta_text = db.Column(db.String(100))
    cta_link = db.Column(db.String(500))

    # Background
    bg_type = db.Column(db.String(20), default='color')  # color, gradient, image
    bg_color = db.Column(db.String(20), default='#6366f1')
    bg_gradient_start = db.Column(db.String(20))
    bg_gradient_end = db.Column(db.String(20))
    bg_image_id = db.Column(db.Integer, db.ForeignKey('website_media.id'))
    bg_overlay_color = db.Column(db.String(20), default='rgba(0,0,0,0.5)')

    # Text Styling
    text_color = db.Column(db.String(20), default='#ffffff')
    text_align = db.Column(db.String(20), default='center')  # left, center, right

    # Display Settings
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bg_image = db.relationship('WebsiteMedia', foreign_keys=[bg_image_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'section': self.section,
            'title': self.title,
            'subtitle': self.subtitle,
            'cta_text': self.cta_text,
            'cta_link': self.cta_link,
            'bg_type': self.bg_type,
            'bg_color': self.bg_color,
            'bg_gradient_start': self.bg_gradient_start,
            'bg_gradient_end': self.bg_gradient_end,
            'bg_image': self.bg_image.to_dict() if self.bg_image else None,
            'bg_overlay_color': self.bg_overlay_color,
            'text_color': self.text_color,
            'text_align': self.text_align,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

