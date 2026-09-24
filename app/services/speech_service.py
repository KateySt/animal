import httpx

from app.core.config import get_speech_config
from app.core.error_codes import ErrorCode
from app.core.exceptions import BadRequestError

ALLOWED_AUDIO_CONTENT_TYPES = {"audio/webm", "audio/mp4", "audio/wav", "audio/ogg"}
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/"

TIMEOUT = 30.0


class SpeechService:
    async def transcribe(self, audio_bytes: bytes, content_type: str) -> str:
        if content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
            raise BadRequestError(ErrorCode.TRANSCRIBE_INVALID_TYPE)
        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            raise BadRequestError(ErrorCode.TRANSCRIBE_TOO_LARGE)

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

        transcript = response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
        if not transcript.strip():
            raise BadRequestError(ErrorCode.TRANSCRIBE_EMPTY)
        return transcript

    async def synthesize(self, text: str) -> bytes:
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
