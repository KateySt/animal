import os

import ai

from app.core.config import get_anthropic_config
from app.core.prompts.system_prompt import ASSISTANT_PREVIOUS_SUMMARY_TEMPLATE, SUMMARY_PROMPT, TITLE_PROMPT


def get_model() -> ai.Model:
    os.environ.setdefault("ANTHROPIC_API_KEY", get_anthropic_config().ANTHROPIC_API_KEY)
    return ai.get_model(f"anthropic:{get_anthropic_config().ANTHROPIC_MODEL}")


def inference_params(max_tokens: int) -> ai.InferenceRequestParams:
    config = get_anthropic_config()
    return ai.InferenceRequestParams(
        sampling={
            ai.TemperatureSamplerParams: ai.TemperatureSamplerParams(temperature=config.ANTHROPIC_TEMPERATURE),
            ai.TopKSamplerParams: ai.TopKSamplerParams(top_k=config.ANTHROPIC_TOP_K),
        },
        output=ai.OutputParams(max_tokens=max_tokens),
        cache=ai.CacheParams(),
    )


async def generate_title(first_message: str) -> str:
    message = await ai.experimental_generate(
        get_model(),
        [ai.system_message(TITLE_PROMPT), ai.user_message(first_message)],
        params=inference_params(get_anthropic_config().ANTHROPIC_TITLE_MAX_TOKEN),
    )
    return message.text.strip()[:255]


async def generate_summary(previous_summary: str | None, new_transcript: str) -> str:
    if previous_summary:
        content = ASSISTANT_PREVIOUS_SUMMARY_TEMPLATE.format(
            previous_summary=previous_summary, new_transcript=new_transcript
        )
    else:
        content = new_transcript
    message = await ai.experimental_generate(
        get_model(),
        [ai.system_message(SUMMARY_PROMPT), ai.user_message(content)],
        params=inference_params(get_anthropic_config().ANTHROPIC_SUMMERY_MAX_TOKEN),
    )
    return message.text.strip()
