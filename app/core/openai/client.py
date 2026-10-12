import base64
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import openai
from openai import AsyncOpenAI

from app.core.config import ImageConfig, get_image_config
from app.core.exceptions import ImageGenerationUnavailableError, ImagePromptRejectedError


@dataclass(frozen=True)
class ImagePartial:
    index: int
    b64: str


@dataclass(frozen=True)
class ImageCompleted:
    data: bytes


ImageEvent = ImagePartial | ImageCompleted


class ImageGenerator:
    def __init__(self, client: AsyncOpenAI, config: ImageConfig) -> None:
        self._client = client
        self._config = config

    @property
    def media_type(self) -> str:
        return f"image/{self._config.OPENAI_IMAGE_FORMAT}"

    async def open_stream(self, prompt: str) -> AsyncGenerator[ImageEvent, None]:
        config = self._config
        try:
            stream = await self._client.images.generate(
                model=config.OPENAI_IMAGE_MODEL,
                prompt=prompt,
                n=1,
                size=config.OPENAI_IMAGE_SIZE,
                quality=config.OPENAI_IMAGE_QUALITY,
                output_format=config.OPENAI_IMAGE_FORMAT,
                output_compression=config.OPENAI_IMAGE_COMPRESSION,
                partial_images=config.OPENAI_IMAGE_PARTIALS,
                stream=True,
            )
        except openai.BadRequestError as exc:
            if exc.code == "moderation_blocked":
                raise ImagePromptRejectedError() from exc
            raise ImageGenerationUnavailableError() from exc
        except openai.APIError as exc:
            raise ImageGenerationUnavailableError() from exc
        return self._events(stream)

    async def _events(self, stream: openai.AsyncStream) -> AsyncGenerator[ImageEvent, None]:
        try:
            async for event in stream:
                if event.type == "image_generation.partial_image":
                    yield ImagePartial(event.partial_image_index, event.b64_json)
                elif event.type == "image_generation.completed":
                    yield ImageCompleted(base64.b64decode(event.b64_json))
        except openai.APIError as exc:
            if exc.code == "moderation_blocked":
                raise ImagePromptRejectedError() from exc
            raise ImageGenerationUnavailableError() from exc
        except ValueError as exc:
            raise ImageGenerationUnavailableError() from exc
        finally:
            await stream.close()

    async def close(self) -> None:
        await self._client.close()


def _build_image_generator() -> ImageGenerator:
    config = get_image_config()
    client = AsyncOpenAI(
        api_key=config.OPENAI_API_KEY.get_secret_value(),
        timeout=config.OPENAI_TIMEOUT_SECONDS,
        max_retries=config.OPENAI_MAX_RETRIES,
    )
    return ImageGenerator(client, config)


image_generator = _build_image_generator()
