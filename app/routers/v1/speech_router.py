from fastapi import APIRouter, Depends, Response, UploadFile

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.schemas.speech import SynthesizeRequest, TranscribeResponse
from app.services import SpeechService, get_speech_service

router = APIRouter()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile,
    service: SpeechService = Depends(get_speech_service),
    _: User = Depends(get_current_user),
) -> TranscribeResponse:
    audio_bytes = await file.read()
    transcript = await service.transcribe(audio_bytes, file.content_type or "")
    return TranscribeResponse(transcript=transcript)


@router.post("/synthesize")
async def synthesize(
    payload: SynthesizeRequest,
    service: SpeechService = Depends(get_speech_service),
    _: User = Depends(get_current_user),
) -> Response:
    audio_bytes = await service.synthesize(payload.text)
    return Response(content=audio_bytes, media_type="audio/mpeg")
