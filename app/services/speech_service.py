import httpx
from app.core.config import get_speech_config
from app.core.deepgram.client import get_text_from_audio
from app.core.elevenlabs.client import get_audio_from_text
from app.core.error_codes import ErrorCode
from app.core.exceptions import BadRequestError

ALLOWED_AUDIO_CONTENT_TYPES = {"audio/webm", "audio/mp4", "audio/wav", "audio/ogg"}
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024


class SpeechService:
    async def transcribe(self, audio_bytes: bytes, content_type: str) -> str:
        if content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
            raise BadRequestError(ErrorCode.TRANSCRIBE_INVALID_TYPE)
        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            raise BadRequestError(ErrorCode.TRANSCRIBE_TOO_LARGE)

        data = await get_text_from_audio(audio_bytes)
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        if not transcript.strip():
            raise BadRequestError(ErrorCode.TRANSCRIBE_EMPTY)
        return transcript

    async def synthesize(self, text: str) -> bytes:
        return await get_audio_from_text(text)
