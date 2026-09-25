from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_platform_admin: bool
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )