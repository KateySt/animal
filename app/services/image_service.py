from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.anthropic import to_ui_history
from app.core.openai.client import get_image_from_text
from app.db import MessageRole
from app.db.models.user import User
from app.schemas.chat import GenerateImageResponse
from app.services.chat_session_service import ChatSessionService
from app.services.minio_service import minio_service


class ImageService:
    def __init__(self, session: AsyncSession, session_service: ChatSessionService) -> None:
        self._session = session
        self._session_service = session_service

    async def generate_and_store(self, session_id: UUID, description: str, user: User) -> GenerateImageResponse:
        chat_session = await self._session_service.get_session(session_id)
        self._session_service.check_session_owner(chat_session.user_id, user)

        image_bytes = await get_image_from_text(description)
        filename = f"{uuid4().hex}.png"
        url = await minio_service.upload_file(f"chat-images/{session_id}/{filename}", image_bytes, "image/png")

        assistant_content = [
            {"type": "text", "text": "Generated image"},
            {"type": "file", "media_type": "image/png", "url": url, "filename": filename},
        ]

        await self._session_service.create_message(session_id, MessageRole.user, description)
        await self._session_service.create_message(session_id, MessageRole.assistant, assistant_content)

        rows = [(MessageRole.user, description), (MessageRole.assistant, assistant_content)]
        return GenerateImageResponse(messages=to_ui_history(rows))
