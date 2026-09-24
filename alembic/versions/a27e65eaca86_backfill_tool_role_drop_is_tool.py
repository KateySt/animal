"""backfill tool role drop is_tool

Revision ID: a27e65eaca86
Revises: 30cc8639e0c2
Create Date: 2026-09-22 14:47:57.177360

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a27e65eaca86"
down_revision: str | Sequence[str] | None = "30cc8639e0c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE chatmessages SET role = 'tool' WHERE is_tool = true")
    op.drop_column("chatmessages", "is_tool")


def downgrade() -> None:
    op.add_column("chatmessages", sa.Column("is_tool", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("chatmessages", "is_tool", server_default=None)
    op.execute("UPDATE chatmessages SET is_tool = true, role = 'user' WHERE role = 'tool'")
