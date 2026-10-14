
from pydantic import BaseModel, Field


class KioskTokenRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    device_secret: str = Field(min_length=32)


class KioskTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
