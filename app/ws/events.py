from typing import Any

from pydantic import ValidationError

from app.core.exceptions import CustomError, NotFoundError
from app.db.session import AsyncSessionLocal
from app.services.chat_session_service import ChatSessionService
from app.ws.auth import get_current_principal_ws
from app.ws.rooms import get_chat_session_room
from app.ws.schemas import ChatSessionRoomPayload
from app.ws.server import sio


@sio.event
async def connect(sid: str, _: dict, auth: dict | None) -> None:
    token = (auth or {}).get("token")
    if not token:
        raise ConnectionRefusedError("missing token")

    async with AsyncSessionLocal() as session:
        try:
            principal = await get_current_principal_ws(token, session)
        except CustomError as exc:
            raise ConnectionRefusedError(exc.detail) from exc

    await sio.save_session(sid, {"user_id": principal.user_id, "is_superuser": principal.is_superuser})


@sio.event
async def join_chat_session(sid: str, data: dict[str, Any]) -> None:
    try:
        payload = ChatSessionRoomPayload.model_validate(data)
    except ValidationError:
        raise ConnectionRefusedError(f"Not valid payload {data}")

    ws_session = await sio.get_session(sid)

    async with AsyncSessionLocal() as session:
        try:
            chat_session = await ChatSessionService(session).get_session(payload.session_id)
        except NotFoundError:
            raise ConnectionRefusedError(f"Not found chat session {payload.session_id}")

    if chat_session.user_id != ws_session["user_id"]:
        raise ConnectionRefusedError(f"Not allowed to join chat session {payload.session_id}")

    await sio.enter_room(sid, get_chat_session_room(payload.session_id))


@sio.event
async def leave_chat_session(sid: str, data: dict[str, Any]) -> None:
    try:
        payload = ChatSessionRoomPayload.model_validate(data)
    except ValidationError:
        raise ConnectionRefusedError(f"Not valid payload {data}")

    await sio.leave_room(sid, get_chat_session_room(payload.session_id))
