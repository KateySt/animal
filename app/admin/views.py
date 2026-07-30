from starlette.requests import Request
from starlette_admin import PasswordField
from starlette_admin.contrib.sqla import ModelView

from app.core.security import hash_password


class ResourceAdmin(ModelView):
    searchable_fields = ["name"]
    sortable_fields = ["id", "name", "created_at"]


class PermissionAdmin(ModelView):
    fields = ["id", "resource", "action"]
    sortable_fields = ["id", "action", "created_at"]


class RoleAdmin(ModelView):
    fields = ["id", "name", "description", "permissions"]
    searchable_fields = ["name"]
    sortable_fields = ["id", "name", "created_at"]


class AnimalAdmin(ModelView):
    searchable_fields = ["name"]


class HealthLogAdmin(ModelView):
    searchable_fields = ["procedure_name"]


class InvoiceAdmin(ModelView):
    fields = ["id", "user", "animal", "health_logs", "amount_in_cents", "status", "stripe_payment_intent_id", "created_at", "updated_at"]
    exclude_fields_from_list = ["health_logs"]
    sortable_fields = ["status", "amount_in_cents", "created_at"]
    fields_default_sort = [("created_at", True)]


class UserAdmin(ModelView):
    fields = [
        "id",
        "email",
        PasswordField("password", label="Password", required=False, help_text="Leave empty to keep current password"),
        "roles",
        "is_active",
        "is_verified",
        "is_superuser",
        "created_at",
        "updated_at",
    ]

    exclude_fields_from_list = ["password", "hashed_password", "oauth_accounts"]
    exclude_fields_from_detail = ["password", "hashed_password"]

    searchable_fields = ["email"]
    sortable_fields = ["email", "is_active", "is_verified", "is_superuser", "created_at"]
    fields_default_sort = [("created_at", True)]

    async def before_create(self, request: Request, data: dict, obj: object) -> None:
        password = data.pop("password", None)
        if not password:
            raise ValueError("Password is required when creating a user")
        obj.hashed_password = hash_password(password)

    async def before_edit(self, request: Request, data: dict, obj: object) -> None:
        password = data.pop("password", None)
        if password:
            obj.hashed_password = hash_password(password)
