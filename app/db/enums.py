from enum import StrEnum


class Gender(StrEnum):
    male = "male"
    female = "female"
    unknown = "unknown"


class TokenType(StrEnum):
    access = "access"
    refresh = "refresh"
