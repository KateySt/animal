from starlette.requests import Request
from starlette_admin import PasswordField
from starlette_admin.contrib.sqla import ModelView

from app.core.security import hash_password


class ResourceAdmin(ModelView):
    fields = ["id", "name", "description", "permissions", "created_at", "updated_at"]
    searchable_fields = ["name"]
    sortable_fields = ["id", "name", "created_at"]
    fields_default_sort = [("created_at", True)]


class PermissionAdmin(ModelView):
    fields = ["id", "resource", "action", "created_at", "updated_at"]
    sortable_fields = ["id", "action", "created_at"]


class RoleAdmin(ModelView):
    fields = ["id", "name", "description", "permissions", "created_at", "updated_at"]
    searchable_fields = ["name"]
    sortable_fields = ["id", "name", "created_at"]


class AnimalAdmin(ModelView):
    fields = ["id", "gender", "birth_date", "owner", "health_logs", "created_at", "updated_at"]
    exclude_fields_from_list = ["health_logs"]
    searchable_fields = ["gender"]
    sortable_fields = ["gender", "birth_date", "created_at"]
    fields_default_sort = [("created_at", True)]


class HealthLogAdmin(ModelView):
    fields = ["id", "animal", "invoices", "created_at", "updated_at"]
    exclude_fields_from_list = ["invoices"]
    sortable_fields = ["created_at"]
    fields_default_sort = [("created_at", True)]


class InvoiceAdmin(ModelView):
    fields = [
        "id",
        "user",
        "animal",
        "health_logs",
        "amount_in_cents",
        "currency",
        "status",
        "stripe_payment_intent_id",
        "created_at",
        "updated_at",
    ]
    exclude_fields_from_list = ["health_logs"]
    sortable_fields = ["status", "currency", "amount_in_cents", "created_at"]
    fields_default_sort = [("created_at", True)]


class ChatSessionAdmin(ModelView):
    fields = ["id", "user", "title", "summary", "messages", "created_at", "updated_at"]
    exclude_fields_from_list = ["messages", "summary"]
    searchable_fields = ["title"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]


class ChatMessageAdmin(ModelView):
    fields = ["id", "session", "role", "content", "is_tool", "created_at", "updated_at"]
    exclude_fields_from_list = ["content"]
    sortable_fields = ["role", "created_at"]
    fields_default_sort = [("created_at", True)]


class UserAdmin(ModelView):
    fields = [
        "id",
        "email",
        PasswordField("password", label="Password", required=False, help_text="Leave empty to keep current password"),
        "roles",
        "oauth_accounts",
        "animals",
        "is_active",
        "is_verified",
        "is_superuser",
        "permissions_version",
        "created_at",
        "updated_at",
    ]

    exclude_fields_from_list = ["password", "hashed_password", "oauth_accounts", "animals"]
    exclude_fields_from_detail = ["password", "hashed_password"]
    exclude_fields_from_create = ["permissions_version"]
    exclude_fields_from_edit = ["permissions_version"]

    searchable_fields = ["email"]
    sortable_fields = ["email", "is_active", "is_verified", "is_superuser", "permissions_version", "created_at"]
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
