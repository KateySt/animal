import datetime
import uuid

from pydantic import BaseModel, ConfigDict

from app.db import DocumentStatus


class ChatDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    error_message: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ChatDocumentListRead(BaseModel):
    documents: list[ChatDocumentRead]


class DocumentStatusWebhook(BaseModel):
    status: DocumentStatus
    error: str | None = None
