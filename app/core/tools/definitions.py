from enum import StrEnum

from anthropic.types import ToolParam

from app.db import InvoiceStatus


class ChatTool(StrEnum):
    GET_INVOICES = "get_invoices_tool"


TOOL_DEFINITIONS: list[ToolParam] = [
    ToolParam(
        name=ChatTool.GET_INVOICES,
        description=(
            "Retrieve the current user's invoices with linked animal and health log data. "
            "Call this whenever the user asks about: their invoices, payments, spending, costs, bills, "
            "invoice status (pending/processing/paid/cancelled), currency, or totals for a time period. "
            "Returns a JSON object with an 'invoices' array and a 'total' (sum of amounts). "
            "Each invoice includes: status, amount (float in the invoice's currency), "
            "animal (gender, birth_date, translations), and health_logs (with translations). "
            "Default date range is the current month to today — only set start_date/end_date if the user specifies a period. "
            "Only set status if the user explicitly filters by one."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Filter invoices created on or after this date (YYYY-MM-DD). Defaults to first day of current month.",
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Filter invoices created on or before this date (YYYY-MM-DD). Defaults to today.",
                },
                "status": {
                    "type": "string",
                    "enum": [str(status.value) for status in InvoiceStatus],
                    "description": "Return only invoices with this status. Omit to return all statuses.",
                },
            },
            "required": [],
        },
    ),
]
