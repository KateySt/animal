from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.db import MessageRole


class AgentContextMessage(BaseModel):
    role: MessageRole
    content: Any


class AgentSessionContext(BaseModel):
    summary: str | None
    messages: list[AgentContextMessage]


class AgentMessageCreate(BaseModel):
    role: MessageRole
    content: Any
    occurred_at: datetime


class AgentDocumentStatuses(BaseModel):
    ready_documents: list[str]
    processing_documents: list[str]
    failed_documents: list[str]


class AgentDocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
