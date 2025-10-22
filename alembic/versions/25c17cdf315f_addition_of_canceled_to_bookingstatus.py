"""addition of canceled to BookingStatus

Revision ID: 25c17cdf315f
Revises: dcbd84485e96
Create Date: 2025-10-22 07:03:01.293402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25c17cdf315f'
down_revision: Union[str, None] = 'dcbd84485e96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'canceled';")


def downgrade() -> None:
    pass