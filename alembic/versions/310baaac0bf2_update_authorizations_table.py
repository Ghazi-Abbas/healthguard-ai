"""The authorizations user foreign key is created with the base table.

Revision ID: 310baaac0bf2
Revises: 7f0a4a643ef8
"""

from typing import Sequence, Union

revision: str = "310baaac0bf2"
down_revision: Union[str, Sequence[str], None] = "7f0a4a643ef8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Avoid creating the same foreign key twice.
    pass


def downgrade() -> None:
    pass