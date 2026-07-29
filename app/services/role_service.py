from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import column, delete, except_, select, update, values
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.error_codes import ErrorCode
from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.db.models import Permission, Role, role_crud
from app.db.models.associations import role_permissions, user_roles
from app.db.models.user import User
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.redis_service import redis_service


class RoleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_roles(self) -> dict:
        return await role_crud.get_multi(self._session, limit=None, return_total_count=False)

    async def get_role(self, role_id: UUID) -> Role:
        role = await self._session.scalar(
            select(Role).options(selectinload(Role.permissions).selectinload(Permission.resource)).where(
                Role.id == role_id)
        )
        if role is None:
            raise NotFoundError(ErrorCode.ROLE_NOT_FOUND)
        return role

    async def check_role(self, role_id: UUID) -> None:
        if not await role_crud.exists(self._session, id=role_id):
            raise NotFoundError(ErrorCode.ROLE_NOT_FOUND)

    async def create_role(self, payload: RoleCreate) -> RoleRead:
        if await role_crud.exists(self._session, name=payload.name):
            raise AlreadyExistsError(ErrorCode.ROLE_ALREADY_EXISTS)

        return await role_crud.create(
            self._session,
            payload,
            schema_to_select=RoleRead,
        )

    async def update_role(self, role_id: UUID, payload: RoleUpdate) -> RoleRead:
        await self.check_role(role_id)

        return await role_crud.update(
            self._session,
            payload.model_dump(exclude_unset=True),
            id=role_id,
            return_columns=role_crud.model_col_names,
        )

    async def delete_role(self, role_id: UUID) -> None:
        await self.check_role(role_id)
        await role_crud.delete(self._session, id=role_id)

    async def set_role_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> Role:
        await self.check_role(role_id)

        not_found_permissions = (
            await self._session.scalars(
                except_(
                    select(values(column("id", Permission.id.type), name="requested").data(
                        [(pid,) for pid in permission_ids]).c.id),
                    select(Permission.id).where(Permission.id.in_(permission_ids)),
                )
            )
        ).all()
        if not_found_permissions:
            raise NotFoundError(ErrorCode.PERMISSIONS_NOT_FOUND)

        await self._session.execute(delete(role_permissions).where(role_permissions.c.role_id == role_id))
        for pid in permission_ids:
            await self._session.execute(role_permissions.insert().values(role_id=role_id, permission_id=pid))

        affected = await self._bump_permissions_version_by_role(role_id)
        await self._session.commit()
        for user_id in affected:
            await redis_service.delete_cache(f"permissions_version:{user_id}")
        return await self.get_role(role_id)

    async def assign_roles_to_user(self, user_id: UUID, role_ids: list[UUID]) -> User:
        user = await self._session.scalar(select(User).options(selectinload(User.roles)).where(User.id == user_id))
        if user is None:
            raise NotFoundError(ErrorCode.USER_NOT_FOUND)

        roles = (await self._session.scalars(select(Role).where(Role.id.in_(role_ids)))).all()
        missing = set(role_ids) - {role.id for role in roles}
        if missing:
            raise NotFoundError(ErrorCode.ROLES_NOT_FOUND)

        user.roles = list(roles)
        await self._bump_permissions_version([user_id])
        await self._session.commit()
        await redis_service.delete_cache(f"permissions_version:{user_id}")
        return await self._session.scalar(select(User).options(selectinload(User.roles)).where(User.id == user_id))

    async def _bump_permissions_version_by_role(self, role_id: UUID):
        result = await self._session.execute(
            update(User)
            .where(User.id.in_(select(user_roles.c.user_id).where(user_roles.c.role_id == role_id).scalar_subquery()))
            .values(permissions_version=User.permissions_version + 1)
            .returning(User.id)
        )
        return result.scalars().all()

    async def _bump_permissions_version(self, user_ids: Sequence[UUID]) -> None:
        if not user_ids:
            return
        await self._session.execute(update(User).where(User.id.in_(user_ids)).values(permissions_version=User.permissions_version + 1))
