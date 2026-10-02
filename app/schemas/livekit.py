from pydantic import BaseModel


class LiveKitTokenResponse(BaseModel):
    url: str
    token: str
    room_name: str
