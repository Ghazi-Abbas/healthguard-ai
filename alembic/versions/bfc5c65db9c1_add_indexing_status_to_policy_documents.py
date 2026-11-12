"""add indexing status to policy documents

Revision ID: bfc5c65db9c1
Revises: a2236f563844
Create Date: 2026-10-22 22:28:50.185420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bfc5c65db9c1'
down_revision: Union[str, Sequence[str], None] = 'a2236f563844'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "policy_documents",
        sa.Column(
            "indexing_status",
            sa.String(length=30),
            server_default="PENDING",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("policy_documents", "indexing_status")
