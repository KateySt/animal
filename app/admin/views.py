from starlette.requests import Request
from starlette_admin import PasswordField
from starlette_admin.contrib.sqla import ModelView

from app.core.security import hash_password
from app.db.models import ChatDocument, ChatSession, User
from app.services.document_purger import document_purger


class ResourceAdmin(ModelView):
    fields = ["id", "name", "description", "permissions", "created_at", "updated_at"]
    searchable_fields = ["name"]
    sortable_fields = ["id", "name", "created_at"]
    fields_default_sort = [("created_at", True)]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]


class PermissionAdmin(ModelView):
    fields = ["id", "resource", "action", "created_at", "updated_at"]
    sortable_fields = ["id", "action", "created_at"]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]


class RoleAdmin(ModelView):
    fields = ["id", "name", "description", "permissions", "created_at", "updated_at"]
    searchable_fields = ["name"]
    sortable_fields = ["id", "name", "created_at"]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]


class AnimalAdmin(ModelView):
    fields = ["id", "gender", "birth_date", "owner", "health_logs", "created_at", "updated_at"]
    exclude_fields_from_list = ["health_logs"]
    searchable_fields = ["gender"]
    sortable_fields = ["gender", "birth_date", "created_at"]
    fields_default_sort = [("created_at", True)]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]


class HealthLogAdmin(ModelView):
    fields = ["id", "animal", "invoices", "created_at", "updated_at"]
    exclude_fields_from_list = ["invoices"]
    sortable_fields = ["created_at"]
    fields_default_sort = [("created_at", True)]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]


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
    exporters = ["csv", "xlsx", "json"]


class ChatSessionAdmin(ModelView):
    async def before_delete(self, request: Request, obj: ChatSession) -> None:
        await document_purger.purge_sessions(request.state.session, [obj.id])

    fields = ["id", "user", "title", "summary", "last_summarized_message_id", "messages", "created_at", "updated_at"]
    exclude_fields_from_list = ["messages", "summary"]
    searchable_fields = ["title"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]


class ChatMessageAdmin(ModelView):
    fields = ["id", "session", "role", "content", "created_at", "updated_at"]
    exclude_fields_from_list = ["content"]
    sortable_fields = ["role", "created_at"]
    fields_default_sort = [("created_at", True)]


class ChatDocumentAdmin(ModelView):
    async def before_delete(self, request: Request, obj: ChatDocument) -> None:
        await document_purger.purge([obj])

    fields = [
        "id",
        "chat_session",
        "filename",
        "content_type",
        "size_bytes",
        "storage_key",
        "status",
        "created_at",
        "updated_at",
    ]
    exclude_fields_from_list = ["storage_key"]
    searchable_fields = ["filename"]
    sortable_fields = ["filename", "status", "size_bytes", "created_at"]
    fields_default_sort = [("created_at", True)]


class OAuthAccountAdmin(ModelView):
    fields = ["id", "user_id", "oauth_name", "account_id", "account_email", "created_at", "updated_at"]
    searchable_fields = ["account_email", "oauth_name"]
    sortable_fields = ["oauth_name", "account_email", "created_at"]
    fields_default_sort = [("created_at", True)]


class UserAdmin(ModelView):
    async def before_delete(self, request: Request, obj: User) -> None:
        await document_purger.purge_user(request.state.session, obj.id)

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
    exporters = ["csv", "xlsx", "json"]

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
