from enum import StrEnum


class Gender(StrEnum):
    male = "male"
    female = "female"
    unknown = "unknown"


class Policy(StrEnum):
    read = "read"
    create = "create"
    update = "update"
    delete = "delete"


class Role(StrEnum):
    user = "user"
    admin = "admin"
    staff = "staff"
