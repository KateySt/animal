"""

Revision ID: 04284b37ab54
Revises: a1b2c3d4e5f6
Create Date: 2026-07-27 10:50:41.412274

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04284b37ab54'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('invoices',
    sa.Column('animal_id', sa.UUID(), nullable=False),
    sa.Column('health_log_id', sa.UUID(), nullable=False),
    sa.Column('amount_in_cents', sa.Integer(), nullable=False),
    sa.Column('issued_date', sa.Date(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'paid', 'cancelled', name='invoicestatus'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['animal_id'], ['animals.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['health_log_id'], ['healthlogs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('animals', sa.Column('owner_id', sa.UUID(), nullable=False))
    op.create_foreign_key(None, 'animals', 'users', ['owner_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    op.drop_constraint(None, 'animals', type_='foreignkey')
    op.drop_column('animals', 'owner_id')
    op.drop_table('invoices')
