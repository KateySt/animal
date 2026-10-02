from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat_session_service import ChatSessionService


def get_chat_session_service(session: AsyncSession) -> ChatSessionService:
    return ChatSessionService(session)
