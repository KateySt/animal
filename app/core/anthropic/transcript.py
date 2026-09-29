from collections.abc import Iterable
from typing import Any
from uuid import uuid4

from app.db import MessageRole


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return " ".join(block["text"] for block in content if block.get("type") == "text")


def serialize_transcript(rows: Iterable[tuple[MessageRole, Any]]) -> str:
    return "\n".join(f"{role}: {_content_to_text(content)}" for role, content in rows)


def to_ui_history(rows: Iterable[tuple[MessageRole, Any]]) -> list[dict[str, Any]]:
    ui_messages: list[dict[str, Any]] = []
    current_assistant: dict[str, Any] | None = None
    tool_parts_by_call_id: dict[str, dict[str, Any]] = {}

    for role, content in rows:
        if role == MessageRole.user:
            current_assistant = None
            tool_parts_by_call_id = {}
            ui_messages.append({
                "id": str(uuid4()),
                "role": "user",
                "parts": [{"type": "text", "text": _content_to_text(content)}],
            })
            continue

        if role == MessageRole.tool:
            for block in content:
                part = tool_parts_by_call_id.get(block["tool_use_id"])
                if part is not None:
                    part["state"] = "output-available"
                    part["output"] = block["content"]
            continue

        if current_assistant is None:
            current_assistant = {"id": str(uuid4()), "role": "assistant", "parts": []}
            ui_messages.append(current_assistant)

        for block in content:
            if block["type"] == "text":
                current_assistant["parts"].append({"type": "text", "text": block["text"]})
            elif block["type"] == "tool_use":
                part = {
                    "type": f"tool-{block['name']}",
                    "toolCallId": block["id"],
                    "state": "input-available",
                    "input": block["input"],
                }
                current_assistant["parts"].append(part)
                tool_parts_by_call_id[block["id"]] = part
            elif block["type"] == "file":
                current_assistant["parts"].append({
                    "type": "file",
                    "mediaType": block["media_type"],
                    "url": block.get("url"),
                    "filename": block.get("filename"),
                })

    return ui_messages
