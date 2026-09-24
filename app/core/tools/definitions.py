import json
from datetime import UTC, date, datetime

import ai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db import InvoiceStatus
from app.db.models import Animal, HealthLog
from app.db.models.invoice import Invoice
from app.db.models.user import User
from app.schemas.chat import AnimalToolData, HealthLogToolData, InvoiceToolData


# to isolate context form chat
def build_get_invoices_tool(session: AsyncSession, user: User) -> ai.AgentTool:
    @ai.tool
    async def get_invoices_tool(
        start_date: date | None = None,
        end_date: date | None = None,
        status: InvoiceStatus | None = None,
    ) -> str:
        """Retrieve the current user's invoices with linked animal and health log data.

        Call this whenever the user asks about: their invoices, payments, spending, costs, bills,
        invoice status (pending/processing/paid/cancelled), currency, or totals for a time period.
        Returns a JSON object with an 'invoices' array and a 'total' (sum of amounts).
        Each invoice includes: status, amount (float in the invoice's currency),
        animal (gender, birth_date, translations), and health_logs (with translations).
        Default date range is the current month to today — only set start_date/end_date if the user specifies a period.
        Only set status if the user explicitly filters by one.
        """
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

    return get_invoices_tool
