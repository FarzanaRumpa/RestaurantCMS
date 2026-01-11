"""
Background Job Models
=====================
Database models for tracking and managing background jobs.

This system provides:
1. Job scheduling and tracking
2. Retry logic with exponential backoff
3. Dead-letter queue for failed jobs
4. Idempotency key storage
5. Execution tracing via logs
"""

from datetime import datetime, timedelta
from app import db
import uuid
import json


class JobStatus:
    """Job status constants"""
    PENDING = 'pending'
    SCHEDULED = 'scheduled'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRYING = 'retrying'
    DEAD = 'dead'  # Max retries exceeded, moved to dead letter queue
    CANCELLED = 'cancelled'


class JobType:
    """Job type constants for naming convention"""
    # Subscription & Billing
    TRIAL_EXPIRATION = 'subscription.trial_expiration'
    SUBSCRIPTION_RENEWAL = 'subscription.renewal'
    PAYMENT_RETRY = 'subscription.payment_retry'
    SUBSCRIPTION_REMINDER = 'subscription.reminder'
    GRACE_PERIOD_CHECK = 'subscription.grace_period_check'
    SUBSCRIPTION_DOWNGRADE = 'subscription.downgrade'
    SUBSCRIPTION_SUSPEND = 'subscription.suspend'

    # Order Management
    ORDER_CLEANUP = 'order.cleanup_display_numbers'
    ORDER_NOTIFICATION = 'order.notification'

    # Notifications
    NOTIFICATION_EMAIL = 'notification.email'
    NOTIFICATION_SMS = 'notification.sms'
    NOTIFICATION_PUSH = 'notification.push'

    # Maintenance
    CLEANUP_EXPIRED_SESSIONS = 'maintenance.cleanup_sessions'
    CLEANUP_OLD_LOGS = 'maintenance.cleanup_logs'
    DATABASE_OPTIMIZATION = 'maintenance.db_optimize'


class BackgroundJob(db.Model):
    """
    Main table for tracking background jobs.

    Features:
    - Idempotency via unique job_key
    - Retry tracking with exponential backoff
    - Detailed execution logging
    - Dead letter queue support
    """
    __tablename__ = 'background_jobs'

    id = db.Column(db.Integer, primary_key=True)

    # Unique identifier for deduplication
    job_id = db.Column(db.String(50), unique=True, nullable=False,
                       default=lambda: f"job_{uuid.uuid4().hex[:16]}")

    # Idempotency key for ensuring job uniqueness
    # Format: {job_type}:{entity_id}:{date} e.g., "subscription.renewal:123:2024-01-15"
    idempotency_key = db.Column(db.String(255), unique=True, nullable=True, index=True)

    # Job classification
    job_type = db.Column(db.String(100), nullable=False, index=True)
    job_name = db.Column(db.String(255))  # Human readable name

    # Associated entities
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=True, index=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=True)
    order_id = db.Column(db.Integer, nullable=True)  # Not FK to avoid issues

    # Job payload (JSON)
    payload = db.Column(db.Text, nullable=True)

    # Scheduling
    scheduled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Status tracking
    status = db.Column(db.String(20), default=JobStatus.PENDING, index=True)
    priority = db.Column(db.Integer, default=5)  # 1 = highest, 10 = lowest

    # Retry configuration
    max_retries = db.Column(db.Integer, default=3)
    retry_count = db.Column(db.Integer, default=0)
    retry_delay_seconds = db.Column(db.Integer, default=300)  # 5 minutes base delay
    next_retry_at = db.Column(db.DateTime, nullable=True)

    # Execution results
    result = db.Column(db.Text, nullable=True)  # JSON result
    error_message = db.Column(db.Text, nullable=True)
    error_trace = db.Column(db.Text, nullable=True)  # Stack trace

    # Locking for concurrent processing
    locked_by = db.Column(db.String(100), nullable=True)  # Worker ID
    locked_at = db.Column(db.DateTime, nullable=True)
    lock_expires_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        db.Index('ix_job_status_scheduled', 'status', 'scheduled_at'),
        db.Index('ix_job_type_status', 'job_type', 'status'),
        db.Index('ix_job_restaurant_status', 'restaurant_id', 'status'),
    )

    def get_payload(self) -> dict:
        """Parse and return the job payload"""
        if not self.payload:
            return {}
        try:
            return json.loads(self.payload)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_payload(self, data: dict):
        """Set the job payload from a dict"""
        self.payload = json.dumps(data)

    def get_result(self) -> dict:
        """Parse and return the job result"""
        if not self.result:
            return {}
        try:
            return json.loads(self.result)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_result(self, data: dict):
        """Set the job result from a dict"""
        self.result = json.dumps(data)

    def calculate_next_retry(self) -> datetime:
        """
        Calculate next retry time using exponential backoff.

        Formula: base_delay * (2 ^ retry_count)
        With jitter to prevent thundering herd
        """
        import random

        base_delay = self.retry_delay_seconds
        exponential_delay = base_delay * (2 ** self.retry_count)

        # Add jitter (±20%)
        jitter = exponential_delay * 0.2 * (random.random() - 0.5) * 2
        final_delay = max(60, exponential_delay + jitter)  # Minimum 1 minute

        # Cap at 24 hours
        final_delay = min(final_delay, 86400)

        return datetime.utcnow() + timedelta(seconds=final_delay)

    def can_retry(self) -> bool:
        """Check if this job can be retried"""
        return self.retry_count < self.max_retries

    def mark_started(self, worker_id: str = None):
        """Mark job as started"""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.locked_by = worker_id
        self.locked_at = datetime.utcnow()
        self.lock_expires_at = datetime.utcnow() + timedelta(minutes=30)

    def mark_completed(self, result: dict = None):
        """Mark job as completed successfully"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.locked_by = None
        self.locked_at = None
        self.lock_expires_at = None
        if result:
            self.set_result(result)

    def mark_failed(self, error: str, trace: str = None):
        """Mark job as failed and schedule retry if possible"""
        self.error_message = error
        self.error_trace = trace
        self.locked_by = None
        self.locked_at = None
        self.lock_expires_at = None

        if self.can_retry():
            self.retry_count += 1
            self.status = JobStatus.RETRYING
            self.next_retry_at = self.calculate_next_retry()
        else:
            self.status = JobStatus.DEAD
            self.completed_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_type': self.job_type,
            'job_name': self.job_name,
            'idempotency_key': self.idempotency_key,
            'status': self.status,
            'priority': self.priority,
            'restaurant_id': self.restaurant_id,
            'subscription_id': self.subscription_id,
            'payload': self.get_payload(),
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'error_message': self.error_message,
            'result': self.get_result(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class JobExecutionLog(db.Model):
    """
    Detailed execution log for job auditing.

    Each job attempt creates a log entry for traceability.
    """
    __tablename__ = 'job_execution_logs'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('background_jobs.id'), nullable=False, index=True)

    # Execution attempt
    attempt_number = db.Column(db.Integer, nullable=False, default=1)

    # Worker info
    worker_id = db.Column(db.String(100))
    worker_host = db.Column(db.String(255))

    # Timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)

    # Status
    status = db.Column(db.String(20), nullable=False)  # started, completed, failed
    success = db.Column(db.Boolean, default=False)

    # Details
    input_data = db.Column(db.Text, nullable=True)  # JSON snapshot of payload
    output_data = db.Column(db.Text, nullable=True)  # JSON result
    error_message = db.Column(db.Text, nullable=True)
    error_trace = db.Column(db.Text, nullable=True)

    # Additional context
    log_messages = db.Column(db.Text, nullable=True)  # JSON array of log entries

    # Relationships
    job = db.relationship('BackgroundJob', backref=db.backref('execution_logs', lazy='dynamic'))

    def set_ended(self, success: bool, output: dict = None, error: str = None, trace: str = None):
        """Set the execution end state"""
        self.ended_at = datetime.utcnow()
        self.status = 'completed' if success else 'failed'
        self.success = success

        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

        if output:
            self.output_data = json.dumps(output)
        if error:
            self.error_message = error
        if trace:
            self.error_trace = trace

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'job_id': self.job_id,
            'attempt_number': self.attempt_number,
            'worker_id': self.worker_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_ms': self.duration_ms,
            'status': self.status,
            'success': self.success,
            'error_message': self.error_message
        }


class IdempotencyRecord(db.Model):
    """
    Store idempotency keys for webhooks and critical operations.

    This ensures that webhook replays and duplicate requests are no-ops.
    """
    __tablename__ = 'idempotency_records'

    id = db.Column(db.Integer, primary_key=True)

    # The idempotency key (webhook event ID, request ID, etc.)
    idempotency_key = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # Context
    operation_type = db.Column(db.String(100), nullable=False)  # 'webhook.stripe', 'webhook.paypal', 'billing.charge'
    entity_type = db.Column(db.String(50))  # 'subscription', 'order', 'payment'
    entity_id = db.Column(db.String(100))  # The related entity ID

    # Request details
    request_hash = db.Column(db.String(64))  # SHA256 of request body for verification
    source_ip = db.Column(db.String(45))  # IPv6 compatible

    # Processing status
    status = db.Column(db.String(20), default='processed')  # received, processing, processed, ignored
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Result
    result_data = db.Column(db.Text, nullable=True)  # JSON result

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # When this record can be cleaned up

    # Index for cleanup queries
    __table_args__ = (
        db.Index('ix_idempotency_expires', 'expires_at'),
        db.Index('ix_idempotency_operation', 'operation_type', 'created_at'),
    )

    @classmethod
    def exists(cls, key: str) -> bool:
        """Check if an idempotency key already exists"""
        return cls.query.filter_by(idempotency_key=key).first() is not None

    @classmethod
    def get_or_none(cls, key: str) -> 'IdempotencyRecord':
        """Get existing record or None"""
        return cls.query.filter_by(idempotency_key=key).first()

    @classmethod
    def create_if_not_exists(cls, key: str, operation_type: str, **kwargs) -> tuple:
        """
        Create a new record if it doesn't exist.

        Returns:
            Tuple of (record, created: bool)
        """
        existing = cls.query.filter_by(idempotency_key=key).first()
        if existing:
            return existing, False

        record = cls(
            idempotency_key=key,
            operation_type=operation_type,
            **kwargs
        )
        db.session.add(record)
        return record, True

    def to_dict(self) -> dict:
        result_data = None
        if self.result_data:
            try:
                result_data = json.loads(self.result_data)
            except:
                result_data = self.result_data

        return {
            'id': self.id,
            'idempotency_key': self.idempotency_key,
            'operation_type': self.operation_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'status': self.status,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'result_data': result_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

