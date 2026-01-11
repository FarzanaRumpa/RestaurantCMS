"""
Phase 2 Database Migration - Production-Grade Features
=======================================================
This migration adds tables for:
1. Restaurant Onboarding
2. Feature Visibility
3. Background Jobs
4. Job Execution Logs
5. Idempotency Records (for webhooks)
6. Tax Rules
7. Order Tax Snapshots

Run with: flask db upgrade
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers
revision = 'phase2_production_features'
down_revision = 'dual_order_number_system'  # Previous migration
branch_labels = None
depends_on = None


def upgrade():
    # =====================================================
    # 1. Restaurant Onboarding Table
    # =====================================================
    op.create_table('restaurant_onboarding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('is_complete', sa.Boolean(), default=False),
        sa.Column('started_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('completed_at', sa.DateTime(), nullable=True),

        # Individual step completion flags
        sa.Column('profile_completed', sa.Boolean(), default=False),
        sa.Column('profile_completed_at', sa.DateTime(), nullable=True),
        sa.Column('category_created', sa.Boolean(), default=False),
        sa.Column('category_created_at', sa.DateTime(), nullable=True),
        sa.Column('menu_item_created', sa.Boolean(), default=False),
        sa.Column('menu_item_created_at', sa.DateTime(), nullable=True),
        sa.Column('table_added', sa.Boolean(), default=False),
        sa.Column('table_added_at', sa.DateTime(), nullable=True),
        sa.Column('qr_code_generated', sa.Boolean(), default=False),
        sa.Column('qr_code_generated_at', sa.DateTime(), nullable=True),
        sa.Column('test_order_completed', sa.Boolean(), default=False),
        sa.Column('test_order_completed_at', sa.DateTime(), nullable=True),

        sa.Column('current_step', sa.String(50), default='profile_completed'),
        sa.Column('skipped', sa.Boolean(), default=False),
        sa.Column('skipped_at', sa.DateTime(), nullable=True),
        sa.Column('skipped_by_id', sa.Integer(), nullable=True),
        sa.Column('skip_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.ForeignKeyConstraint(['skipped_by_id'], ['users.id']),
        sa.UniqueConstraint('restaurant_id')
    )
    op.create_index('ix_onboarding_complete', 'restaurant_onboarding', ['is_complete'])

    # =====================================================
    # 2. Feature Visibility Table
    # =====================================================
    op.create_table('feature_visibility',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('feature_name', sa.String(50), nullable=False),
        sa.Column('is_visible', sa.Boolean(), default=False),
        sa.Column('is_locked', sa.Boolean(), default=True),
        sa.Column('lock_reason', sa.String(100), nullable=True),
        sa.Column('unlock_condition', sa.String(50), nullable=True),
        sa.Column('unlock_threshold', sa.Integer(), nullable=True),
        sa.Column('admin_override', sa.Boolean(), default=False),
        sa.Column('override_by_id', sa.Integer(), nullable=True),
        sa.Column('override_at', sa.DateTime(), nullable=True),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.ForeignKeyConstraint(['override_by_id'], ['users.id']),
        sa.UniqueConstraint('restaurant_id', 'feature_name', name='uq_restaurant_feature')
    )

    # =====================================================
    # 3. Background Jobs Table
    # =====================================================
    op.create_table('background_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(50), nullable=False, unique=True),
        sa.Column('idempotency_key', sa.String(255), nullable=True, unique=True),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('job_name', sa.String(255), nullable=True),
        sa.Column('restaurant_id', sa.Integer(), nullable=True),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('priority', sa.Integer(), default=5),
        sa.Column('max_retries', sa.Integer(), default=3),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('retry_delay_seconds', sa.Integer(), default=300),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_trace', sa.Text(), nullable=True),
        sa.Column('locked_by', sa.String(100), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('lock_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'])
    )
    op.create_index('ix_job_status_scheduled', 'background_jobs', ['status', 'scheduled_at'])
    op.create_index('ix_job_type_status', 'background_jobs', ['job_type', 'status'])
    op.create_index('ix_job_restaurant_status', 'background_jobs', ['restaurant_id', 'status'])
    op.create_index('ix_job_idempotency', 'background_jobs', ['idempotency_key'])

    # =====================================================
    # 4. Job Execution Logs Table
    # =====================================================
    op.create_table('job_execution_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), default=1),
        sa.Column('worker_id', sa.String(100), nullable=True),
        sa.Column('worker_host', sa.String(255), nullable=True),
        sa.Column('started_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('output_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_trace', sa.Text(), nullable=True),
        sa.Column('log_messages', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['background_jobs.id'])
    )
    op.create_index('ix_job_log_job_id', 'job_execution_logs', ['job_id'])

    # =====================================================
    # 5. Idempotency Records Table
    # =====================================================
    op.create_table('idempotency_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('idempotency_key', sa.String(255), nullable=False, unique=True),
        sa.Column('operation_type', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.String(100), nullable=True),
        sa.Column('request_hash', sa.String(64), nullable=True),
        sa.Column('source_ip', sa.String(45), nullable=True),
        sa.Column('status', sa.String(20), default='processed'),
        sa.Column('processed_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('result_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('expires_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_idempotency_key', 'idempotency_records', ['idempotency_key'])
    op.create_index('ix_idempotency_expires', 'idempotency_records', ['expires_at'])
    op.create_index('ix_idempotency_operation', 'idempotency_records', ['operation_type', 'created_at'])

    # =====================================================
    # 6. Tax Rules Table
    # =====================================================
    op.create_table('tax_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('is_inclusive', sa.Boolean(), default=False),
        sa.Column('is_compound', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('apply_to_all_items', sa.Boolean(), default=True),
        sa.Column('apply_to_categories', sa.Text(), nullable=True),
        sa.Column('min_order_amount', sa.Float(), default=0),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('show_on_invoice', sa.Boolean(), default=True),
        sa.Column('registration_number', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.UniqueConstraint('restaurant_id', 'code', name='uq_restaurant_tax_code')
    )
    op.create_index('ix_tax_rules_restaurant', 'tax_rules', ['restaurant_id'])
    op.create_index('ix_tax_rules_active', 'tax_rules', ['is_active'])

    # =====================================================
    # 7. Order Tax Snapshots Table
    # =====================================================
    op.create_table('order_tax_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('tax_name', sa.String(100), nullable=False),
        sa.Column('tax_code', sa.String(20), nullable=True),
        sa.Column('tax_rate', sa.Float(), nullable=False),
        sa.Column('is_inclusive', sa.Boolean(), default=False),
        sa.Column('taxable_amount', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Float(), nullable=False),
        sa.Column('tax_rule_id', sa.Integer(), nullable=True),
        sa.Column('registration_number', sa.String(100), nullable=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['tax_rule_id'], ['tax_rules.id'])
    )
    op.create_index('ix_order_tax_order', 'order_tax_snapshots', ['order_id'])


def downgrade():
    op.drop_table('order_tax_snapshots')
    op.drop_table('tax_rules')
    op.drop_table('idempotency_records')
    op.drop_table('job_execution_logs')
    op.drop_table('background_jobs')
    op.drop_table('feature_visibility')
    op.drop_table('restaurant_onboarding')

