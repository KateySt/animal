import json
from collections.abc import Iterable
from typing import Any

from app.db import MessageRole


def serialize_content_block(block: Any) -> dict:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return {"type": block.type}


def serialize_transcript(rows: Iterable[tuple[MessageRole, Any]]) -> str:
    return "\n".join(f"{role}: {content if isinstance(content, str) else json.dumps(content)}" for role, content in rows)
