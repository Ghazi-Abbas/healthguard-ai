"""update users table
# alembic revision -m "update users table"
Revision ID: 725edc2ecfb1
Revises: ac3d270078ae
Create Date: 2026-09-25 15:45:48.644828

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '725edc2ecfb1'
down_revision: Union[str, Sequence[str], None] = 'ac3d270078ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # Add is_active
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true()
        )
    )

    # Add updated_at
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        )
    )

    # Add foreign key:
    # users.organization_id -> organizations.id
    op.create_foreign_key(
        "fk_users_organization_id",
        "users",
        "organizations",
        ["organization_id"],
        ["id"]
    )

    # Add unique constraint on email
    op.create_unique_constraint(
        "uq_users_email",
        "users",
        ["email"]
    )


def downgrade() -> None:

    op.drop_constraint(
        "uq_users_email",
        "users",
        type_="unique"
    )

    op.drop_constraint(
        "fk_users_organization_id",
        "users",
        type_="foreignkey"
    )

    op.drop_column(
        "users",
        "updated_at"
    )

    op.drop_column(
        "users",
        "is_active"
    )

    # alembic upgrade head
