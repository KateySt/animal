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
    paid = "paid"
    cancelled = "cancelled"
