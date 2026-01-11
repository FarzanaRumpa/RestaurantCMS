"""
Phase 3 Database Migration - Enterprise Features
=================================================
This migration adds tables for:
1. White-Label & Custom Domains
2. Feature Flags
3. Audit Logs
4. Data Export Requests
5. Data Deletion Requests

Revision ID: phase3_enterprise_features
Revises: phase2_production_features
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers
revision = 'phase3_enterprise_features'
down_revision = 'phase2_production_features'
branch_labels = None
depends_on = None


def upgrade():
    # =====================================================
    # 1. Custom Domains Table
    # =====================================================
    op.create_table('custom_domains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('subdomain', sa.String(100), nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verification_token', sa.String(100), nullable=True),
        sa.Column('verification_method', sa.String(20), default='dns'),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('ssl_enabled', sa.Boolean(), default=False),
        sa.Column('ssl_issued_at', sa.DateTime(), nullable=True),
        sa.Column('ssl_expires_at', sa.DateTime(), nullable=True),
        sa.Column('ssl_provider', sa.String(50), default='letsencrypt'),
        sa.Column('ssl_auto_renew', sa.Boolean(), default=True),
        sa.Column('ssl_last_renewal_attempt', sa.DateTime(), nullable=True),
        sa.Column('ssl_renewal_error', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.UniqueConstraint('restaurant_id'),
        sa.UniqueConstraint('domain')
    )
    op.create_index('ix_custom_domain', 'custom_domains', ['domain'])
    op.create_index('ix_custom_domain_active', 'custom_domains', ['is_active'])

    # =====================================================
    # 2. White-Label Branding Table
    # =====================================================
    op.create_table('white_label_branding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=False),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('logo_dark_url', sa.String(500), nullable=True),
        sa.Column('favicon_url', sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(7), default='#6366f1'),
        sa.Column('secondary_color', sa.String(7), default='#1a1a2e'),
        sa.Column('accent_color', sa.String(7), nullable=True),
        sa.Column('heading_font', sa.String(100), nullable=True),
        sa.Column('body_font', sa.String(100), nullable=True),
        sa.Column('company_name', sa.String(200), nullable=True),
        sa.Column('tagline', sa.String(500), nullable=True),
        sa.Column('footer_text', sa.Text(), nullable=True),
        sa.Column('copyright_text', sa.String(500), nullable=True),
        sa.Column('support_email', sa.String(120), nullable=True),
        sa.Column('support_phone', sa.String(20), nullable=True),
        sa.Column('support_url', sa.String(500), nullable=True),
        sa.Column('privacy_policy_url', sa.String(500), nullable=True),
        sa.Column('terms_of_service_url', sa.String(500), nullable=True),
        sa.Column('hide_powered_by', sa.Boolean(), default=False),
        sa.Column('hide_saas_logo', sa.Boolean(), default=False),
        sa.Column('hide_saas_links', sa.Boolean(), default=False),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('custom_head_html', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.UniqueConstraint('restaurant_id')
    )

    # =====================================================
    # 3. Feature Flags Table
    # =====================================================
    op.create_table('feature_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('flag_type', sa.String(20), default='boolean'),
        sa.Column('is_enabled', sa.Boolean(), default=False),
        sa.Column('percentage', sa.Integer(), default=0),
        sa.Column('enabled_restaurants', sa.Text(), nullable=True),
        sa.Column('disabled_restaurants', sa.Text(), nullable=True),
        sa.Column('activate_at', sa.DateTime(), nullable=True),
        sa.Column('deactivate_at', sa.DateTime(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('created_by_id', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_feature_flag_name', 'feature_flags', ['name'])

    # =====================================================
    # 4. Audit Logs Table
    # =====================================================
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), default='info'),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_type', sa.String(20), default='user'),
        sa.Column('actor_ip', sa.String(45), nullable=True),
        sa.Column('actor_user_agent', sa.Text(), nullable=True),
        sa.Column('target_type', sa.String(50), nullable=True),
        sa.Column('target_id', sa.String(100), nullable=True),
        sa.Column('restaurant_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(50), nullable=True),
        sa.Column('request_path', sa.String(255), nullable=True),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.UniqueConstraint('log_id')
    )
    op.create_index('ix_audit_category', 'audit_logs', ['category'])
    op.create_index('ix_audit_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_created', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_actor_date', 'audit_logs', ['actor_id', 'created_at'])
    op.create_index('ix_audit_category_action', 'audit_logs', ['category', 'action'])
    op.create_index('ix_audit_target', 'audit_logs', ['target_type', 'target_id'])
    op.create_index('ix_audit_restaurant', 'audit_logs', ['restaurant_id'])

    # =====================================================
    # 5. Data Export Requests Table
    # =====================================================
    op.create_table('data_export_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('export_id', sa.String(50), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('requested_by_id', sa.Integer(), nullable=False),
        sa.Column('export_type', sa.String(50), default='full'),
        sa.Column('date_from', sa.DateTime(), nullable=True),
        sa.Column('date_to', sa.DateTime(), nullable=True),
        sa.Column('format', sa.String(20), default='json'),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('download_url', sa.String(500), nullable=True),
        sa.Column('download_token', sa.String(100), nullable=True),
        sa.Column('download_expires_at', sa.DateTime(), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.ForeignKeyConstraint(['requested_by_id'], ['users.id']),
        sa.UniqueConstraint('export_id')
    )
    op.create_index('ix_export_restaurant', 'data_export_requests', ['restaurant_id'])

    # =====================================================
    # 6. Data Deletion Requests Table
    # =====================================================
    op.create_table('data_deletion_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deletion_id', sa.String(50), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('requested_by_id', sa.Integer(), nullable=False),
        sa.Column('deletion_type', sa.String(50), default='account'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('requires_approval', sa.Boolean(), default=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('soft_delete_at', sa.DateTime(), nullable=True),
        sa.Column('hard_delete_scheduled', sa.DateTime(), nullable=True),
        sa.Column('hard_delete_at', sa.DateTime(), nullable=True),
        sa.Column('confirmation_token', sa.String(100), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.ForeignKeyConstraint(['requested_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id']),
        sa.UniqueConstraint('deletion_id')
    )
    op.create_index('ix_deletion_restaurant', 'data_deletion_requests', ['restaurant_id'])

    # =====================================================
    # 7. Add indexes for performance optimization
    # =====================================================
    # Orders table indexes for dashboard queries
    try:
        op.create_index('ix_orders_created_at', 'orders', ['created_at'])
        op.create_index('ix_orders_payment_status', 'orders', ['payment_status'])
        op.create_index('ix_orders_restaurant_created', 'orders', ['restaurant_id', 'created_at'])
    except Exception:
        pass  # Index may already exist

    # Subscriptions table indexes
    try:
        op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
        op.create_index('ix_subscriptions_next_billing', 'subscriptions', ['next_billing_date'])
    except Exception:
        pass

    # Menu items index for availability queries
    try:
        op.create_index('ix_menu_items_available', 'menu_items', ['is_available'])
    except Exception:
        pass


def downgrade():
    # Drop indexes
    try:
        op.drop_index('ix_orders_created_at', 'orders')
        op.drop_index('ix_orders_payment_status', 'orders')
        op.drop_index('ix_orders_restaurant_created', 'orders')
        op.drop_index('ix_subscriptions_status', 'subscriptions')
        op.drop_index('ix_subscriptions_next_billing', 'subscriptions')
        op.drop_index('ix_menu_items_available', 'menu_items')
    except Exception:
        pass

    # Drop tables
    op.drop_table('data_deletion_requests')
    op.drop_table('data_export_requests')
    op.drop_table('audit_logs')
    op.drop_table('feature_flags')
    op.drop_table('white_label_branding')
    op.drop_table('custom_domains')

