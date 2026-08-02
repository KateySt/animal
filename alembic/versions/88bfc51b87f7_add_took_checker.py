"""

Revision ID: 88bfc51b87f7
Revises: 5b5e74bdf0e9
Create Date: 2026-07-30 16:03:18.424895

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "88bfc51b87f7"
down_revision: str | Sequence[str] | None = "5b5e74bdf0e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chatmessages", sa.Column("is_tool", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("chatmessages", "is_tool", server_default=None)


def downgrade() -> None:
    op.drop_column("chatmessages", "is_tool")
