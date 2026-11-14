
"""create authorization reviews table

Revision ID: 2c47f3753c22
Revises: 49c0717741fc
Create Date: 2026-11-05 22:55:15.641247
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2c47f3753c22"
down_revision: Union[str, Sequence[str], None] = "49c0717741fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "authorization_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("authorization_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["authorization_id"], ["authorizations.id"]
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"], ["users.id"]
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"]
        ),
    )

    op.create_index(
        "ix_authorization_reviews_authorization_id",
        "authorization_reviews",
        ["authorization_id"],
    )

    op.create_index(
        "ix_authorization_reviews_reviewer_id",
        "authorization_reviews",
        ["reviewer_id"],
    )

    op.create_index(
        "ix_authorization_reviews_organization_id",
        "authorization_reviews",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_authorization_reviews_organization_id",
        table_name="authorization_reviews",
    )

    op.drop_index(
        "ix_authorization_reviews_reviewer_id",
        table_name="authorization_reviews",
    )

    op.drop_index(
        "ix_authorization_reviews_authorization_id",
        table_name="authorization_reviews",
    )

    op.drop_table("authorization_reviews")
