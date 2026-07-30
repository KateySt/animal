from enum import StrEnum


class Gender(StrEnum):
    male = "male"
    female = "female"
    unknown = "unknown"


class TokenType(StrEnum):
    access = "access"
    refresh = "refresh"


class Currency(StrEnum):
    usd = "usd"
    uah = "uah"


class InvoiceStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    paid = "paid"
    cancelled = "cancelled"


class Locale(StrEnum):
    en = "en"
    ru = "ru"
    uk = "uk"


class MessageRole(StrEnum):
    user = "user"
    assistant = "assistant"
