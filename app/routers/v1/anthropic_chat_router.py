from uuid import UUID

import ai
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.core.anthropic import to_ui_history
from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.schemas.chat import ChatSessionListRead, ChatSessionRead, ChatSessionReadWithMessages, SendMessageRequest
from app.services import get_anthropic_chat_service, get_chat_session_service
from app.services.anthropic_chat_service import AnthropicChatService
from app.services.chat_session_service import ChatSessionService

router = APIRouter()


@router.post("", response_model=ChatSessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    service: ChatSessionService = Depends(get_chat_session_service),
    user: User = Depends(get_current_user),
) -> ChatSessionRead:
    return await service.create_session(user)


@router.get("", response_model=ChatSessionListRead)
async def list_sessions(
    service: ChatSessionService = Depends(get_chat_session_service),
    user: User = Depends(get_current_user),
) -> ChatSessionListRead:
    sessions = await service.get_user_sessions(user)
    return ChatSessionListRead(sessions=sessions)


@router.get("/{session_id}", response_model=ChatSessionReadWithMessages)
async def get_session(
    session_id: UUID,
    service: ChatSessionService = Depends(get_chat_session_service),
    _: User = Depends(get_current_user),
) -> ChatSessionReadWithMessages:
    chat_session = await service.get_session_with_messages(session_id)
    return ChatSessionReadWithMessages(
        id=chat_session.id,
        title=chat_session.title,
        summary=chat_session.summary,
        created_at=chat_session.created_at,
        updated_at=chat_session.updated_at,
        ui_messages=to_ui_history([(m.role, m.content) for m in chat_session.messages]),
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    service: ChatSessionService = Depends(get_chat_session_service),
    user: User = Depends(get_current_user),
) -> None:
    await service.delete_session(session_id, user)


@router.post("/{session_id}/messages", status_code=status.HTTP_200_OK)
async def send_message(
    session_id: UUID,
    payload: SendMessageRequest,
    service: AnthropicChatService = Depends(get_anthropic_chat_service),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    return StreamingResponse(
        service.stream_response(session_id, payload.content, user),
        headers=ai.ui.ai_sdk.UI_MESSAGE_STREAM_HEADERS,
    )
