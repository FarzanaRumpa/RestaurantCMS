"""
Contact Form Models
Database model for storing contact form submissions
"""
from datetime import datetime
from app import db


class ContactMessage(db.Model):
    """Contact form submissions"""
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)

    # Metadata
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    referrer = db.Column(db.String(500))

    # Status tracking
    status = db.Column(db.String(20), default='new')  # new, read, replied, archived, spam
    is_spam = db.Column(db.Boolean, default=False)
    admin_notes = db.Column(db.Text)
    replied_at = db.Column(db.DateTime)
    replied_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    replied_by = db.relationship('User', backref='contact_replies', foreign_keys=[replied_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'is_spam': self.is_spam,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'replied_at': self.replied_at.isoformat() if self.replied_at else None,
            'replied_by': self.replied_by.username if self.replied_by else None
        }

    def __repr__(self):
        return f'<ContactMessage {self.id}: {self.name} - {self.subject}>'

