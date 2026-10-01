from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionRoomPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: UUID = Field(alias="sessionId")
