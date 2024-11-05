"""Add is_verified field to User model

Revision ID: 23c2ce0313f4
Revises: e42f678cfd04
Create Date: 2024-11-05 16:46:06.147026

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '23c2ce0313f4'
down_revision = 'e42f678cfd04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # adding is_verified field to users table
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True))


def downgrade() -> None:
    # deleting is_verified field from users table
    op.drop_column('users', 'is_verified')
