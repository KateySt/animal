from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import verify_internal_token
from app.schemas.document import DocumentStatusWebhook
from app.services import get_document_service
from app.services.document_service import DocumentService

router = APIRouter(dependencies=[Depends(verify_internal_token)])


@router.post("/documents/{document_id}/status", status_code=status.HTTP_204_NO_CONTENT)
async def update_document_status(
        document_id: UUID,
        payload: DocumentStatusWebhook,
        service: DocumentService = Depends(get_document_service),
) -> None:
    await service.set_status(document_id, payload.status, payload.error)
