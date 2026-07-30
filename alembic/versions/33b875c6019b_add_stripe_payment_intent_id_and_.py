"""add stripe_payment_intent_id and processing status

Revision ID: 33b875c6019b
Revises: c6ba024d10c6
Create Date: 2026-07-28 18:32:15.250496

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '33b875c6019b'
down_revision: Union[str, Sequence[str], None] = 'c6ba024d10c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('invoices', sa.Column('stripe_payment_intent_id', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'invoices', ['stripe_payment_intent_id'])


def downgrade() -> None:
    op.drop_constraint(None, 'invoices', type_='unique')
    op.drop_column('invoices', 'stripe_payment_intent_id')
