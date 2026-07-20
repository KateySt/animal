"""

Revision ID: cc3ec08f54ef_add_animal_and_log
Revises:
Create Date: 2026-07-20 12:26:03.552746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc3ec08f54ef_add_animal_and_log'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('animals',
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('caretaker_notes', sa.String(length=255), nullable=True),
    sa.Column('gender', sa.Enum('MALE', 'FEMALE', 'UNKNOWN', name='gender'), nullable=False),
    sa.Column('birth_date', sa.Date(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('healthlogs',
    sa.Column('animal_id', sa.UUID(), nullable=False),
    sa.Column('procedure_name', sa.String(length=100), nullable=False),
    sa.Column('examination_findings', sa.String(length=255), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['animal_id'], ['animals.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('healthlogs')
    op.drop_table('animals')
