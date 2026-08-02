from collections.abc import Sequence
from typing import Any
from uuid import UUID

from anthropic.types import MessageParam
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import ValidationError, get_anthropic_config
from app.core.error_codes import ErrorCode
from app.core.exceptions import NotFoundError
from app.core.prompts.system_prompt import ASSISTANT_SUMMARY_TEMPLATE, SUMMARY_TEMPLATE
from app.db import MessageRole
from app.db.models import ChatMessage, ChatSession
from app.db.models.user import User


class ChatSessionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(self, user: User) -> ChatSession:
        new_session = ChatSession(user_id=user.id, messages=[])
        self._session.add(new_session)
        await self._session.commit()
        await self._session.refresh(new_session)
        return new_session

    async def get_user_sessions(self, user: User) -> Sequence[ChatSession]:
        result = await self._session.execute(select(ChatSession).where(ChatSession.user_id == user.id))
        return result.scalars().all()

    async def get_session_with_messages(self, session_id: UUID) -> ChatSession:
        result = await self._session.execute(
            select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages)))
        chat_session = result.scalar_one_or_none()
        if chat_session is None:
            raise NotFoundError(ErrorCode.CHAT_SESSION_NOT_FOUND)
        return chat_session

    async def get_session(self, session_id: UUID) -> ChatSession:
        result = await self._session.execute(select(ChatSession).where(ChatSession.id == session_id))
        chat_session = result.scalar_one_or_none()
        if chat_session is None:
            raise NotFoundError(ErrorCode.CHAT_SESSION_NOT_FOUND)
        return chat_session

    async def get_messages_for_anthropic(self, session_id: UUID, summary: str | None = None) -> list[MessageParam]:
        rows = await self._session.execute(
            select(ChatMessage.role, ChatMessage.content)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(get_anthropic_config().RECENT_WINDOW)
        )
        recent = list(reversed([MessageParam(role=role, content=content) for role, content in rows]))
        if summary:
            prefix = [
                MessageParam(role=MessageRole.user, content=SUMMARY_TEMPLATE.format(summary=summary)),
                MessageParam(role=MessageRole.assistant, content=ASSISTANT_SUMMARY_TEMPLATE),
            ]
            return prefix + recent
        return recent

    async def count_user_messages(self, session_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .where(ChatMessage.session_id == session_id)
            .where(ChatMessage.role == MessageRole.user)
            .where(ChatMessage.is_tool == False)
        )
        return result.scalar_one()

    async def get_messages_since_summary(self, session_id: UUID, last_summarized_message_id: UUID | None) -> list[
        tuple[MessageRole, Any]]:
        query = (
            select(ChatMessage.role, ChatMessage.content)
            .where(ChatMessage.session_id == session_id)
            .where(ChatMessage.is_tool == False)
            .order_by(ChatMessage.created_at.asc())
        )
        if last_summarized_message_id is not None:
            boundary = select(ChatMessage.created_at).where(
                ChatMessage.id == last_summarized_message_id).scalar_subquery()
            query = query.where(ChatMessage.created_at > boundary)
        rows = await self._session.execute(query)
        return [(role, content) for role, content in rows]

    async def get_last_message_id(self, session_id: UUID) -> UUID | None:
        result = await self._session.execute(
            select(ChatMessage.id)
            .where(ChatMessage.session_id == session_id)
            .where(ChatMessage.is_tool == False)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def set_summary(self, chat_session: ChatSession, summary: str,
                          last_summarized_message_id: UUID | None) -> None:
        chat_session.summary = summary
        chat_session.last_summarized_message_id = last_summarized_message_id
        await self._session.commit()

    @staticmethod
    def check_session_owner(session_owner_id: UUID, user: User) -> None:
        if session_owner_id != user.id:
            raise ValidationError(ErrorCode.CHAT_OWNER_NOT_MATCH)

    async def delete_session(self, session_id: UUID, user: User) -> None:
        chat_session = await self.get_session(session_id)
        self.check_session_owner(chat_session.user_id, user)
        await self._session.delete(chat_session)
        await self._session.commit()

    async def create_message(self, session_id: UUID, role: MessageRole, content: Any, is_tool: bool = False) -> None:
        message = ChatMessage(session_id=session_id, role=role, content=content, is_tool=is_tool)
        self._session.add(message)
        await self._session.commit()

    async def count_messages(self, session_id: UUID) -> int:
        result = await self._session.execute(select(func.count()).where(ChatMessage.session_id == session_id))
        return result.scalar_one()
