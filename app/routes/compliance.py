"""
Compliance Routes
=================
API endpoints for data export, deletion, and audit logs.
GDPR and compliance-related operations.
"""

from flask import Blueprint, request, jsonify, g, session, send_file
from functools import wraps
from datetime import datetime
import logging
import os

from app import db
from app.services.audit_service import AuditService, DataExportService, DataDeletionService
from app.api.versioning import api_response, ValidationError, NotFoundError, AuthorizationError, PaginatedResponse
from app.models.compliance_models import AuditLog, DataExportRequest, DataDeletionRequest

logger = logging.getLogger(__name__)

compliance_bp = Blueprint('compliance', __name__, url_prefix='/owner/api/compliance')


def owner_required(f):
    """Require authenticated restaurant owner"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'owner_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        from app.models import Restaurant
        restaurant = Restaurant.query.filter_by(owner_id=session['owner_id']).first()
        if not restaurant:
            return jsonify({'error': 'No restaurant found'}), 404

        g.restaurant_id = restaurant.id
        g.restaurant = restaurant
        g.owner_id = session['owner_id']
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# DATA EXPORT ENDPOINTS
# =============================================================================

@compliance_bp.route('/export', methods=['POST'])
@owner_required
def request_export():
    """Request a data export"""
    data = request.get_json() or {}

    export_type = data.get('export_type', 'full')
    format = data.get('format', 'json')

    if export_type not in ['full', 'orders', 'menu', 'invoices', 'customers']:
        raise ValidationError("Invalid export type", field='export_type')

    if format not in ['json', 'csv', 'xlsx']:
        raise ValidationError("Invalid format", field='format')

    # Parse date filters
    date_from = None
    date_to = None
    if data.get('date_from'):
        try:
            date_from = datetime.fromisoformat(data['date_from'])
        except ValueError:
            raise ValidationError("Invalid date format", field='date_from')

    if data.get('date_to'):
        try:
            date_to = datetime.fromisoformat(data['date_to'])
        except ValueError:
            raise ValidationError("Invalid date format", field='date_to')

    export_request = DataExportService.request_export(
        restaurant_id=g.restaurant_id,
        requested_by_id=g.owner_id,
        export_type=export_type,
        format=format,
        date_from=date_from,
        date_to=date_to
    )

    return api_response(
        data=export_request.to_dict(),
        message="Export request created. You will be notified when ready.",
        status_code=201
    )


@compliance_bp.route('/export', methods=['GET'])
@owner_required
def list_exports():
    """List export requests"""
    page, per_page = PaginatedResponse.get_pagination_params()

    query = DataExportRequest.query.filter_by(
        restaurant_id=g.restaurant_id
    ).order_by(DataExportRequest.created_at.desc())

    result = PaginatedResponse.paginate(query, page, per_page)
    return api_response(data=result['data'], meta={'pagination': result['pagination']})


@compliance_bp.route('/export/<export_id>', methods=['GET'])
@owner_required
def get_export_status(export_id):
    """Get export request status"""
    export_request = DataExportRequest.query.filter_by(
        export_id=export_id,
        restaurant_id=g.restaurant_id
    ).first()

    if not export_request:
        raise NotFoundError("Export request", export_id)

    return api_response(data=export_request.to_dict())


@compliance_bp.route('/export/<export_id>/download', methods=['GET'])
@owner_required
def download_export(export_id):
    """Download completed export"""
    export_request = DataExportRequest.query.filter_by(
        export_id=export_id,
        restaurant_id=g.restaurant_id
    ).first()

    if not export_request:
        raise NotFoundError("Export request", export_id)

    if export_request.status != 'completed':
        raise ValidationError("Export not ready for download")

    if export_request.download_expires_at and export_request.download_expires_at < datetime.utcnow():
        raise ValidationError("Download link has expired")

    if not export_request.file_path or not os.path.exists(export_request.file_path):
        raise NotFoundError("Export file")

    export_request.downloaded_at = datetime.utcnow()
    db.session.commit()

    return send_file(
        export_request.file_path,
        as_attachment=True,
        download_name=f"export_{export_id}.{export_request.format}"
    )


# =============================================================================
# DATA DELETION ENDPOINTS
# =============================================================================

@compliance_bp.route('/deletion', methods=['POST'])
@owner_required
def request_deletion():
    """Request account/data deletion (GDPR right to be forgotten)"""
    data = request.get_json() or {}

    deletion_type = data.get('deletion_type', 'account')
    reason = data.get('reason')

    if deletion_type not in ['account', 'orders', 'customers', 'full']:
        raise ValidationError("Invalid deletion type", field='deletion_type')

    deletion_request = DataDeletionService.request_deletion(
        restaurant_id=g.restaurant_id,
        requested_by_id=g.owner_id,
        deletion_type=deletion_type,
        reason=reason
    )

    return api_response(
        data=deletion_request.to_dict(),
        message="Deletion request created. You will receive a confirmation email.",
        status_code=201
    )


@compliance_bp.route('/deletion', methods=['GET'])
@owner_required
def list_deletion_requests():
    """List deletion requests"""
    page, per_page = PaginatedResponse.get_pagination_params()

    query = DataDeletionRequest.query.filter_by(
        restaurant_id=g.restaurant_id
    ).order_by(DataDeletionRequest.created_at.desc())

    result = PaginatedResponse.paginate(query, page, per_page)
    return api_response(data=result['data'], meta={'pagination': result['pagination']})


@compliance_bp.route('/deletion/<deletion_id>', methods=['GET'])
@owner_required
def get_deletion_status(deletion_id):
    """Get deletion request status"""
    deletion_request = DataDeletionRequest.query.filter_by(
        deletion_id=deletion_id,
        restaurant_id=g.restaurant_id
    ).first()

    if not deletion_request:
        raise NotFoundError("Deletion request", deletion_id)

    return api_response(data=deletion_request.to_dict())


@compliance_bp.route('/deletion/<deletion_id>/cancel', methods=['POST'])
@owner_required
def cancel_deletion(deletion_id):
    """Cancel a pending deletion request"""
    deletion_request = DataDeletionRequest.query.filter_by(
        deletion_id=deletion_id,
        restaurant_id=g.restaurant_id
    ).first()

    if not deletion_request:
        raise NotFoundError("Deletion request", deletion_id)

    if deletion_request.status not in ['pending', 'approved']:
        raise ValidationError("Cannot cancel deletion in current status")

    deletion_request.status = 'cancelled'
    db.session.commit()

    return api_response(message="Deletion request cancelled")


# =============================================================================
# AUDIT LOG ENDPOINTS
# =============================================================================

@compliance_bp.route('/audit-logs', methods=['GET'])
@owner_required
def list_audit_logs():
    """List audit logs for restaurant"""
    page, per_page = PaginatedResponse.get_pagination_params()

    query = AuditLog.query.filter_by(
        restaurant_id=g.restaurant_id
    )

    # Apply filters
    category = request.args.get('category')
    if category:
        query = query.filter(AuditLog.category == category)

    action = request.args.get('action')
    if action:
        query = query.filter(AuditLog.action == action)

    severity = request.args.get('severity')
    if severity:
        query = query.filter(AuditLog.severity == severity)

    date_from = request.args.get('date_from')
    if date_from:
        try:
            query = query.filter(AuditLog.created_at >= datetime.fromisoformat(date_from))
        except ValueError:
            pass

    date_to = request.args.get('date_to')
    if date_to:
        try:
            query = query.filter(AuditLog.created_at <= datetime.fromisoformat(date_to))
        except ValueError:
            pass

    query = query.order_by(AuditLog.created_at.desc())

    result = PaginatedResponse.paginate(query, page, per_page)
    return api_response(data=result['data'], meta={'pagination': result['pagination']})


@compliance_bp.route('/audit-logs/<log_id>', methods=['GET'])
@owner_required
def get_audit_log(log_id):
    """Get audit log details"""
    log = AuditLog.query.filter_by(
        log_id=log_id,
        restaurant_id=g.restaurant_id
    ).first()

    if not log:
        raise NotFoundError("Audit log", log_id)

    return api_response(data={
        **log.to_dict(),
        'old_value': log.get_old_value(),
        'new_value': log.get_new_value()
    })


# =============================================================================
# PRIVACY SETTINGS
# =============================================================================

@compliance_bp.route('/privacy-settings', methods=['GET'])
@owner_required
def get_privacy_settings():
    """Get privacy and data retention settings"""
    # Return current settings
    return api_response(data={
        'data_retention_days': 365,
        'auto_delete_old_orders': False,
        'mask_customer_pii': True,
        'export_format_options': ['json', 'csv', 'xlsx'],
        'deletion_retention_days': 30
    })


@compliance_bp.route('/privacy-settings', methods=['PUT'])
@owner_required
def update_privacy_settings():
    """Update privacy settings"""
    data = request.get_json() or {}

    # Placeholder for privacy settings update
    # This would update restaurant-specific privacy preferences

    return api_response(message="Privacy settings updated")

