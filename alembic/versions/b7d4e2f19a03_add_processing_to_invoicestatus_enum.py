"""add processing value to invoicestatus enum

Revision ID: b7d4e2f19a03
Revises: a3f1c9d2b7e4
Create Date: 2026-08-08 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d4e2f19a03"
down_revision: str | Sequence[str] | None = "a3f1c9d2b7e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'processing' BEFORE 'paid'")


def downgrade() -> None:
    # PostgreSQL cannot drop a single enum value, so recreate the type without it.
    op.execute("ALTER TYPE invoicestatus RENAME TO invoicestatus_old")
    op.execute("CREATE TYPE invoicestatus AS ENUM ('pending', 'paid', 'cancelled')")
    op.execute("UPDATE invoices SET status = 'pending' WHERE status = 'processing'")
    op.execute(
        "ALTER TABLE invoices ALTER COLUMN status TYPE invoicestatus "
        "USING status::text::invoicestatus"
    )
    op.execute("DROP TYPE invoicestatus_old")
