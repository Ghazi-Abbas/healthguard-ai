"""add policy status

Revision ID: a2236f563844
Revises: 3f1e3db0d75c
Create Date: 2026-10-18 00:56:42.356102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a2236f563844'
down_revision: Union[str, Sequence[str], None] = '3f1e3db0d75c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None






def upgrade() -> None:
    # The previous migration already added this column.
    # Change its database default to ACTIVE.
    op.alter_column(
        "policies",
        "status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default="ACTIVE",
    )


def downgrade() -> None:
    # Restore the previous database default.
    op.alter_column(
        "policies",
        "status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default="DRAFT",
    )
