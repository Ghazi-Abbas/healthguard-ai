
"""create authorization workflows

Revision ID: 56a119adcbb9
Revises: bd8ca7b0411c
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '56a119adcbb9'
down_revision: Union[str, Sequence[str], None] = 'bd8ca7b0411c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        'authorization_workflows',

        sa.Column(
            'id',
            sa.Integer(),
            autoincrement=True,
            nullable=False
        ),

        sa.Column(
            'authorization_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'organization_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'thread_id',
            sa.String(length=255),
            nullable=False
        ),

        sa.Column(
            'workflow_status',
            sa.String(length=50),
            nullable=False
        ),

        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False
        ),

        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ['authorization_id'],
            ['authorizations.id']
        ),

        sa.ForeignKeyConstraint(
            ['organization_id'],
            ['organizations.id']
        ),

        sa.PrimaryKeyConstraint('id'),

        sa.UniqueConstraint(
            'authorization_id',
            name='uq_workflow_authorization'
        ),

        sa.UniqueConstraint(
            'thread_id',
            name='uq_workflow_thread'
        )
    )


def downgrade() -> None:

    op.drop_table('authorization_workflows')
