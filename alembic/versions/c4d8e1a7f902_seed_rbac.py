"""seed roles, resources and permissions

Revision ID: c4d8e1a7f902
Revises: b3e1f0c2d4a5
Create Date: 2026-10-08 12:00:00.000000

Idempotent: rows that already exist (e.g. created by hand in the admin) are kept as is.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from alembic import op

revision: str = "c4d8e1a7f902"
down_revision: str | Sequence[str] | None = "b3e1f0c2d4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ACTIONS = ("read", "create", "update", "delete")

RESOURCES = {
    "animals": "Animals",
    "healthlogs": "Animal health logs",
}

ROLES = {
    "admin": ("Administrator", [f"{resource}:{action}" for resource in RESOURCES for action in ACTIONS]),
    "vet": ("Veterinarian", [f"{resource}:{action}" for resource in RESOURCES for action in ACTIONS]),
}

resources = sa.table(
    "resources",
    sa.column("id", sa.UUID()),
    sa.column("name", sa.String()),
    sa.column("description", sa.String()),
)
roles = sa.table(
    "roles",
    sa.column("id", sa.UUID()),
    sa.column("name", sa.String()),
    sa.column("description", sa.String()),
)
permissions = sa.table(
    "permissions",
    sa.column("id", sa.UUID()),
    sa.column("resource_id", sa.UUID()),
    sa.column("action", sa.String()),
)
role_permissions = sa.table(
    "role_permissions",
    sa.column("role_id", sa.UUID()),
    sa.column("permission_id", sa.UUID()),
)
users = sa.table("users", sa.column("permissions_version", sa.Integer()))


def upgrade() -> None:
    op.execute(
        insert(resources)
        .values([{"id": sa.func.gen_random_uuid(), "name": name, "description": description} for name, description in RESOURCES.items()])
        .on_conflict_do_nothing(index_elements=["name"])
    )

    actions = sa.values(sa.column("action", sa.String()), name="actions").data([(action,) for action in ACTIONS])
    op.execute(
        insert(permissions)
        .from_select(
            ["id", "resource_id", "action"],
            sa.select(sa.func.gen_random_uuid(), resources.c.id, actions.c.action)
            .select_from(resources.join(actions, sa.true()))
            .where(resources.c.name.in_(RESOURCES)),
        )
        .on_conflict_do_nothing(constraint="uq_permission_resource_action")
    )

    op.execute(
        insert(roles)
        .values([{"id": sa.func.gen_random_uuid(), "name": name, "description": description} for name, (description, _) in ROLES.items()])
        .on_conflict_do_nothing(index_elements=["name"])
    )

    for role_name, (_, scopes) in ROLES.items():
        for scope in scopes:
            resource_name, action = scope.split(":")
            op.execute(
                insert(role_permissions)
                .from_select(
                    ["role_id", "permission_id"],
                    sa.select(roles.c.id, permissions.c.id)
                    .select_from(permissions.join(resources, resources.c.id == permissions.c.resource_id))
                    .where(roles.c.name == role_name, resources.c.name == resource_name, permissions.c.action == action),
                )
                .on_conflict_do_nothing()
            )

    op.execute(users.update().values(permissions_version=users.c.permissions_version + 1))


def downgrade() -> None:
    role_ids = sa.select(roles.c.id).where(roles.c.name.in_(ROLES))
    resource_ids = sa.select(resources.c.id).where(resources.c.name.in_(RESOURCES))

    op.execute(role_permissions.delete().where(role_permissions.c.role_id.in_(role_ids)))
    op.execute(permissions.delete().where(permissions.c.resource_id.in_(resource_ids)))
    op.execute(resources.delete().where(resources.c.name.in_(RESOURCES)))
    op.execute(roles.delete().where(roles.c.name.in_(ROLES)))
    op.execute(users.update().values(permissions_version=users.c.permissions_version + 1))
