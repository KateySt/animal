from uuid import UUID

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.schemas.chat import GenerateImageRequest, GenerateImageResponse
from app.services import get_image_service
from app.services.image_service import ImageService
from fastapi import APIRouter, Depends, status

router = APIRouter()


@router.post("/{session_id}/generate-image", response_model=GenerateImageResponse)
async def generate_image(
        session_id: UUID,
        payload: GenerateImageRequest,
        service: ImageService = Depends(get_image_service),
        user: User = Depends(get_current_user),
) -> GenerateImageResponse:
    return await service.generate_and_store(session_id, payload.description, user)
