import anthropic
from anthropic.types import Message, MessageParam

from app.core.config import get_anthropic_config
from app.core.prompts import SYSTEM_PROMPT
from app.core.prompts.system_prompt import ASSISTANT_PREVIOUS_SUMMARY_TEMPLATE, SUMMARY_PROMPT, TITLE_PROMPT
from app.core.tools.definitions import TOOL_DEFINITIONS
from app.db import MessageRole

client = anthropic.AsyncAnthropic(api_key=get_anthropic_config().ANTHROPIC_API_KEY)


def _first_text(response: Message) -> str:
    return next((block.text for block in response.content if block.type == "text"), "").strip()


async def generate_title(first_message: str) -> str:
    response = await client.messages.create(
        model=get_anthropic_config().ANTHROPIC_MODEL,
        max_tokens=get_anthropic_config().ANTHROPIC_TITLE_MAX_TOKEN,
        system=TITLE_PROMPT,
        messages=[{"role": MessageRole.user, "content": first_message}],
    )
    return _first_text(response)[:255]


async def generate_summary(previous_summary: str | None, new_transcript: str) -> str:
    if previous_summary:
        content = ASSISTANT_PREVIOUS_SUMMARY_TEMPLATE.format(previous_summary=previous_summary, new_transcript=new_transcript)
    else:
        content = new_transcript
    response = await client.messages.create(
        model=get_anthropic_config().ANTHROPIC_MODEL,
        max_tokens=get_anthropic_config().ANTHROPIC_SUMMERY_MAX_TOKEN,
        system=SUMMARY_PROMPT,
        messages=[{"role": MessageRole.user, "content": content}],
    )
    return _first_text(response)


def stream(messages: list[MessageParam]):
    return client.messages.stream(
        model=get_anthropic_config().ANTHROPIC_MODEL,
        max_tokens=get_anthropic_config().ANTHROPIC_MAX_TOKEN,
        temperature=get_anthropic_config().ANTHROPIC_TEMPERATURE,
        top_k=get_anthropic_config().ANTHROPIC_TOP_K,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=TOOL_DEFINITIONS,
    )
