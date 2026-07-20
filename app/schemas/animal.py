import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.db import Gender
from app.db.models.animal import Animal
from app.db.models.health_log import HealthLog


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

    def to_animal(self) -> Animal:
        return Animal(
            name=self.name,
            gender=self.gender,
            birth_date=self.birth_date,
            caretaker_notes=self.caretaker_notes,
        )

    def to_health_logs(self, animal_id: uuid.UUID) -> list[HealthLog]:
        return [
            HealthLog(
                animal_id=animal_id,
                procedure_name=health_log.procedure_name,
                examination_findings=health_log.examination_findings,
            )
            for health_log in self.health_logs
        ]


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
