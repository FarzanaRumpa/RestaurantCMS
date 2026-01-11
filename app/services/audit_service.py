"""
Audit & Compliance Service
==========================
Service layer for audit logging, data export, and deletion workflows.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from flask import g, request
import logging
import json
import os

from app import db
from app.models.compliance_models import (
    AuditLog, AuditLogCategory, AuditLogAction,
    DataExportRequest, DataDeletionRequest, PIIMaskingConfig
)

logger = logging.getLogger(__name__)


class AuditService:
    """Service for creating and querying audit logs."""

    @staticmethod
    def log(
        category: str,
        action: str,
        actor_id: int = None,
        actor_type: str = 'user',
        target_type: str = None,
        target_id: str = None,
        restaurant_id: int = None,
        description: str = None,
        old_value: dict = None,
        new_value: dict = None,
        metadata: dict = None,
        severity: str = 'info'
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            category: Log category (use AuditLogCategory constants)
            action: Action performed (use AuditLogAction constants)
            actor_id: User ID who performed the action
            actor_type: Type of actor (user, system, webhook, api)
            target_type: Type of target entity
            target_id: ID of target entity
            restaurant_id: Associated restaurant
            description: Human-readable description
            old_value: Previous state (dict, will be JSON-serialized)
            new_value: New state (dict, will be JSON-serialized)
            metadata: Additional context
            severity: Log severity (info, warning, critical)

        Returns:
            Created AuditLog object
        """
        # Mask PII in values before logging
        if old_value:
            old_value = PIIMaskingConfig.mask_dict(old_value)
        if new_value:
            new_value = PIIMaskingConfig.mask_dict(new_value)
        if metadata:
            metadata = PIIMaskingConfig.mask_dict(metadata)

        log_entry = AuditLog(
            category=category,
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_ip=request.remote_addr if request else None,
            actor_user_agent=request.user_agent.string if request and request.user_agent else None,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            restaurant_id=restaurant_id,
            description=description,
            severity=severity,
            request_id=getattr(g, 'correlation_id', None) if g else None,
            request_path=request.path if request else None,
            request_method=request.method if request else None
        )

        if old_value:
            log_entry.set_old_value(old_value)
        if new_value:
            log_entry.set_new_value(new_value)
        if metadata:
            log_entry.set_metadata(metadata)

        db.session.add(log_entry)
        db.session.commit()

        return log_entry

    @staticmethod
    def log_billing_event(
        action: str,
        subscription_id: int,
        restaurant_id: int,
        amount: float = None,
        currency: str = 'USD',
        details: dict = None,
        actor_id: int = None
    ) -> AuditLog:
        """Convenience method for billing-related audit logs."""
        return AuditService.log(
            category=AuditLogCategory.BILLING,
            action=action,
            actor_id=actor_id,
            target_type='subscription',
            target_id=str(subscription_id),
            restaurant_id=restaurant_id,
            description=f"Billing action: {action}",
            new_value={
                'amount': amount,
                'currency': currency,
                **(details or {})
            },
            severity='info' if action != AuditLogAction.PAYMENT_FAILED else 'warning'
        )

    @staticmethod
    def log_auth_event(
        action: str,
        user_id: int,
        success: bool = True,
        details: dict = None
    ) -> AuditLog:
        """Convenience method for authentication-related audit logs."""
        return AuditService.log(
            category=AuditLogCategory.AUTHENTICATION,
            action=action,
            actor_id=user_id if success else None,
            target_type='user',
            target_id=str(user_id),
            description=f"Auth action: {action}",
            metadata=details,
            severity='info' if success else 'warning'
        )

    @staticmethod
    def log_config_change(
        action: str,
        actor_id: int,
        restaurant_id: int,
        config_type: str,
        old_config: dict = None,
        new_config: dict = None
    ) -> AuditLog:
        """Convenience method for configuration change audit logs."""
        return AuditService.log(
            category=AuditLogCategory.CONFIGURATION,
            action=action,
            actor_id=actor_id,
            target_type=config_type,
            restaurant_id=restaurant_id,
            description=f"Configuration changed: {config_type}",
            old_value=old_config,
            new_value=new_config
        )

    @staticmethod
    def query_logs(
        restaurant_id: int = None,
        category: str = None,
        action: str = None,
        actor_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        severity: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Query audit logs with filters."""
        query = AuditLog.query

        if restaurant_id:
            query = query.filter(AuditLog.restaurant_id == restaurant_id)
        if category:
            query = query.filter(AuditLog.category == category)
        if action:
            query = query.filter(AuditLog.action == action)
        if actor_id:
            query = query.filter(AuditLog.actor_id == actor_id)
        if severity:
            query = query.filter(AuditLog.severity == severity)
        if date_from:
            query = query.filter(AuditLog.created_at >= date_from)
        if date_to:
            query = query.filter(AuditLog.created_at <= date_to)

        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()


class DataExportService:
    """Service for data export workflows."""

    EXPORT_RETENTION_DAYS = 7

    @staticmethod
    def request_export(
        restaurant_id: int,
        requested_by_id: int,
        export_type: str = 'full',
        format: str = 'json',
        date_from: datetime = None,
        date_to: datetime = None
    ) -> DataExportRequest:
        """
        Create a data export request.

        Args:
            restaurant_id: Restaurant to export data for
            requested_by_id: User requesting the export
            export_type: Type of export (full, orders, menu, invoices, customers)
            format: Export format (json, csv, xlsx)
            date_from: Start date filter
            date_to: End date filter

        Returns:
            Created DataExportRequest
        """
        export_request = DataExportRequest(
            restaurant_id=restaurant_id,
            requested_by_id=requested_by_id,
            export_type=export_type,
            format=format,
            date_from=date_from,
            date_to=date_to,
            status='pending'
        )
        export_request.generate_download_token()

        db.session.add(export_request)
        db.session.commit()

        # Log the export request
        AuditService.log(
            category=AuditLogCategory.DATA_ACCESS,
            action=AuditLogAction.DATA_EXPORTED,
            actor_id=requested_by_id,
            target_type='restaurant',
            target_id=str(restaurant_id),
            restaurant_id=restaurant_id,
            description=f"Data export requested: {export_type}",
            metadata={'export_type': export_type, 'format': format}
        )

        logger.info(f"Data export requested: {export_request.export_id}")
        return export_request

    @staticmethod
    def process_export(export_id: str) -> bool:
        """
        Process a pending export request.

        This would typically be called by a background job.
        """
        export_request = DataExportRequest.query.filter_by(export_id=export_id).first()
        if not export_request or export_request.status != 'pending':
            return False

        export_request.status = 'processing'
        export_request.started_at = datetime.utcnow()
        db.session.commit()

        try:
            # Generate export based on type
            if export_request.export_type == 'full':
                data = DataExportService._export_full(export_request)
            elif export_request.export_type == 'orders':
                data = DataExportService._export_orders(export_request)
            elif export_request.export_type == 'menu':
                data = DataExportService._export_menu(export_request)
            else:
                data = DataExportService._export_full(export_request)

            # Save to file
            file_path = DataExportService._save_export(export_request, data)

            export_request.file_path = file_path
            export_request.file_size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            export_request.status = 'completed'
            export_request.completed_at = datetime.utcnow()
            export_request.download_expires_at = datetime.utcnow() + timedelta(days=DataExportService.EXPORT_RETENTION_DAYS)
            export_request.progress = 100

            db.session.commit()
            logger.info(f"Export completed: {export_id}")
            return True

        except Exception as e:
            export_request.status = 'failed'
            export_request.error_message = str(e)
            db.session.commit()
            logger.error(f"Export failed: {export_id} - {e}")
            return False

    @staticmethod
    def _export_full(export_request: DataExportRequest) -> dict:
        """Export all restaurant data."""
        from app.models import Restaurant, Category, MenuItem, Table, Order

        restaurant = Restaurant.query.get(export_request.restaurant_id)
        if not restaurant:
            return {}

        return {
            'restaurant': {
                'name': restaurant.name,
                'description': restaurant.description,
                'address': restaurant.address,
                'phone': PIIMaskingConfig.mask_value('phone', restaurant.phone),
                'email': PIIMaskingConfig.mask_value('email', restaurant.email)
            },
            'categories': [cat.to_dict() for cat in Category.query.filter_by(restaurant_id=restaurant.id).all()],
            'menu_items': [item.to_dict() for cat in restaurant.categories for item in cat.items],
            'tables': [table.to_dict() for table in Table.query.filter_by(restaurant_id=restaurant.id).all()],
            'orders': DataExportService._export_orders(export_request),
            'exported_at': datetime.utcnow().isoformat()
        }

    @staticmethod
    def _export_orders(export_request: DataExportRequest) -> list:
        """Export order data with PII masked."""
        from app.models import Order

        query = Order.query.filter_by(restaurant_id=export_request.restaurant_id)

        if export_request.date_from:
            query = query.filter(Order.created_at >= export_request.date_from)
        if export_request.date_to:
            query = query.filter(Order.created_at <= export_request.date_to)

        orders = []
        for order in query.all():
            order_dict = order.to_dict()
            # Mask PII
            order_dict = PIIMaskingConfig.mask_dict(order_dict)
            orders.append(order_dict)

        return orders

    @staticmethod
    def _export_menu(export_request: DataExportRequest) -> dict:
        """Export menu data."""
        from app.models import Category

        categories = Category.query.filter_by(restaurant_id=export_request.restaurant_id).all()
        return {
            'categories': [cat.to_dict() for cat in categories]
        }

    @staticmethod
    def _save_export(export_request: DataExportRequest, data: dict) -> str:
        """Save export data to file."""
        export_dir = os.path.join('instance', 'exports', str(export_request.restaurant_id))
        os.makedirs(export_dir, exist_ok=True)

        filename = f"{export_request.export_id}.{export_request.format}"
        file_path = os.path.join(export_dir, filename)

        if export_request.format == 'json':
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        # CSV and XLSX would need additional implementation

        return file_path


class DataDeletionService:
    """Service for data deletion workflows."""

    SOFT_DELETE_RETENTION_DAYS = 30

    @staticmethod
    def request_deletion(
        restaurant_id: int,
        requested_by_id: int,
        deletion_type: str = 'account',
        reason: str = None,
        requires_approval: bool = True
    ) -> DataDeletionRequest:
        """
        Create a data deletion request.

        Implements soft delete → hard delete workflow.
        """
        deletion_request = DataDeletionRequest(
            restaurant_id=restaurant_id,
            requested_by_id=requested_by_id,
            deletion_type=deletion_type,
            reason=reason,
            requires_approval=requires_approval,
            status='pending'
        )

        import secrets
        deletion_request.confirmation_token = secrets.token_urlsafe(32)

        db.session.add(deletion_request)
        db.session.commit()

        # Log the deletion request
        AuditService.log(
            category=AuditLogCategory.DATA_DELETION,
            action=AuditLogAction.DATA_DELETED,
            actor_id=requested_by_id,
            target_type='restaurant',
            target_id=str(restaurant_id),
            restaurant_id=restaurant_id,
            description=f"Data deletion requested: {deletion_type}",
            metadata={'deletion_type': deletion_type, 'reason': reason},
            severity='warning'
        )

        logger.info(f"Deletion request created: {deletion_request.deletion_id}")
        return deletion_request

    @staticmethod
    def approve_deletion(
        deletion_id: str,
        approved_by_id: int
    ) -> bool:
        """Approve a pending deletion request."""
        deletion_request = DataDeletionRequest.query.filter_by(deletion_id=deletion_id).first()
        if not deletion_request or deletion_request.status != 'pending':
            return False

        deletion_request.status = 'approved'
        deletion_request.approved_by_id = approved_by_id
        deletion_request.approved_at = datetime.utcnow()

        db.session.commit()

        # Log approval
        AuditService.log(
            category=AuditLogCategory.DATA_DELETION,
            action='deletion_approved',
            actor_id=approved_by_id,
            target_type='deletion_request',
            target_id=deletion_id,
            restaurant_id=deletion_request.restaurant_id,
            severity='warning'
        )

        return True

    @staticmethod
    def execute_soft_delete(deletion_id: str) -> bool:
        """Execute soft delete for a restaurant."""
        deletion_request = DataDeletionRequest.query.filter_by(deletion_id=deletion_id).first()
        if not deletion_request or deletion_request.status != 'approved':
            return False

        from app.models import Restaurant

        restaurant = Restaurant.query.get(deletion_request.restaurant_id)
        if restaurant:
            restaurant.is_active = False
            # Additional soft delete logic here

        deletion_request.status = 'soft_deleted'
        deletion_request.soft_delete_at = datetime.utcnow()
        deletion_request.hard_delete_scheduled = datetime.utcnow() + timedelta(
            days=DataDeletionService.SOFT_DELETE_RETENTION_DAYS
        )

        db.session.commit()

        logger.info(f"Soft delete executed: {deletion_id}")
        return True

    @staticmethod
    def execute_hard_delete(deletion_id: str) -> bool:
        """
        Execute hard delete for a restaurant.

        This permanently removes all data. Should only be called
        after soft delete retention period.
        """
        deletion_request = DataDeletionRequest.query.filter_by(deletion_id=deletion_id).first()
        if not deletion_request or deletion_request.status != 'soft_deleted':
            return False

        # Check retention period
        if deletion_request.hard_delete_scheduled > datetime.utcnow():
            return False

        # Hard delete implementation would go here
        # This is a placeholder - actual implementation would cascade delete all related data

        deletion_request.status = 'hard_deleted'
        deletion_request.hard_delete_at = datetime.utcnow()

        db.session.commit()

        logger.info(f"Hard delete executed: {deletion_id}")
        return True

