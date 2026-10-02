from functools import lru_cache

import anthropic

from app.core.config import get_anthropic_config
from app.core.prompts.system_prompt import ASSISTANT_PREVIOUS_SUMMARY_TEMPLATE, SUMMARY_PROMPT, TITLE_PROMPT


@lru_cache
def get_anthropic_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=get_anthropic_config().ANTHROPIC_API_KEY)


async def _generate(system_prompt: str, user_content: str, max_tokens: int) -> str:
    config = get_anthropic_config()
    response = await get_anthropic_client().messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    block = response.content[0]
    return block.text.strip() if isinstance(block, anthropic.types.TextBlock) else ""


async def generate_title(first_message: str) -> str:
    text = await _generate(TITLE_PROMPT, first_message, get_anthropic_config().ANTHROPIC_TITLE_MAX_TOKEN)
    return text[:255]


async def generate_summary(previous_summary: str | None, new_transcript: str) -> str:
    content = (
        ASSISTANT_PREVIOUS_SUMMARY_TEMPLATE.format(previous_summary=previous_summary, new_transcript=new_transcript)
        if previous_summary
        else new_transcript
    )
    return await _generate(SUMMARY_PROMPT, content, get_anthropic_config().ANTHROPIC_SUMMERY_MAX_TOKEN)
