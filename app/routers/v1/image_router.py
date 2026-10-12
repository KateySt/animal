from collections.abc import AsyncIterable
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.schemas.chat import GenerateImageRequest, GenerateImageResponse, ImagePartialEvent, ImageStreamEvent
from app.services import get_image_service
from app.services.image_service import ImageGeneration, ImageService

router = APIRouter()


async def start_image_generation(
        session_id: UUID,
        payload: GenerateImageRequest,
        service: ImageService = Depends(get_image_service),
        user: User = Depends(get_current_user),
) -> ImageGeneration:
    return await service.start(session_id, payload.description, user)


def _to_sse(event: ImageStreamEvent) -> ServerSentEvent:
    if isinstance(event, ImagePartialEvent):
        return ServerSentEvent(event="partial", data=event)
    if isinstance(event, GenerateImageResponse):
        return ServerSentEvent(event="done", data=event)
    return ServerSentEvent(event="error", data=event)


@router.post("/{session_id}/generate-image", response_class=EventSourceResponse)
async def generate_image(
        generation: ImageGeneration = Depends(start_image_generation),
) -> AsyncIterable[ServerSentEvent]:
    async for event in generation.events():
        yield _to_sse(event)
