"""rename chatdocuments.minio_object_name to storage_key

Revision ID: b3e1f0c2d4a5
Revises: 40773d7cb700
Create Date: 2026-10-08 16:45:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3e1f0c2d4a5'
down_revision: str | Sequence[str] | None = '40773d7cb700'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column('chatdocuments', 'minio_object_name', new_column_name='storage_key')


def downgrade() -> None:
    op.alter_column('chatdocuments', 'storage_key', new_column_name='minio_object_name')
