
"""create users table and organizations table

Revision ID: ac3d270078ae
Revises: None
Create Date: 2026-09-21 13:02:20.968754
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ac3d270078ae"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # Create organizations first
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True
        ),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False
        ),
    )

    # Create users
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True
        ),
        sa.Column(
            "email",
            sa.String(255),
            nullable=False
        ),
        sa.Column(
            "password_hash",
            sa.String(255),
            nullable=False
        ),
        sa.Column(
            "role",
            sa.String(50),
            nullable=False
        ),
        sa.Column(
            "organization_id",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),
    )


def downgrade() -> None:

    # Drop users before organizations
    op.drop_table("users")
    op.drop_table("organizations")
