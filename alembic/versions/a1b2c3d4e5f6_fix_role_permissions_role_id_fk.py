"""
Revision ID: a1b2c3d4e5f6
Revises: ccd2f695bfe7
Create Date: 2026-07-24 17:18:00.000000

Migration 37c7a62f623f created role_permissions.role_id FK with ondelete=CASCADE,
but the model declares ondelete=RESTRICT. Align DB to match the model.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "ccd2f695bfe7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("role_permissions_role_id_fkey", "role_permissions", type_="foreignkey")
    op.create_foreign_key(
        "role_permissions_role_id_fkey",
        "role_permissions",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("role_permissions_role_id_fkey", "role_permissions", type_="foreignkey")
    op.create_foreign_key(
        "role_permissions_role_id_fkey",
        "role_permissions",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="CASCADE",
    )
