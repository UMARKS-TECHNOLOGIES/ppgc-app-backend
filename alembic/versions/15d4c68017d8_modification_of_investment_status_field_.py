"""Modification of Investment status field to enum

Revision ID: 15d4c68017d8
Revises: 96a5de5b3f61
Create Date: 2025-11-04 09:12:03.174125
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15d4c68017d8'
down_revision: Union[str, None] = '96a5de5b3f61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1️⃣ Create the ENUM type explicitly
    investment_status = sa.Enum('active', 'completed', 'canceled', name='investment_status')
    investment_status.create(op.get_bind(), checkfirst=True)

    # 2️⃣ Alter the existing column to use the new ENUM
    op.alter_column(
        'investments',
        'status',
        existing_type=sa.VARCHAR(),
        type_=investment_status,
        existing_nullable=True,  # or False, depending on your model
        nullable=False,
        postgresql_using="status::investment_status",
    )


def downgrade() -> None:
    # 1️⃣ Revert the column back to VARCHAR
    op.alter_column(
        'investments',
        'status',
        existing_type=sa.Enum('active', 'completed', 'canceled', name='investment_status'),
        type_=sa.VARCHAR(),
        existing_nullable=False,
        nullable=True
    )

    # 2️⃣ Drop the ENUM type explicitly
    sa.Enum(name='investment_status').drop(op.get_bind(), checkfirst=True)
