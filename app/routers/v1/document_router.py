from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, status

from app.core.dependencies import get_current_user, validate_document_file
from app.db.models.user import User
from app.schemas.document import ChatDocumentListRead, ChatDocumentRead
from app.services import get_document_service
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/{session_id}/documents", response_model=ChatDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
        session_id: UUID,
        file: UploadFile = Depends(validate_document_file),
        service: DocumentService = Depends(get_document_service),
        user: User = Depends(get_current_user),
) -> ChatDocumentRead:
    document = await service.upload_document(session_id, user, file)
    return ChatDocumentRead.model_validate(document)


@router.get("/{session_id}/documents", response_model=ChatDocumentListRead)
async def list_documents(
        session_id: UUID,
        service: DocumentService = Depends(get_document_service),
        user: User = Depends(get_current_user),
) -> ChatDocumentListRead:
    documents = await service.list_documents(session_id, user)
    return ChatDocumentListRead(documents=[ChatDocumentRead.model_validate(document) for document in documents])


@router.delete("/{session_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
        session_id: UUID,
        document_id: UUID,
        service: DocumentService = Depends(get_document_service),
        user: User = Depends(get_current_user),
) -> None:
    await service.delete_document(session_id, document_id, user)
