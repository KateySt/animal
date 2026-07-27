"""

Revision ID: 9ec6510b3a0d
Revises: fc241bfaf3fc
Create Date: 2026-07-27 12:29:07.488360

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ec6510b3a0d"
down_revision: str | Sequence[str] | None = "fc241bfaf3fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

currency_enum = postgresql.ENUM("usd", "uah", name="currency", create_type=True)


def upgrade() -> None:
    currency_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("invoices", sa.Column("currency", sa.Enum("usd", "uah", name="currency"), nullable=True))
    invoices = sa.table("invoices", sa.column("currency", sa.Enum("usd", "uah", name="currency")))
    op.execute(invoices.update().where(invoices.c.currency.is_(None)).values(currency="usd"))
    op.alter_column("invoices", "currency", nullable=False)


def downgrade() -> None:
    op.drop_column("invoices", "currency")
    currency_enum.drop(op.get_bind(), checkfirst=True)
