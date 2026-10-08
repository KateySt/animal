"""add chat documents

Revision ID: 40773d7cb700
Revises: a27e65eaca86
Create Date: 2026-10-01 09:39:12.900887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40773d7cb700'
down_revision: Union[str, Sequence[str], None] = 'a27e65eaca86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chatdocuments',
    sa.Column('chat_session_id', sa.UUID(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=100), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('minio_object_name', sa.String(length=512), nullable=False),
    sa.Column('status', sa.Enum('uploading', 'embedding', 'ready', 'failed', name='documentstatus'), nullable=False),
    sa.Column('error_message', sa.String(length=500), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['chat_session_id'], ['chatsessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatdocuments_chat_session_id'), 'chatdocuments', ['chat_session_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chatdocuments_chat_session_id'), table_name='chatdocuments')
    op.drop_table('chatdocuments')
