"""Create policy tables.

Revision ID: 3f1e3db0d75c
Revises: a2b6bb1e0a96
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "3f1e3db0d75c"
down_revision: Union[str, Sequence[str], None] = "a2b6bb1e0a96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.String(length=50), nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("version", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"],
            name="fk_policies_organization_id_organizations",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("processing_status", sa.String(length=50), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["policy_id"], ["policies.id"],
            name="fk_policy_documents_policy_id_policies",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy_document_pages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["policy_documents.id"],
            name="fk_policy_document_pages_document_id_policy_documents",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("policy_document_pages")
    op.drop_table("policy_documents")
    op.drop_table("policies")