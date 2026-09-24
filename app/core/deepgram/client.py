import httpx

from app.core.config import get_speech_config
from app.core.error_codes import ErrorCode
from app.core.exceptions import BadRequestError

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"

TIMEOUT = 30.0


async def get_text_from_audio(audio_bytes: bytes) -> dict:
    config = get_speech_config()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                DEEPGRAM_URL,
                headers={"Authorization": f"Token {config.DEEPGRAM_API_KEY}"},
                params={"model": config.DEEPGRAM_MODEL, "smart_format": "true"},
                content=audio_bytes,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise BadRequestError(ErrorCode.STT_PROVIDER_ERROR) from exc
    return response.json()
