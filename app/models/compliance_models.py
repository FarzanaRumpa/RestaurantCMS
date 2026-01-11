"""
Compliance & Data Governance Models
===================================
Database models for audit logging, data export, and deletion workflows.

Features:
1. Comprehensive audit logging
2. Data export tracking
3. Soft delete → Hard delete workflows
4. PII handling
"""

from datetime import datetime
from app import db
import json
import uuid


class AuditLogCategory:
    """Audit log category constants"""
    BILLING = 'billing'
    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    CONFIGURATION = 'configuration'
    DATA_ACCESS = 'data_access'
    DATA_MODIFICATION = 'data_modification'
    DATA_DELETION = 'data_deletion'
    SECURITY = 'security'
    SUBSCRIPTION = 'subscription'
    USER_MANAGEMENT = 'user_management'


class AuditLogAction:
    """Audit log action constants"""
    # Authentication
    LOGIN = 'login'
    LOGOUT = 'logout'
    LOGIN_FAILED = 'login_failed'
    PASSWORD_CHANGED = 'password_changed'
    PASSWORD_RESET = 'password_reset'

    # Authorization
    ROLE_CHANGED = 'role_changed'
    PERMISSION_GRANTED = 'permission_granted'
    PERMISSION_REVOKED = 'permission_revoked'

    # Billing
    PAYMENT_PROCESSED = 'payment_processed'
    PAYMENT_FAILED = 'payment_failed'
    SUBSCRIPTION_CREATED = 'subscription_created'
    SUBSCRIPTION_UPDATED = 'subscription_updated'
    SUBSCRIPTION_CANCELLED = 'subscription_cancelled'
    INVOICE_GENERATED = 'invoice_generated'
    REFUND_ISSUED = 'refund_issued'

    # Configuration
    SETTINGS_CHANGED = 'settings_changed'
    FEATURE_ENABLED = 'feature_enabled'
    FEATURE_DISABLED = 'feature_disabled'
    PLAN_UPGRADED = 'plan_upgraded'
    PLAN_DOWNGRADED = 'plan_downgraded'

    # Data operations
    DATA_EXPORTED = 'data_exported'
    DATA_DELETED = 'data_deleted'
    DATA_ARCHIVED = 'data_archived'
    DATA_RESTORED = 'data_restored'

    # User management
    USER_CREATED = 'user_created'
    USER_UPDATED = 'user_updated'
    USER_DELETED = 'user_deleted'
    USER_SUSPENDED = 'user_suspended'
    USER_REACTIVATED = 'user_reactivated'


class AuditLog(db.Model):
    """
    Comprehensive audit log for compliance.

    Tracks all significant actions for:
    - Billing changes
    - Role/permission changes
    - Configuration changes
    - Data access and modifications
    """
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.String(50), unique=True, default=lambda: f"audit_{uuid.uuid4().hex[:16]}")

    # Classification
    category = db.Column(db.String(50), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), default='info')  # info, warning, critical

    # Actor (who performed the action)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    actor_type = db.Column(db.String(20), default='user')  # user, system, webhook, api
    actor_ip = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    actor_user_agent = db.Column(db.Text, nullable=True)

    # Target (what was affected)
    target_type = db.Column(db.String(50), nullable=True)  # user, restaurant, order, subscription
    target_id = db.Column(db.String(100), nullable=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=True, index=True)

    # Details
    description = db.Column(db.Text, nullable=True)
    old_value = db.Column(db.Text, nullable=True)  # JSON - previous state
    new_value = db.Column(db.Text, nullable=True)  # JSON - new state
    extra_data = db.Column(db.Text, nullable=True)  # JSON - additional context

    # Request context
    request_id = db.Column(db.String(50), nullable=True)  # Correlation ID
    request_path = db.Column(db.String(255), nullable=True)
    request_method = db.Column(db.String(10), nullable=True)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Indexes for efficient querying
    __table_args__ = (
        db.Index('ix_audit_actor_date', 'actor_id', 'created_at'),
        db.Index('ix_audit_category_action', 'category', 'action'),
        db.Index('ix_audit_target', 'target_type', 'target_id'),
    )

    def set_old_value(self, value):
        if value is not None:
            self.old_value = json.dumps(value, default=str)

    def set_new_value(self, value):
        if value is not None:
            self.new_value = json.dumps(value, default=str)

    def set_extra_data(self, value):
        if value is not None:
            self.extra_data = json.dumps(value, default=str)

    # Alias for backward compatibility
    def set_metadata(self, value):
        self.set_extra_data(value)

    def get_old_value(self):
        if self.old_value:
            try:
                return json.loads(self.old_value)
            except:
                return self.old_value
        return None

    def get_new_value(self):
        if self.new_value:
            try:
                return json.loads(self.new_value)
            except:
                return self.new_value
        return None

    def to_dict(self):
        return {
            'id': self.log_id,
            'category': self.category,
            'action': self.action,
            'severity': self.severity,
            'actor_type': self.actor_type,
            'actor_id': self.actor_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'restaurant_id': self.restaurant_id,
            'description': self.description,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DataExportRequest(db.Model):
    """
    Track data export requests for compliance.

    Supports GDPR right to data portability.
    """
    __tablename__ = 'data_export_requests'

    id = db.Column(db.Integer, primary_key=True)
    export_id = db.Column(db.String(50), unique=True, default=lambda: f"export_{uuid.uuid4().hex[:16]}")

    # Requester
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Export configuration
    export_type = db.Column(db.String(50), default='full')  # full, orders, menu, invoices, customers
    date_from = db.Column(db.DateTime, nullable=True)
    date_to = db.Column(db.DateTime, nullable=True)
    format = db.Column(db.String(20), default='json')  # json, csv, xlsx

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed, expired
    progress = db.Column(db.Integer, default=0)  # 0-100

    # Result
    file_path = db.Column(db.String(500), nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    download_url = db.Column(db.String(500), nullable=True)
    download_token = db.Column(db.String(100), nullable=True)
    download_expires_at = db.Column(db.DateTime, nullable=True)
    downloaded_at = db.Column(db.DateTime, nullable=True)

    # Error handling
    error_message = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    restaurant = db.relationship('Restaurant', backref='export_requests')
    requested_by = db.relationship('User', backref='data_export_requests')

    def generate_download_token(self):
        import secrets
        self.download_token = secrets.token_urlsafe(32)
        return self.download_token

    def to_dict(self):
        return {
            'id': self.export_id,
            'export_type': self.export_type,
            'format': self.format,
            'status': self.status,
            'progress': self.progress,
            'file_size_bytes': self.file_size_bytes,
            'download_expires_at': self.download_expires_at.isoformat() if self.download_expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class DataDeletionRequest(db.Model):
    """
    Track data deletion requests for GDPR compliance.

    Implements soft delete → hard delete workflow.
    """
    __tablename__ = 'data_deletion_requests'

    id = db.Column(db.Integer, primary_key=True)
    deletion_id = db.Column(db.String(50), unique=True, default=lambda: f"delete_{uuid.uuid4().hex[:16]}")

    # Requester
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Deletion scope
    deletion_type = db.Column(db.String(50), default='account')  # account, orders, customers, full
    reason = db.Column(db.Text, nullable=True)

    # Workflow
    status = db.Column(db.String(20), default='pending')  # pending, approved, soft_deleted, hard_deleted, cancelled
    requires_approval = db.Column(db.Boolean, default=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    # Retention
    soft_delete_at = db.Column(db.DateTime, nullable=True)
    hard_delete_scheduled = db.Column(db.DateTime, nullable=True)  # Usually 30 days after soft delete
    hard_delete_at = db.Column(db.DateTime, nullable=True)

    # Confirmation
    confirmation_token = db.Column(db.String(100), nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    restaurant = db.relationship('Restaurant', backref='deletion_requests')
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='deletion_requests')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

    def to_dict(self):
        return {
            'id': self.deletion_id,
            'deletion_type': self.deletion_type,
            'status': self.status,
            'requires_approval': self.requires_approval,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'soft_delete_at': self.soft_delete_at.isoformat() if self.soft_delete_at else None,
            'hard_delete_scheduled': self.hard_delete_scheduled.isoformat() if self.hard_delete_scheduled else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PIIMaskingConfig:
    """
    Configuration for PII masking in logs and exports.
    """

    # Fields that should be masked
    PII_FIELDS = [
        'email', 'phone', 'password', 'password_hash',
        'card_number', 'cvv', 'card_expiry',
        'address', 'postal_code', 'zip_code',
        'ssn', 'national_id', 'passport',
        'bank_account', 'routing_number',
        'api_key', 'api_secret', 'token',
        'customer_phone', 'customer_email', 'customer_name'
    ]

    # Masking patterns
    EMAIL_MASK_PATTERN = r'^(.{2}).*(@.*)$'
    PHONE_MASK_PATTERN = r'^(.{3}).*(.{2})$'

    @classmethod
    def mask_value(cls, field_name: str, value: str) -> str:
        """Mask a PII value based on field type"""
        if not value:
            return value

        field_lower = field_name.lower()

        if 'email' in field_lower:
            # Show first 2 chars and domain
            parts = value.split('@')
            if len(parts) == 2:
                return f"{parts[0][:2]}***@{parts[1]}"
            return '***@***.***'

        if 'phone' in field_lower:
            # Show first 3 and last 2 digits
            digits = ''.join(filter(str.isdigit, value))
            if len(digits) >= 5:
                return f"{digits[:3]}***{digits[-2:]}"
            return '***'

        if any(x in field_lower for x in ['card', 'account', 'routing']):
            # Show last 4 digits only
            digits = ''.join(filter(str.isdigit, value))
            if len(digits) >= 4:
                return f"****{digits[-4:]}"
            return '****'

        if any(x in field_lower for x in ['password', 'secret', 'token', 'key', 'cvv']):
            # Fully mask
            return '********'

        if any(x in field_lower for x in ['name', 'address']):
            # Show first letter only
            if len(value) > 0:
                return f"{value[0]}***"
            return '***'

        # Default masking
        return '***'

    @classmethod
    def mask_dict(cls, data: dict, fields_to_mask: list = None) -> dict:
        """Mask PII fields in a dictionary"""
        if not data:
            return data

        masked = data.copy()
        fields = fields_to_mask or cls.PII_FIELDS

        for key, value in masked.items():
            if any(pii in key.lower() for pii in fields):
                if isinstance(value, str):
                    masked[key] = cls.mask_value(key, value)
                elif isinstance(value, dict):
                    masked[key] = cls.mask_dict(value, fields)

        return masked

