import json
from datetime import UTC, date, datetime
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.book_rag import search_documents
from app.core.exceptions import BookRagUnavailableError
from app.core.logger import log
from app.db import DocumentStatus, InvoiceStatus
from app.db.models import Animal, ChatDocument, HealthLog
from app.db.models.invoice import Invoice
from app.db.models.user import User
from app.schemas.chat import AnimalToolData, HealthLogToolData, InvoiceToolData


async def get_invoices_tool(
    session: AsyncSession,
    user: User,
    start_date: date | None = None,
    end_date: date | None = None,
    status: InvoiceStatus | None = None,
) -> str:
    now = datetime.now(UTC).date()
    start = start_date or now.replace(day=1)
    end = end_date or now

    query = (
        select(Invoice)
        .where(Invoice.user_id == user.id)
        .where(Invoice.created_at >= datetime(start.year, start.month, start.day, tzinfo=UTC))
        .where(Invoice.created_at <= datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC))
        .options(
            joinedload(Invoice.animal).options(selectinload(Animal.translations)),
            selectinload(Invoice.health_logs).options(selectinload(HealthLog.translations)),
        )
    )
    if status is not None:
        query = query.where(Invoice.status == status)

    result = await session.execute(query)
    invoices = result.scalars().all()

    items = [
        InvoiceToolData(
            status=invoice.status,
            amount=invoice.to_float(invoice.currency),
            currency=invoice.currency,
            animal=AnimalToolData(
                gender=invoice.animal.gender,
                birth_date=invoice.animal.birth_date,
                translations=invoice.animal.translations,
            ),
            health_log=[HealthLogToolData(translations=log.translations) for log in invoice.health_logs],
        ).model_dump(mode="json")
        for invoice in invoices
    ]

    return json.dumps({"invoices": items, "total": round(sum(i["amount"] for i in items), 2)})


async def get_document_statuses(session: AsyncSession, chat_session_id: UUID) -> dict[str, list[str]]:
    rows = await session.execute(
        select(ChatDocument.filename, ChatDocument.status).where(ChatDocument.chat_session_id == chat_session_id)
    )
    documents = rows.all()
    return {
        "ready_documents": [filename for filename, status in documents if status == DocumentStatus.ready],
        "processing_documents": [
            filename for filename, status in documents if status in (DocumentStatus.uploading, DocumentStatus.embedding)
        ],
        "failed_documents": [filename for filename, status in documents if status == DocumentStatus.failed],
    }


async def search_chat_documents_tool(session: AsyncSession, chat_session_id: UUID, query: str, top_k: int = 5) -> str:
    status_info = await get_document_statuses(session, chat_session_id)

    if not status_info["ready_documents"]:
        return json.dumps({"chunks": [], **status_info})

    try:
        results = await search_documents(chat_session_id, query, top_k=top_k)
    except (httpx.HTTPError, BookRagUnavailableError):
        log.exception(f"search_documents failed for chat session {chat_session_id}")
        return json.dumps({"error": "document search is temporarily unavailable", **status_info})
    return json.dumps({"chunks": results, **status_info})
