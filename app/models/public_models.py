"""
Public Module Models
Database models specific to public module
"""
from datetime import datetime
from app import db

class PublicView(db.Model):
    """Track public views of restaurants and menus"""
    __tablename__ = 'public_views'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.String(255))
    referrer = db.Column(db.String(255))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))

    restaurant = db.relationship('Restaurant', backref='public_views', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'ip_address': self.ip_address,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None
        }


class PublicFeedback(db.Model):
    """Public feedback and ratings"""
    __tablename__ = 'public_feedback'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 stars
    comment = db.Column(db.Text)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(120))
    ip_address = db.Column(db.String(45))
    is_verified = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    restaurant = db.relationship('Restaurant', backref='feedbacks', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'rating': self.rating,
            'comment': self.comment,
            'customer_name': self.customer_name,
            'is_verified': self.is_verified,
            'is_published': self.is_published,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PublicMenuClick(db.Model):
    """Track menu item clicks/views"""
    __tablename__ = 'public_menu_clicks'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    ip_address = db.Column(db.String(45))
    session_id = db.Column(db.String(100))
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)

    restaurant = db.relationship('Restaurant', backref='menu_clicks', lazy=True)
    menu_item = db.relationship('MenuItem', backref='click_tracks', lazy=True)
    category = db.relationship('Category', backref='click_tracks', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'menu_item_id': self.menu_item_id,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None
        }


class PublicSearchLog(db.Model):
    """Log public search queries for analytics"""
    __tablename__ = 'public_search_logs'

    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(255), nullable=False)
    results_count = db.Column(db.Integer, default=0)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    searched_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'search_query': self.search_query,
            'results_count': self.results_count,
            'searched_at': self.searched_at.isoformat() if self.searched_at else None
        }

