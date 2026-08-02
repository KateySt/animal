import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.db import Gender, MessageRole
from app.schemas.animal import AnimalTranslationRead, HealthLogTranslationRead


class ChatSessionUpdate(BaseModel):
    title: str


class SendMessageRequest(BaseModel):
    content: str


class ChatMessage(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: Any
    is_tool: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


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

    messages: list[ChatMessage]


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
