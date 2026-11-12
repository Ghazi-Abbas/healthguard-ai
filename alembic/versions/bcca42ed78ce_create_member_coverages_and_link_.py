"""create member coverages and link authorizations

Revision ID: bcca42ed78ce
Revises: bfc5c65db9c1
Create Date: 2026-10-25 15:16:31.907275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bcca42ed78ce'
down_revision: Union[str, Sequence[str], None] = 'bfc5c65db9c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create member_coverages table.
    op.create_table(
        "member_coverages",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "member_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "member_number",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "coverage_status",
            sa.String(length=30),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column(
            "effective_date",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "termination_date",
            sa.Date(),
            nullable=True,
        ),
    )

    # 2. Create index on member_id.
    op.create_index(
        "ix_member_coverages_member_id",
        "member_coverages",
        ["member_id"],
        unique=False,
    )

    # 3. Add member_coverage_id to existing authorizations.
    # Nullable allows existing authorization rows to remain valid.
    op.add_column(
        "authorizations",
        sa.Column(
            "member_coverage_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # 4. Create the foreign key.
    op.create_foreign_key(
        "fk_authorizations_member_coverage_id",
        "authorizations",
        "member_coverages",
        ["member_coverage_id"],
        ["id"],
    )


def downgrade() -> None:
    # Reverse the changes in dependency order.
    op.drop_constraint(
        "fk_authorizations_member_coverage_id",
        "authorizations",
        type_="foreignkey",
    )

    op.drop_column(
        "authorizations",
        "member_coverage_id",
    )

    op.drop_index(
        "ix_member_coverages_member_id",
        table_name="member_coverages",
    )

    op.drop_table("member_coverages")
