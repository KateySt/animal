import json
from collections.abc import Iterable
from typing import Any

import ai

from app.core.prompts.system_prompt import ASSISTANT_SUMMARY_TEMPLATE, SUMMARY_TEMPLATE
from app.db import MessageRole


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return " ".join(block["text"] for block in content if block.get("type") == "text")


def serialize_transcript(rows: Iterable[tuple[MessageRole, Any]]) -> str:
    return "\n".join(f"{role}: {_content_to_text(content)}" for role, content in rows)


def _block_to_part(block: dict[str, Any]) -> Any:
    if block["type"] == "text":
        return ai.text_part(block["text"])
    if block["type"] == "tool_use":
        return ai.types.messages.ToolCallPart(
            tool_call_id=block["id"], tool_name=block["name"], tool_args=json.dumps(block["input"])
        )
    raise ValueError(f"Unsupported stored content block type: {block['type']!r}")


def _row_to_message(role: MessageRole, content: Any) -> Any:
    if role == MessageRole.tool:
        return ai.tool_message(
            *[ai.tool_result_part(block["tool_use_id"], result=block["content"]) for block in content]
        )
    if isinstance(content, str):
        return ai.user_message(content) if role == MessageRole.user else ai.assistant_message(content)
    return ai.message(*[_block_to_part(block) for block in content], role=role)


def to_ai_messages(rows: Iterable[tuple[MessageRole, Any]], summary: str | None = None) -> list[Any]:
    messages: list[Any] = []
    if summary:
        messages.append(ai.user_message(SUMMARY_TEMPLATE.format(summary=summary)))
        messages.append(ai.assistant_message(ASSISTANT_SUMMARY_TEMPLATE))
    messages.extend(_row_to_message(role, content) for role, content in rows)
    return messages


def to_ui_history(rows: Iterable[tuple[MessageRole, Any]]) -> list[dict[str, Any]]:
    ui_messages = ai.ui.ai_sdk.to_ui_messages(to_ai_messages(rows))
    return [message.model_dump(mode="json", by_alias=True) for message in ui_messages]


def from_ai_message(message: Any) -> Any:
    if message.role == "tool":
        return [
            {"type": "tool_result", "tool_use_id": result.tool_call_id, "content": result.result}
            for result in message.tool_results
        ]
    blocks: list[dict[str, Any]] = []
    for part in message.parts:
        if isinstance(part, ai.types.messages.TextPart):
            blocks.append({"type": "text", "text": part.text})
        elif isinstance(part, ai.types.messages.ToolCallPart):
            blocks.append(
                {"type": "tool_use", "id": part.tool_call_id, "name": part.tool_name, "input": json.loads(part.tool_args)}
            )
        else:
            raise ValueError(f"Unsupported ai message part kind: {part.kind!r}")
    return blocks
