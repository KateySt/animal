"""

Revision ID: 5b5e74bdf0e9
Revises: f3e64415bb00
Create Date: 2026-07-30 15:27:48.589913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b5e74bdf0e9'
down_revision: Union[str, Sequence[str], None] = 'f3e64415bb00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chatsessions',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatsessions_user_id'), 'chatsessions', ['user_id'], unique=False)
    op.create_table('chatmessages',
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('role', sa.Enum('user', 'assistant', name='messagerole'), nullable=False),
    sa.Column('content', sa.JSON(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['chatsessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatmessages_session_id'), 'chatmessages', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chatmessages_session_id'), table_name='chatmessages')
    op.drop_table('chatmessages')
    op.drop_index(op.f('ix_chatsessions_user_id'), table_name='chatsessions')
    op.drop_table('chatsessions')
