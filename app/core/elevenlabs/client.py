import httpx
from app.core.config import get_speech_config
from app.core.deepgram.client import get_text_from_audio
from app.core.error_codes import ErrorCode
from app.core.exceptions import BadRequestError

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/"

TIMEOUT = 30.0


async def get_audio_from_text(text: str) -> bytes:
    config = get_speech_config()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                ELEVENLABS_URL + f"{config.ELEVENLABS_VOICE_ID}",
                headers={"xi-api-key": config.ELEVENLABS_API_KEY, "Accept": "audio/mpeg"},
                json={"text": text, "model_id": config.ELEVENLABS_MODEL},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise BadRequestError(ErrorCode.TTS_PROVIDER_ERROR) from exc
    return response.content
