"""
Webhook Safety Service - Handles webhook processing with safety guarantees.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import hmac
import hashlib
import json
import logging

from app import db
from app.models.background_job_models import IdempotencyRecord

logger = logging.getLogger(__name__)


class WebhookVerificationError(Exception):
    """Raised when webhook signature verification fails"""
    pass


class WebhookReplayError(Exception):
    """Raised when a webhook replay is detected"""
    pass


class WebhookService:
    """Service for safely processing payment webhooks."""

    MAX_EVENT_AGE_SECONDS = 300
    IDEMPOTENCY_EXPIRY_DAYS = 7

    @staticmethod
    def verify_stripe_signature(payload: bytes, signature: str, webhook_secret: str) -> bool:
        """Verify Stripe webhook signature."""
        if not signature or not webhook_secret:
            raise WebhookVerificationError("Missing signature or webhook secret")

        try:
            elements = {}
            for part in signature.split(','):
                key, value = part.split('=', 1)
                elements[key] = value

            timestamp = elements.get('t')
            expected_sig = elements.get('v1')

            if not timestamp or not expected_sig:
                raise WebhookVerificationError("Invalid signature format")

            event_time = int(timestamp)
            current_time = int(datetime.utcnow().timestamp())

            if abs(current_time - event_time) > WebhookService.MAX_EVENT_AGE_SECONDS:
                raise WebhookVerificationError("Webhook timestamp too old")

            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            computed_sig = hmac.new(
                webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_sig, computed_sig):
                raise WebhookVerificationError("Signature verification failed")

            return True

        except WebhookVerificationError:
            raise
        except Exception as e:
            raise WebhookVerificationError(f"Signature verification error: {str(e)}")

    @staticmethod
    def check_idempotency(event_id: str, operation_type: str, request_body: bytes = None) -> Tuple[bool, Optional[IdempotencyRecord]]:
        """Check if this webhook event has already been processed."""
        idempotency_key = f"{operation_type}:{event_id}"
        existing = IdempotencyRecord.query.filter_by(idempotency_key=idempotency_key).first()
        if existing:
            return True, existing
        return False, None

    @staticmethod
    def record_webhook_processed(event_id: str, operation_type: str, **kwargs) -> IdempotencyRecord:
        """Record that a webhook has been processed."""
        idempotency_key = f"{operation_type}:{event_id}"

        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            operation_type=operation_type,
            entity_type=kwargs.get('entity_type'),
            entity_id=str(kwargs.get('entity_id')) if kwargs.get('entity_id') else None,
            status='processed',
            processed_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=WebhookService.IDEMPOTENCY_EXPIRY_DAYS)
        )

        if kwargs.get('result_data'):
            record.result_data = json.dumps(kwargs.get('result_data'))

        db.session.add(record)
        return record

    @staticmethod
    def process_stripe_webhook(payload: bytes, signature: str) -> Dict[str, Any]:
        """Process a Stripe webhook with full safety guarantees."""
        from app.models.website_content_models import PaymentGateway

        gateway = PaymentGateway.query.filter_by(name='stripe', is_active=True).first()
        if not gateway:
            raise WebhookVerificationError("Stripe gateway not configured")

        webhook_secret = gateway.webhook_secret
        if not webhook_secret:
            raise WebhookVerificationError("Stripe webhook secret not configured")

        WebhookService.verify_stripe_signature(payload, signature, webhook_secret)

        try:
            event_data = json.loads(payload)
        except json.JSONDecodeError:
            raise WebhookVerificationError("Invalid JSON payload")

        event_id = event_data.get('id')
        event_type = event_data.get('type')

        if not event_id:
            raise WebhookVerificationError("Missing event ID")

        is_duplicate, existing = WebhookService.check_idempotency(event_id, 'webhook.stripe', payload)

        if is_duplicate:
            logger.info(f"Duplicate Stripe webhook ignored: {event_id}")
            return {
                'status': 'duplicate',
                'event_id': event_id,
                'original_processed_at': existing.processed_at.isoformat() if existing else None
            }

        result = {'action': 'processed', 'event_type': event_type}

        WebhookService.record_webhook_processed(
            event_id=event_id,
            operation_type='webhook.stripe',
            result_data=result
        )

        db.session.commit()

        return {
            'status': 'processed',
            'event_id': event_id,
            'event_type': event_type,
            'result': result
        }

