from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import aclosing
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.anthropic import to_ui_history
from app.core.blob import public_storage
from app.core.exceptions import CustomError, ImageGenerationUnavailableError
from app.core.openai import ImageEvent, ImageGenerator, ImagePartial
from app.db import MessageRole
from app.db.models.user import User
from app.schemas.chat import GenerateImageResponse, ImagePartialEvent, ImageStreamError, ImageStreamEvent
from app.services.chat_session_service import ChatSessionService


class ImageService:
    def __init__(self, session: AsyncSession, session_service: ChatSessionService, generator: ImageGenerator) -> None:
        self._session = session
        self._session_service = session_service
        self._generator = generator

    async def start(self, session_id: UUID, description: str, user: User) -> "ImageGeneration":
        chat_session = await self._session_service.get_session(session_id)
        self._session_service.check_session_owner(chat_session.user_id, user)
        await self._session.commit()
        stream = await self._generator.open_stream(description)
        return ImageGeneration(self, session_id, description, stream)

    @property
    def media_type(self) -> str:
        return self._generator.media_type

    async def store(self, session_id: UUID, description: str, image_bytes: bytes) -> GenerateImageResponse:
        extension = self.media_type.split("/")[1]
        filename = f"{uuid4().hex}.{extension}"
        object_name = f"chat-images/{session_id}/{filename}"
        await public_storage.upload_file(object_name, image_bytes, self.media_type)
        url = public_storage.public_url(object_name)

        assistant_content = [
            {"type": "text", "text": "Generated image"},
            {"type": "file", "media_type": self.media_type, "url": url, "filename": filename},
        ]

        rows = [(MessageRole.user, description), (MessageRole.assistant, assistant_content)]
        await self._session_service.create_messages(session_id, rows)
        return GenerateImageResponse(messages=to_ui_history(rows))


class ImageGeneration:
    def __init__(self, service: ImageService, session_id: UUID, description: str, stream: AsyncGenerator[ImageEvent, None]) -> None:
        self._service = service
        self._session_id = session_id
        self._description = description
        self._stream = stream

    async def events(self) -> AsyncIterator[ImageStreamEvent]:
        try:
            async with aclosing(self._stream) as stream:
                async for event in stream:
                    if isinstance(event, ImagePartial):
                        yield ImagePartialEvent(index=event.index, b64=event.b64, media_type=self._service.media_type)
                        continue
                    response = await self._service.store(self._session_id, self._description, event.data)
                    yield response
                    return
            raise ImageGenerationUnavailableError()
        except CustomError as exc:
            yield ImageStreamError(detail=exc.detail, error_code=exc.error_code)
