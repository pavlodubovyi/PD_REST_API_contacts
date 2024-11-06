"""Initial migration

Revision ID: f02caee9c2f5
Revises: 
Create Date: 2024-11-06 15:34:45.595232

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f02caee9c2f5"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("avatar", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("birthday", sa.Date(), nullable=True),
        sa.Column("additional_info", sa.String(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contacts_email"), "contacts", ["email"], unique=True)
    op.create_index(
        op.f("ix_contacts_first_name"), "contacts", ["first_name"], unique=False
    )
    op.create_index(op.f("ix_contacts_id"), "contacts", ["id"], unique=False)
    op.create_index(
        op.f("ix_contacts_last_name"), "contacts", ["last_name"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_contacts_last_name"), table_name="contacts")
    op.drop_index(op.f("ix_contacts_id"), table_name="contacts")
    op.drop_index(op.f("ix_contacts_first_name"), table_name="contacts")
    op.drop_index(op.f("ix_contacts_email"), table_name="contacts")
    op.drop_table("contacts")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    # ### end Alembic commands ###