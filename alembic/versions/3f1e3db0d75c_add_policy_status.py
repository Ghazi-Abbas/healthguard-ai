
"""add policy status

Revision ID: 3f1e3db0d75c
Revises: a2b6bb1e0a96
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision: str = "3f1e3db0d75c"
down_revision: Union[str, Sequence[str], None] = "a2b6bb1e0a96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The status column was already added by
    # revision 3f1e3db0d75c.
    # Update the default to ACTIVE instead.
    op.alter_column(
        "policies",
        "status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default="ACTIVE",
    )


def downgrade() -> None:
    # Restore the previous default.
    op.alter_column(
        "policies",
        "status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default="DRAFT",
    )
