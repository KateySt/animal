"""add stripe_events

Revision ID: c6ba024d10c6
Revises: a9c7731ce189
Create Date: 2026-07-27 18:46:58.804712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6ba024d10c6'
down_revision: Union[str, Sequence[str], None] = 'a9c7731ce189'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('stripeevents',
    sa.Column('event_id', sa.String(), nullable=False),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('event_id')
    )


def downgrade() -> None:
    op.drop_table('stripeevents')