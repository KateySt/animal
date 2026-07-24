"""seed roles and permissions

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-27 00:00:00.000000
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOW = datetime.now(UTC)
ACTIONS = ("read", "create", "update", "delete")

# Module-level so downgrade() can reference the same UUIDs
R_ANIMALS: UUID = uuid4()
R_HEALTH_LOGS: UUID = uuid4()

P_ANIMALS: dict[str, UUID] = {a: uuid4() for a in ACTIONS}
P_HEALTH_LOGS: dict[str, UUID] = {a: uuid4() for a in ACTIONS}

ROLE_VIEWER: UUID = uuid4()
ROLE_VET: UUID = uuid4()
ROLE_STAFF: UUID = uuid4()

resources_table = sa.table(
    "resources",
    sa.column("id", PG_UUID(as_uuid=True)),
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

permissions_table = sa.table(
    "permissions",
    sa.column("id", PG_UUID(as_uuid=True)),
    sa.column("resource_id", PG_UUID(as_uuid=True)),
    sa.column("action", sa.String),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

roles_table = sa.table(
    "roles",
    sa.column("id", PG_UUID(as_uuid=True)),
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

role_permissions_table = sa.table(
    "role_permissions",
    sa.column("role_id", PG_UUID(as_uuid=True)),
    sa.column("permission_id", PG_UUID(as_uuid=True)),
)


def upgrade() -> None:
    op.bulk_insert(
        resources_table,
        [
            {"id": R_ANIMALS, "name": "animals", "description": "Animal records", "created_at": NOW, "updated_at": NOW},
            {"id": R_HEALTH_LOGS, "name": "health_logs", "description": "Animal health logs", "created_at": NOW, "updated_at": NOW},
        ],
    )

    op.bulk_insert(
        permissions_table,
        [
            *({"id": P_ANIMALS[a], "resource_id": R_ANIMALS, "action": a, "created_at": NOW, "updated_at": NOW} for a in ACTIONS),
            *({"id": P_HEALTH_LOGS[a], "resource_id": R_HEALTH_LOGS, "action": a, "created_at": NOW, "updated_at": NOW} for a in ACTIONS),
        ],
    )

    op.bulk_insert(
        roles_table,
        [
            {"id": ROLE_VIEWER, "name": "viewer", "description": "Read-only access to animals and health logs", "created_at": NOW, "updated_at": NOW},
            {"id": ROLE_VET, "name": "vet", "description": "Read animals; read, create and update health logs", "created_at": NOW, "updated_at": NOW},
            {"id": ROLE_STAFF, "name": "staff", "description": "Full CRUD on animals and health logs", "created_at": NOW, "updated_at": NOW},
        ],
    )

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": ROLE_VIEWER, "permission_id": P_ANIMALS["read"]},
            {"role_id": ROLE_VIEWER, "permission_id": P_HEALTH_LOGS["read"]},
            {"role_id": ROLE_VET, "permission_id": P_ANIMALS["read"]},
            {"role_id": ROLE_VET, "permission_id": P_HEALTH_LOGS["read"]},
            {"role_id": ROLE_VET, "permission_id": P_HEALTH_LOGS["create"]},
            {"role_id": ROLE_VET, "permission_id": P_HEALTH_LOGS["update"]},
            *({"role_id": ROLE_STAFF, "permission_id": P_ANIMALS[a]} for a in ACTIONS),
            *({"role_id": ROLE_STAFF, "permission_id": P_HEALTH_LOGS[a]} for a in ACTIONS),
        ],
    )


def downgrade() -> None:
    op.execute(role_permissions_table.delete().where(role_permissions_table.c.role_id.in_([ROLE_VIEWER, ROLE_VET, ROLE_STAFF])))
    op.execute(roles_table.delete().where(roles_table.c.id.in_([ROLE_VIEWER, ROLE_VET, ROLE_STAFF])))
    op.execute(permissions_table.delete().where(permissions_table.c.id.in_([*P_ANIMALS.values(), *P_HEALTH_LOGS.values()])))
    op.execute(resources_table.delete().where(resources_table.c.id.in_([R_ANIMALS, R_HEALTH_LOGS])))
