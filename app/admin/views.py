from fastapi_users.password import PasswordHelper
from starlette.requests import Request
from starlette_admin import PasswordField
from starlette_admin.contrib.sqla import ModelView


class AnimalAdmin(ModelView):
    searchable_fields = ["name"]


class HealthLogAdmin(ModelView):
    searchable_fields = ["procedure_name"]


class UserAdmin(ModelView):
    fields = [
        "id",
        "email",
        PasswordField("password", label="Password", required=False, help_text="Leave empty to keep current password"),
        "is_active",
        "is_verified",
        "is_superuser",
        "created_at",
        "updated_at",
    ]
    password_helper = PasswordHelper()

    exclude_fields_from_list = ["password", "hashed_password", "oauth_accounts"]
    exclude_fields_from_detail = ["password", "hashed_password"]

    searchable_fields = ["email"]
    sortable_fields = ["email", "is_active", "is_verified", "is_superuser", "created_at"]
    fields_default_sort = [("created_at", True)]

    async def before_create(self, request: Request, data: dict, obj: object) -> None:
        password = data.pop("password", None)
        if not password:
            raise ValueError("Password is required when creating a user")
        obj.hashed_password = self.password_helper.hash(password)

    async def before_edit(self, request: Request, data: dict, obj: object) -> None:
        password = data.pop("password", None)
        if password:
            obj.hashed_password = self.password_helper.hash(password)
