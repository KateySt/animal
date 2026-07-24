"""rewrite auth rbac

Revision ID: 37c7a62f623f
Revises: 9eff90057fee_permissions
Create Date: 2026-07-23 19:21:30.448714

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "37c7a62f623f"
down_revision: str | Sequence[str] | None = "9eff90057fee_permissions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resources",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resources_name"), "resources", ["name"], unique=True)
    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("permissions_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "oauthaccounts",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("oauth_name", sa.String(length=100), nullable=False),
        sa.Column("access_token", sa.String(length=2048), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=True),
        sa.Column("refresh_token", sa.String(length=2048), nullable=True),
        sa.Column("account_id", sa.String(length=320), nullable=False),
        sa.Column("account_email", sa.String(length=320), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("oauth_name", "account_id", name="uq_oauth_provider_account"),
    )
    op.create_index(op.f("ix_oauthaccounts_account_id"), "oauthaccounts", ["account_id"], unique=False)
    op.create_index(op.f("ix_oauthaccounts_oauth_name"), "oauthaccounts", ["oauth_name"], unique=False)
    op.create_index(op.f("ix_oauthaccounts_user_id"), "oauthaccounts", ["user_id"], unique=False)
    op.create_table(
        "refreshtokens",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("user_agent", sa.String(length=400), nullable=True),
        sa.Column("rotated_to", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["rotated_to"], ["refreshtokens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refreshtokens_token_hash"), "refreshtokens", ["token_hash"], unique=True)
    op.create_index(op.f("ix_refreshtokens_user_id"), "refreshtokens", ["user_id"], unique=False)
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )
    op.drop_index(op.f("ix_oauth_account_account_id"), table_name="oauth_account")
    op.drop_index(op.f("ix_oauth_account_oauth_name"), table_name="oauth_account")
    op.drop_table("oauth_account")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")

    op.drop_table("permissions")
    op.create_table(
        "permissions",
        sa.Column("resource_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource_id", "action", name="uq_permission_resource_action"),
    )
    op.create_index(op.f("ix_permissions_resource_id"), "permissions", ["resource_id"], unique=False)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("permission_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.execute("DROP TYPE IF EXISTS policy")
    op.execute("DROP TYPE IF EXISTS role")


def downgrade() -> None:
    op.add_column("permissions", sa.Column("role", postgresql.ENUM("user", "admin", "staff", name="role"), autoincrement=False, nullable=False))
    op.add_column("permissions", sa.Column("resource", sa.VARCHAR(length=100), autoincrement=False, nullable=False))
    op.drop_constraint(None, "permissions", type_="foreignkey")
    op.drop_constraint("uq_permission_resource_action", "permissions", type_="unique")
    op.drop_index(op.f("ix_permissions_resource_id"), table_name="permissions")
    op.alter_column(
        "permissions",
        "action",
        existing_type=sa.String(length=20),
        type_=postgresql.ENUM("read", "create", "update", "delete", name="policy"),
        existing_nullable=False,
    )
    op.drop_column("permissions", "resource_id")
    op.create_table(
        "user",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("email", sa.VARCHAR(length=320), autoincrement=False, nullable=False),
        sa.Column("hashed_password", sa.VARCHAR(length=1024), autoincrement=False, nullable=False),
        sa.Column("is_active", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("is_superuser", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("is_verified", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), autoincrement=False, nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), autoincrement=False, nullable=True),
        sa.Column(
            "role",
            postgresql.ENUM("user", "admin", "staff", name="role"),
            server_default=sa.text("'user'::role"),
            autoincrement=False,
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("user_pkey")),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_table(
        "oauth_account",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("oauth_name", sa.VARCHAR(length=100), autoincrement=False, nullable=False),
        sa.Column("access_token", sa.VARCHAR(length=1024), autoincrement=False, nullable=False),
        sa.Column("expires_at", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("refresh_token", sa.VARCHAR(length=1024), autoincrement=False, nullable=True),
        sa.Column("account_id", sa.VARCHAR(length=320), autoincrement=False, nullable=False),
        sa.Column("account_email", sa.VARCHAR(length=320), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("oauth_account_user_id_fkey"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("oauth_account_pkey")),
    )
    op.create_index(op.f("ix_oauth_account_oauth_name"), "oauth_account", ["oauth_name"], unique=False)
    op.create_index(op.f("ix_oauth_account_account_id"), "oauth_account", ["account_id"], unique=False)
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_index(op.f("ix_refreshtokens_user_id"), table_name="refreshtokens")
    op.drop_index(op.f("ix_refreshtokens_token_hash"), table_name="refreshtokens")
    op.drop_table("refreshtokens")
    op.drop_index(op.f("ix_oauthaccounts_user_id"), table_name="oauthaccounts")
    op.drop_index(op.f("ix_oauthaccounts_oauth_name"), table_name="oauthaccounts")
    op.drop_index(op.f("ix_oauthaccounts_account_id"), table_name="oauthaccounts")
    op.drop_table("oauthaccounts")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")
    op.drop_index(op.f("ix_resources_name"), table_name="resources")
    op.drop_table("resources")
