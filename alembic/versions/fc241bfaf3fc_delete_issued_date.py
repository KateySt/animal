"""

Revision ID: fc241bfaf3fc
Revises: 04284b37ab54
Create Date: 2026-07-27 11:41:44.744213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc241bfaf3fc'
down_revision: Union[str, Sequence[str], None] = '04284b37ab54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('invoices', 'issued_date')

def downgrade() -> None:
    op.add_column('invoices', sa.Column('issued_date', sa.DATE(), autoincrement=False, nullable=False))
