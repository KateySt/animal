import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.db import Gender


class HealthLogCreate(BaseModel):
    procedure_name: str
    examination_findings: str | None = None


class HealthLogInternalCreate(BaseModel):
    animal_id: uuid.UUID
    procedure_name: str
    examination_findings: str | None = None


class HealthLogUpdate(BaseModel):
    procedure_name: str | None = None
    examination_findings: str | None = None


class HealthLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    animal_id: uuid.UUID
    procedure_name: str
    examination_findings: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class AnimalCreate(BaseModel):
    name: str
    gender: Gender
    birth_date: datetime.date
    caretaker_notes: str | None = None
    health_logs: list[HealthLogCreate] = Field(min_length=1)


class AnimalUpdate(BaseModel):
    name: str | None = None
    gender: Gender | None = None
    birth_date: datetime.date | None = None
    caretaker_notes: str | None = None


class AnimalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    gender: Gender
    birth_date: datetime.date
    caretaker_notes: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    health_logs: list[HealthLogRead] = []
