import json
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.exa import get_exa_client
from app.db import InvoiceStatus
from app.db.models import Animal, HealthLog
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


async def web_search_tool(query: str, num_results: int = 5) -> str:
    client = get_exa_client()

    response = await client.search_and_contents(query, num_results=num_results, text=True)

    items = [
        {"title": result.title, "url": result.url, "published_date": result.published_date, "text": result.text}
        for result in response.results
    ]
    return json.dumps({"results": items})
