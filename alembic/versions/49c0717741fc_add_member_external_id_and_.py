
"""add member external id and authorization member relation

Revision ID: 49c0717741fc
Revises: 56a119adcbb9
Create Date: 2026-11-05 14:44:33.956202

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision: str = '49c0717741fc'
down_revision: Union[str, Sequence[str], None] = '56a119adcbb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # 1. Add external member identifier
    op.add_column(
        'members',
        sa.Column(
            'external_member_id',
            sa.String(length=100),
            nullable=False
        )
    )

    # 2. Ensure external member ID is unique within an organization
    op.create_unique_constraint(
        'uq_member_org_external_id',
        'members',
        ['organization_id', 'external_member_id']
    )

    # 3. Add internal member foreign key column
    op.add_column(
        'authorizations',
        sa.Column(
            'member_record_id',
            sa.Integer(),
            nullable=False
        )
    )

    # 4. Create index
    op.create_index(
        'ix_authorizations_member_record_id',
        'authorizations',
        ['member_record_id'],
        unique=False
    )

    # 5. Connect authorization to member
    op.create_foreign_key(
        'fk_authorizations_member_record_id_members',
        'authorizations',
        'members',
        ['member_record_id'],
        ['id']
    )


def downgrade() -> None:

    # 1. Remove foreign key
    op.drop_constraint(
        'fk_authorizations_member_record_id_members',
        'authorizations',
        type_='foreignkey'
    )

    # 2. Remove index
    op.drop_index(
        'ix_authorizations_member_record_id',
        table_name='authorizations'
    )

    # 3. Remove authorization column
    op.drop_column(
        'authorizations',
        'member_record_id'
    )

    # 4. Remove unique constraint
    op.drop_constraint(
        'uq_member_org_external_id',
        'members',
        type_='unique'
    )

    # 5. Remove member column
    op.drop_column(
        'members',
        'external_member_id'
    )
