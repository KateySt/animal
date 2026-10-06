from datetime import date
from uuid import UUID

from livekit.agents import FunctionTool, function_tool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.prompts import GET_INVOICES_TOOL_DESCRIPTION, SEARCH_DOCUMENTS_TOOL_DESCRIPTION, WEB_SEARCH_TOOL_DESCRIPTION
from app.db import InvoiceStatus
from app.db.models.user import User
from app.services.ai_service import get_invoices_tool, search_chat_documents_tool, web_search_tool


def build_invoices_function_tool(session: AsyncSession, user: User) -> FunctionTool:
    @function_tool(description=GET_INVOICES_TOOL_DESCRIPTION)
    async def get_invoices(
        start_date: date | None = None,
        end_date: date | None = None,
        status: InvoiceStatus | None = None,
    ) -> str:
        return await get_invoices_tool(session, user, start_date, end_date, status)

    return get_invoices


def build_web_search_function_tool() -> FunctionTool:
    @function_tool(description=WEB_SEARCH_TOOL_DESCRIPTION)
    async def web_search(query: str, num_results: int = 5) -> str:
        return await web_search_tool(query, num_results)

    return web_search


def build_search_documents_function_tool(
    session_factory: async_sessionmaker[AsyncSession], chat_session_id: UUID
) -> FunctionTool:
    @function_tool(description=SEARCH_DOCUMENTS_TOOL_DESCRIPTION)
    async def search_documents(query: str, top_k: int = 5) -> str:
        async with session_factory() as session:
            return await search_chat_documents_tool(session, chat_session_id, query, top_k)

    return search_documents
