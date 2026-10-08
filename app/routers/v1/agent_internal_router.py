from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import verify_agent_token
from app.db import InvoiceStatus, get_db_session
from app.db.models.chat_session import ChatSession
from app.schemas.agent import (
    AgentContextMessage,
    AgentDocumentSearchRequest,
    AgentDocumentStatuses,
    AgentMessageCreate,
    AgentSessionContext,
)
from app.services import ai_service, get_chat_session_service
from app.services.chat_session_service import ChatSessionService

router = APIRouter(dependencies=[Depends(verify_agent_token)])


async def get_agent_chat_session(
        session_id: UUID,
        service: ChatSessionService = Depends(get_chat_session_service),
) -> ChatSession:
    return await service.get_session_with_user(session_id)


@router.get("/sessions/{session_id}/context", response_model=AgentSessionContext)
async def get_session_context(
        chat_session: ChatSession = Depends(get_agent_chat_session),
        service: ChatSessionService = Depends(get_chat_session_service),
) -> AgentSessionContext:
    messages = await service.get_messages_for_anthropic(chat_session.id)
    return AgentSessionContext(
        summary=chat_session.summary,
        messages=[AgentContextMessage(role=role, content=content) for role, content in messages],
    )


@router.post("/sessions/{session_id}/messages", status_code=status.HTTP_204_NO_CONTENT)
async def create_session_message(
        payload: AgentMessageCreate,
        chat_session: ChatSession = Depends(get_agent_chat_session),
        service: ChatSessionService = Depends(get_chat_session_service),
) -> None:
    await service.save_agent_message(chat_session, payload.role, payload.content, payload.occurred_at)


@router.get("/sessions/{session_id}/documents/statuses", response_model=AgentDocumentStatuses)
async def get_document_statuses(
        chat_session: ChatSession = Depends(get_agent_chat_session),
        db: AsyncSession = Depends(get_db_session),
) -> AgentDocumentStatuses:
    return AgentDocumentStatuses(**await ai_service.get_document_statuses(db, chat_session.id))


@router.post("/sessions/{session_id}/documents/search")
async def search_documents(
        payload: AgentDocumentSearchRequest,
        chat_session: ChatSession = Depends(get_agent_chat_session),
        db: AsyncSession = Depends(get_db_session),
) -> Response:
    result = await ai_service.search_chat_documents_tool(db, chat_session.id, payload.query, payload.top_k)
    return Response(content=result, media_type="application/json")


@router.get("/sessions/{session_id}/invoices")
async def get_invoices(
        start_date: date | None = None,
        end_date: date | None = None,
        invoice_status: InvoiceStatus | None = Query(None, alias="status"),
        chat_session: ChatSession = Depends(get_agent_chat_session),
        db: AsyncSession = Depends(get_db_session),
) -> Response:
    result = await ai_service.get_invoices_tool(db, chat_session.user, start_date, end_date, invoice_status)
    return Response(content=result, media_type="application/json")
