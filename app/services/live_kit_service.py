from datetime import timedelta
from uuid import UUID, uuid4

from livekit.api import (
    AccessToken,
    RoomAgentDispatch,
    RoomConfiguration,
    VideoGrants,
)

from app.core.config import get_livekit_config
from app.db.models.user import User
from app.schemas.livekit import LiveKitTokenResponse


async def create_live_kit_token(session_id: UUID, user: User) -> LiveKitTokenResponse:
    config = get_livekit_config()
    room_name = f"chat-{session_id}-{uuid4().hex[:8]}"

    token = (
        AccessToken(config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)
        .with_identity(str(user.id))
        .with_ttl(timedelta(minutes=5))
        .with_grants(VideoGrants(room_join=True, room=room_name))
        .with_room_config(
            RoomConfiguration(
                agents=[RoomAgentDispatch(agent_name=config.LIVEKIT_AGENT_NAME, metadata=str(session_id))],
                departure_timeout=1,
            )
        )
        .to_jwt()
    )

    return LiveKitTokenResponse(url=config.LIVEKIT_URL, token=token, room_name=room_name)
