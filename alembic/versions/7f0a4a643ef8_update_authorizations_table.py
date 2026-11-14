"""Create the initial authorizations table.

Revision ID: 7f0a4a643ef8
Revises: 725edc2ecfb1
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "7f0a4a643ef8"
down_revision: Union[str, Sequence[str], None] = "725edc2ecfb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Later revisions add member_record_id and member_coverage_id.
    op.create_table(
        "authorizations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.String(length=100), nullable=False),
        sa.Column("procedure_code", sa.String(length=100), nullable=False),
        sa.Column("diagnosis_code", sa.String(length=100), nullable=False),
        sa.Column("clinical_summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_authorizations_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("authorizations")