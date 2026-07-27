from uuid import UUID

from sqlalchemy import ScalarResult, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError, UnauthorizedError
from app.core.security import generate_refresh_token, hash_password
from app.db.models import OAuthAccount, animal_crud, oauth_account_crud, user_crud
from app.db.models.associations import role_permissions, user_roles
from app.db.models.permission import Permission
from app.db.models.resource import Resource
from app.db.models.user import User
from app.schemas.user import OAuthAccountCreate, UserCreate, UserInternal


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserInternal:
        user = await user_crud.get(self._session, schema_to_select=UserInternal, return_as_model=True, id=user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def get_by_email(self, email: str) -> UserInternal:
        user = await user_crud.get(self._session, schema_to_select=UserInternal, return_as_model=True, email=email)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def get_by_animal_id(self, animal_id: UUID) -> UserInternal:
        animal = await animal_crud.get(self._session, id=animal_id)
        if animal is None:
            raise NotFoundError("Animal not found")
        return await self.get_by_id(animal.get("owner_id"))

    async def get_by_oauth(self, oauth_name: str, account_id: str) -> UserInternal | None:
        user = await self._session.execute(
            select(User)
            .join(OAuthAccount, OAuthAccount.user_id == User.id)
            .where(OAuthAccount.oauth_name == oauth_name, OAuthAccount.account_id == account_id)
        )
        user = user.scalars().first()
        if user is None:
            return None
        return UserInternal.model_validate(user)

    async def get_by_email_or_create_with_oauth(self, email: str, account_id: str) -> UserInternal:
        user = await user_crud.get(self._session, schema_to_select=UserInternal, return_as_model=True, email=email)
        if user is None:
            created = await user_crud.create(
                self._session,
                UserCreate(email=email, hashed_password=hash_password(generate_refresh_token())),
                schema_to_select=UserInternal,
                return_as_model=True,
            )
            await oauth_account_crud.create(
                self._session,
                OAuthAccountCreate(
                    user_id=created.id,
                    oauth_name="google",
                    account_id=account_id,
                    account_email=email,
                ),
            )
            return created
        return user

    async def get_scopes(self, user_id: UUID) -> ScalarResult[str]:
        rows = await self._session.execute(
            select(func.concat(Resource.name, ":", Permission.action))
            .select_from(user_roles)
            .join(role_permissions, role_permissions.c.role_id == user_roles.c.role_id)
            .join(Permission, Permission.id == role_permissions.c.permission_id)
            .join(Resource, Resource.id == Permission.resource_id)
            .where(user_roles.c.user_id == user_id)
            .distinct()
        )
        return rows.scalars()

    @staticmethod
    def check_active(user: UserInternal) -> None:
        if not user.is_active:
            raise UnauthorizedError("Inactive user")

    async def create(self, email: str, password: str) -> UserInternal:
        existing = await user_crud.exists(self._session, email=email)
        if existing:
            raise AlreadyExistsError("A user with this email already exists")

        return await user_crud.create(
            self._session,
            UserCreate(email=email, hashed_password=hash_password(password)),
            schema_to_select=UserInternal,
            return_as_model=True,
        )
