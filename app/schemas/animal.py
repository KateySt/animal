import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db import Gender
from app.db.enums import Locale


# to extend
class TranslationValidation(BaseModel):
    @model_validator(mode="after")
    def must_have_english(self):
        if not any(translation.locale == Locale.en for translation in self.translations):
            raise ValueError("English translation ('en') is required")
        return self


class AnimalTranslationCreate(BaseModel):
    locale: Locale
    name: str = Field(max_length=100)
    caretaker_notes: str | None = Field(None, max_length=255)


class AnimalTranslationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    locale: Locale
    name: str
    caretaker_notes: str | None


class HealthLogTranslationCreate(BaseModel):
    locale: Locale
    procedure_name: str = Field(max_length=100)
    examination_findings: str | None = Field(None, max_length=255)


class HealthLogTranslationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    locale: Locale
    procedure_name: str
    examination_findings: str | None


class HealthLogCreate(TranslationValidation):
    translations: list[HealthLogTranslationCreate] = Field(min_length=1)


class HealthLogInternalCreate(HealthLogCreate):
    animal_id: uuid.UUID


class HealthLogUpdate(BaseModel):
    translations: list[HealthLogTranslationCreate] | None = None


class HealthLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    animal_id: uuid.UUID
    translations: list[HealthLogTranslationRead] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_validator("translations", mode="before")
    @classmethod
    def coerce_none_to_list(cls, value):
        return value if value is not None else []


class AnimalCreate(TranslationValidation):
    owner_id: uuid.UUID
    gender: Gender
    birth_date: datetime.date
    translations: list[AnimalTranslationCreate] = Field(min_length=1)
    health_logs: list[HealthLogCreate] = Field(min_length=1)


class AnimalUpdate(BaseModel):
    gender: Gender | None = None
    birth_date: datetime.date | None = None
    translations: list[AnimalTranslationCreate] | None = None


class AnimalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    gender: Gender
    birth_date: datetime.date
    translations: list[AnimalTranslationRead] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime
    health_logs: list[HealthLogRead] = []

    @field_validator("translations", "health_logs", mode="before")
    @classmethod
    def coerce_none_to_list(cls, value):
        return value if value is not None else []
