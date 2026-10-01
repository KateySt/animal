import uuid


def get_chat_session_room(session_id: uuid.UUID | str) -> str:
    return f"chat-session:{session_id}"
