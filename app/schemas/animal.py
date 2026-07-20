import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.db import Gender


class HealthLogCreate(BaseModel):
    procedure_name: str
    examination_findings: str | None = None


class HealthLogResponse(BaseModel):
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


class AnimalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    gender: Gender
    birth_date: datetime.date
    caretaker_notes: str | None
    age: int
    health_logs: list[HealthLogResponse]
    created_at: datetime.datetime
    updated_at: datetime.datetime
