"""Set the policy status default to ACTIVE.

Revision ID: a2236f563844
Revises: 3f1e3db0d75c
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a2236f563844"
down_revision: Union[str, Sequence[str], None] = "3f1e3db0d75c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "policies", "status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default="ACTIVE",
    )


def downgrade() -> None:
    op.alter_column(
        "policies", "status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default="DRAFT",
    )