from datetime import date

from livekit.agents import FunctionTool, function_tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import InvoiceStatus
from app.db.models.user import User
from app.services.ai_service import get_invoices_tool


def build_invoices_function_tool(session: AsyncSession, user: User) -> FunctionTool:
    @function_tool
    async def get_invoices(
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
        return await get_invoices_tool(session, user, start_date, end_date, status)

    return get_invoices
