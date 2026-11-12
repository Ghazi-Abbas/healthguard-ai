"""update authorizations table

Revision ID: 310baaac0bf2
Revises: 7f0a4a643ef8
Create Date: 2026-09-25 18:05:00.674357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '310baaac0bf2'
down_revision: Union[str, Sequence[str], None] = '7f0a4a643ef8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_foreign_key(
        "fk_authorizations_user_id_users",
        "authorizations",
        "users",
        ["user_id"],
        ["id"]
    )


def downgrade() -> None:

    op.drop_constraint(
        "fk_authorizations_user_id_users",
        "authorizations",
        type_="foreignkey"
    )
