"""Add phone and created_by_id to User model

Revision ID: add_user_phone_created_by
Revises:
Create Date: 2024-12-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_phone_created_by'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add phone column
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('created_by_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_users_created_by', 'users', ['created_by_id'], ['id'])


def downgrade():
    # Remove columns
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_created_by', type_='foreignkey')
        batch_op.drop_column('created_by_id')
        batch_op.drop_column('phone')

