"""Non-nullability of room_number

Revision ID: bbf8aff64387
Revises: f53e08ca5be4
Create Date: 2025-11-21 20:37:22.926251
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'bbf8aff64387'
down_revision: Union[str, None] = 'f53e08ca5be4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # 1️⃣ Fix NULL room numbers
    op.execute(
        "UPDATE rooms SET room_number = CONCAT('TEMP-', id) WHERE room_number IS NULL"
    )

    # 3️⃣ Apply NOT NULL constraints
    op.alter_column(
        'rooms',
        'room_number',
        existing_type=sa.VARCHAR(length=50),
        nullable=False
    )


def downgrade() -> None:

    # Roll back NOT NULL constraints
    op.alter_column(
        'rooms',
        'room_number',
        existing_type=sa.VARCHAR(length=50),
        nullable=True
    )
