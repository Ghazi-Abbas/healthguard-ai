"""update document table

Revision ID: a2b6bb1e0a96
Revises: 1f98a7967361
Create Date: 2026-09-30 01:38:10.242160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b6bb1e0a96'
down_revision: Union[str, Sequence[str], None] = '1f98a7967361'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("page_count", sa.Integer(), nullable=False)
    )

    op.drop_column(
        "documents",
        "storage_key"
    )


def downgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("storage_key", sa.String(length=500), nullable=True)
    )

    op.drop_column(
        "documents",
        "page_count"
    )
