"""update authorizations table

Revision ID: 7f0a4a643ef8
Revises: 725edc2ecfb1
Create Date: 2026-09-25 17:50:09.960500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f0a4a643ef8'
down_revision: Union[str, Sequence[str], None] = '725edc2ecfb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "authorizations",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True
        )
    )

    op.add_column(
        "authorizations",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True
        )
    )

    # Make existing rows valid first
    op.execute(
        """
        UPDATE authorizations
        SET created_at = NOW()
        WHERE created_at IS NULL
        """
    )

    op.execute(
        """
        UPDATE authorizations
        SET updated_at = NOW()
        WHERE updated_at IS NULL
        """
    )

    # Now make them NOT NULL
    op.alter_column(
        "authorizations",
        "created_at",
        nullable=False
    )

    op.alter_column(
        "authorizations",
        "updated_at",
        nullable=False
    )

    # user_id was previously nullable
    op.alter_column(
        "authorizations",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False
    )

    op.create_foreign_key(
        "fk_authorizations_user_id_users",
        "authorizations",
        "users",
        ["user_id"],
        ["id"]
    )



def downgrade() -> None:

    op.alter_column(
        "authorizations",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True
    )

    op.drop_column(
        "authorizations",
        "updated_at"
    )

    op.drop_column(
        "authorizations",
        "created_at"
    )
