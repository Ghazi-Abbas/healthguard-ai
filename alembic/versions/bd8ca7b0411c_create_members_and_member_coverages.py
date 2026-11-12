
"""Create members and update member coverages.

Revision ID: bd8ca7b0411c
Revises: bcca42ed78ce
Create Date: 2026-10-25 20:54:04.393932
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision: str = "bd8ca7b0411c"
down_revision: Union[str, Sequence[str], None] = "bcca42ed78ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create members and update the existing member_coverages table."""

    # ---------------------------------------------------------
    # 1. Create members table
    # ---------------------------------------------------------
    op.create_table(
        "members",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_members_id",
        "members",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_members_organization_id",
        "members",
        ["organization_id"],
        unique=False,
    )

    # ---------------------------------------------------------
    # 2. Update existing member_coverages table
    # ---------------------------------------------------------
    # The table already exists, so DO NOT call op.create_table()
    # for member_coverages.

    op.add_column(
        "member_coverages",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "member_coverages",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # Backfill existing rows before making the columns NOT NULL.
    op.execute(
        sa.text(
            """
            UPDATE member_coverages
            SET created_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
               OR updated_at IS NULL
            """
        )
    )

    op.alter_column(
        "member_coverages",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False,
    )

    op.alter_column(
        "member_coverages",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False,
    )

    # ---------------------------------------------------------
    # 3. Add member_id -> members.id foreign key
    # ---------------------------------------------------------
    op.create_foreign_key(
        "fk_member_coverages_member_id_members",
        "member_coverages",
        "members",
        ["member_id"],
        ["id"],
    )


def downgrade() -> None:
    """Reverse the migration."""

    # Remove the foreign key first.
    op.drop_constraint(
        "fk_member_coverages_member_id_members",
        "member_coverages",
        type_="foreignkey",
    )

    # Remove only the columns added by this migration.
    op.drop_column("member_coverages", "updated_at")
    op.drop_column("member_coverages", "created_at")

    # Drop members after removing its dependent foreign key.
    op.drop_index(
        "ix_members_organization_id",
        table_name="members",
    )

    op.drop_index(
        "ix_members_id",
        table_name="members",
    )

    op.drop_table("members")
