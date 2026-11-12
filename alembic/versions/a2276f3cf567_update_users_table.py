"""update users table

Revision ID: a2276f3cf567
Revises: 310baaac0bf2
Create Date: 2026-09-28 15:40:34.119757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2276f3cf567'
down_revision: Union[str, Sequence[str], None] = '310baaac0bf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "username",
            sa.String(length=128),
            nullable=True
        )
    )

    # Backfill existing users here
    # Then make it NOT NULL

    op.alter_column(
        "users",
        "username",
        nullable=False
    )
