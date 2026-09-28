import base64

import httpx
from app.core.config import get_image_config
from app.core.error_codes import ErrorCode
from app.core.exceptions import BadRequestError

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
            raise BadRequestError(ErrorCode.IMAGE_GEN_PROVIDER_ERROR) from exc
    return base64.b64decode(response.json()["data"][0]["b64_json"])
