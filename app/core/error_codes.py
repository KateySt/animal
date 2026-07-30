from enum import Enum


class ErrorCode(Enum):
    def __new__(cls, code: str, message: str):
        obj = object.__new__(cls)
        obj._value_ = code
        obj._message = message
        return obj

    @property
    def code(self) -> str:
        return self._value_

    @property
    def message(self) -> str:
        return self._message

    # Auth
    NOT_AUTHENTICATED = ("not_authenticated", "Not authenticated")
    INVALID_TOKEN = ("invalid_token", "Invalid or expired token")
    TOKEN_INVALIDATED = ("token_invalidated", "Token invalidated, please refresh")
    INVALID_CREDENTIALS = ("invalid_credentials", "Invalid email or password")
    REFRESH_TOKEN_EXPIRED = ("refresh_token_expired", "Refresh token expired")
    INVALID_REFRESH_TOKEN = ("invalid_refresh_token", "Invalid refresh token")
    REFRESH_TOKEN_REUSE = ("refresh_token_reuse", "Refresh token reuse detected, all sessions revoked")
    INACTIVE_USER = ("inactive_user", "Inactive user")
    GOOGLE_EMAIL_ERROR = ("google_email_error", "Google account has problem with email")

    # Authorization
    MISSING_SCOPE = ("missing_scope", "Missing required scope")
    MISSING_ROLE = ("missing_role", "Missing required role")
    SUPERUSER_REQUIRED = ("superuser_required", "Superuser access required")
    FORBIDDEN = ("forbidden", "Access denied")

    # Animal
    ANIMAL_NOT_FOUND = ("animal_not_found", "Animal not found")

    # Health Log
    HEALTH_LOG_NOT_FOUND = ("health_log_not_found", "Health log not found")

    # Invoice
    INVOICE_NOT_FOUND = ("invoice_not_found", "Invoice not found")
    INVOICE_ALREADY_PROCESSING = ("invoice_already_processing", "Invoice payment is already being processed")
    INVOICE_ALREADY_FINALIZED = ("invoice_already_finalized", "Invoice is already finalized")
    INVOICE_WRONG_OWNER = ("invoice_wrong_owner", "Not your invoice")
    INVOICE_MISSING_SIGNATURE = ("invoice_missing_signature", "Missing signature header")
    INVOICE_INVALID_SIGNATURE = ("invoice_invalid_signature", "Invalid signature")

    # User
    USER_NOT_FOUND = ("user_not_found", "User not found")
    USER_ALREADY_EXISTS = ("user_already_exists", "A user with this email already exists")

    # Role
    ROLE_NOT_FOUND = ("role_not_found", "Role not found")
    ROLE_ALREADY_EXISTS = ("role_already_exists", "Role already exists")
    ROLES_NOT_FOUND = ("roles_not_found", "One or more roles not found")

    # Permission
    PERMISSION_NOT_FOUND = ("permission_not_found", "Permission not found")
    PERMISSION_ALREADY_EXISTS = ("permission_already_exists", "Permission already exists")
    PERMISSIONS_NOT_FOUND = ("permissions_not_found", "One or more permissions not found")

    # Resource
    RESOURCE_NOT_FOUND = ("resource_not_found", "Resource not found")
    RESOURCE_ALREADY_EXISTS = ("resource_already_exists", "Resource already exists")
    RESOURCE_HAS_PERMISSIONS = ("resource_has_permissions", "Cannot delete resource with existing permissions. Delete permissions first.")

    # Chat
    CHAT_NOT_FOUND = ("chat_not_found", "Chat not found")
    CHAT_SESSION_NOT_FOUND = ("chat_session_not_found", "Chat session not found")
    CHAT_STREAMING_ERROR = ("chat_streaming_error", "Failed to stream chat response")
    CHAT_OWNER_NOT_MATCH = ("chat_owner_not_match", "Not your chat session")
