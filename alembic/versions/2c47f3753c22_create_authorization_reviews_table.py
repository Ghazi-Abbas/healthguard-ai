"""create authorization reviews table

Revision ID: 2c47f3753c22
Revises: 49c0717741fc
Create Date: 2026-11-05 22:55:15.641247

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2c47f3753c22'
down_revision: Union[str, Sequence[str], None] = '49c0717741fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
