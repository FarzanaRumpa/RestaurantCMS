"""Add dual order number system

This migration adds:
1. DisplayOrderSlot table for managing 4-digit display numbers
2. internal_order_id field to Order (UUID, globally unique)
3. display_order_number field to Order (4-digit integer, restaurant-scoped)

Revision ID: dual_order_number_system
Revises:
Create Date: 2026-01-11
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid


# revision identifiers, used by Alembic.
revision = 'dual_order_number_system'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create display_order_slots table
    op.create_table('display_order_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('display_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='available'),
        sa.Column('current_order_id', sa.Integer(), nullable=True),
        sa.Column('allocated_at', sa.DateTime(), nullable=True),
        sa.Column('cooldown_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.ForeignKeyConstraint(['current_order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('restaurant_id', 'display_number', name='uq_restaurant_display_number')
    )
    op.create_index('ix_display_order_slots_restaurant_id', 'display_order_slots', ['restaurant_id'], unique=False)
    op.create_index('ix_display_slot_status', 'display_order_slots', ['restaurant_id', 'status'], unique=False)

    # Add new columns to orders table
    # internal_order_id - UUID for system use
    op.add_column('orders', sa.Column('internal_order_id', sa.String(50), nullable=True, unique=True))

    # display_order_number - 4-digit number for human use
    op.add_column('orders', sa.Column('display_order_number', sa.Integer(), nullable=True))

    # Create index for efficient restaurant + display number lookups
    op.create_index('ix_order_restaurant_display', 'orders', ['restaurant_id', 'display_order_number'], unique=False)
    op.create_index('ix_order_restaurant_status', 'orders', ['restaurant_id', 'status'], unique=False)

    # Backfill existing orders with internal_order_id
    # This is done in a separate step since we can't use Python functions in raw SQL
    print("Note: Run backfill_order_ids() after migration to populate existing orders with internal_order_id")


def downgrade():
    # Remove indexes
    op.drop_index('ix_order_restaurant_status', table_name='orders')
    op.drop_index('ix_order_restaurant_display', table_name='orders')

    # Remove columns from orders
    op.drop_column('orders', 'display_order_number')
    op.drop_column('orders', 'internal_order_id')

    # Drop display_order_slots table
    op.drop_index('ix_display_slot_status', table_name='display_order_slots')
    op.drop_index('ix_display_order_slots_restaurant_id', table_name='display_order_slots')
    op.drop_table('display_order_slots')

