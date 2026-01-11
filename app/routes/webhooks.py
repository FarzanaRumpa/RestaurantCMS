"""
Webhook Routes - API endpoints for receiving webhooks from payment providers.
"""

from flask import Blueprint, request, jsonify
import logging

from app import db
from app.services.webhook_service import (
    WebhookService,
    WebhookVerificationError,
    WebhookReplayError
)

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhooks', __name__)


@webhook_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    """Receive and process Stripe webhooks."""
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature')

        if not signature:
            logger.warning("Stripe webhook received without signature")
            return jsonify({'error': 'Missing signature'}), 400

        result = WebhookService.process_stripe_webhook(payload, signature)

        if result.get('status') == 'duplicate':
            return jsonify({
                'status': 'acknowledged',
                'message': 'Duplicate event ignored'
            }), 200

        return jsonify({
            'status': 'processed',
            'event_id': result.get('event_id'),
            'event_type': result.get('event_type')
        }), 200

    except WebhookVerificationError as e:
        logger.warning(f"Stripe webhook verification failed: {e}")
        return jsonify({'error': str(e)}), 400

    except WebhookReplayError as e:
        logger.warning(f"Stripe webhook replay detected: {e}")
        return jsonify({
            'status': 'acknowledged',
            'message': 'Replay ignored'
        }), 200

    except Exception as e:
        logger.error(f"Stripe webhook processing error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal processing error'}), 500


@webhook_bp.route('/paypal', methods=['POST'])
def paypal_webhook():
    """Receive and process PayPal webhooks."""
    try:
        payload = request.get_data()

        # For now, acknowledge all PayPal webhooks
        # Full implementation would verify signature and process
        import json
        try:
            event_data = json.loads(payload)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON'}), 400

        event_id = event_data.get('id')
        event_type = event_data.get('event_type')

        logger.info(f"PayPal webhook received: {event_type} ({event_id})")

        return jsonify({
            'status': 'acknowledged',
            'event_id': event_id
        }), 200

    except Exception as e:
        logger.error(f"PayPal webhook processing error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal processing error'}), 500

