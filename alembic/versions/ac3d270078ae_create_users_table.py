"""create users table

Revision ID: ac3d270078ae
Revises: 43ea28decddb
Create Date: 2026-09-21 13:02:20.968754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac3d270078ae'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True
        ),

        sa.Column(
            "email",
            sa.String(255),
            nullable=False
        ),

        sa.Column(
            "password_hash",
            sa.String(255),
            nullable=False
        ),

        sa.Column(
            "role",
            sa.String(50),
            nullable=False
        ),

        sa.Column(
            "organization_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("users")

'''
So your statement is essentially right:

"Alembic changes the actual database, while the model changes the
Python/SQLAlchemy representation. Since the application needs the
model and the database needs the migration, both need to be updated
 when the schema changes."

One nuance: you don't necessarily update both for every change—some
 changes are application-only and don't affect the DB schema. But
 for a database schema change, keeping the model and DB synchronized
   through an Alembic migration is the correct approach.
'''
