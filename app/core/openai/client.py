import base64

import httpx

from app.core.config import get_image_config
from app.core.exceptions import ImageGenerationUnavailableError

OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
TIMEOUT = 60.0


async def get_image_from_text(prompt: str) -> bytes:
    config = get_image_config()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                OPENAI_IMAGES_URL,
                headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
                json={"model": config.OPENAI_IMAGE_MODEL, "prompt": prompt, "n": 1, "size": "1024x1024"},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ImageGenerationUnavailableError() from exc
    try:
        return base64.b64decode(response.json()["data"][0]["b64_json"])
    except (ValueError, KeyError, IndexError, TypeError) as exc:  # ValueError also covers bad JSON and bad base64
        raise ImageGenerationUnavailableError() from exc
