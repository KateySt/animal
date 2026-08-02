"""

Revision ID: a3f1c9d2b7e4
Revises: 88bfc51b87f7
Create Date: 2026-08-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f1c9d2b7e4"
down_revision: str | Sequence[str] | None = "88bfc51b87f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chatsessions", sa.Column("last_summarized_message_id", sa.UUID(), nullable=True))


def downgrade() -> None:
    op.drop_column("chatsessions", "last_summarized_message_id")
