import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db import Gender
from app.schemas.animal import AnimalTranslationRead, HealthLogTranslationRead


class ChatSessionUpdate(BaseModel):
    title: str


class GenerateImageRequest(BaseModel):
    description: str = Field(..., description="Description of the image to generate", min_length=1, max_length=500)


class GenerateImageResponse(BaseModel):
    messages: list[dict[str, Any]]


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    summary: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ChatSessionReadWithMessages(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    summary: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    ui_messages: list[dict[str, Any]]


class ChatSessionListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sessions: list[ChatSessionRead]


class AnimalToolData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    translations: list[AnimalTranslationRead] = []
    gender: Gender
    birth_date: datetime.date


class HealthLogToolData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    translations: list[HealthLogTranslationRead] = []


class InvoiceToolData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    currency: str
    status: str | None
    amount: float
    animal: AnimalToolData
    health_log: list[HealthLogToolData]
