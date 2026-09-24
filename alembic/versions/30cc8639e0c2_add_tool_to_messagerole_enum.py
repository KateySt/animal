"""add tool to messagerole enum

Revision ID: 30cc8639e0c2
Revises: e274bb6a42d1
Create Date: 2026-09-22 14:41:59.414358

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "30cc8639e0c2"
down_revision: str | Sequence[str] | None = "e274bb6a42d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE messagerole ADD VALUE IF NOT EXISTS 'tool'")


def downgrade() -> None:
    op.execute("ALTER TYPE messagerole RENAME TO messagerole_old")
    op.execute("CREATE TYPE messagerole AS ENUM ('user', 'assistant')")
    op.execute("ALTER TABLE chatmessages ALTER COLUMN role TYPE messagerole USING role::text::messagerole")
    op.execute("DROP TYPE messagerole_old")
