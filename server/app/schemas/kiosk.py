from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KioskCreate(BaseModel):
    code: str
    name: str
    location: str | None = None


class KioskResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    location: str | None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class KioskCreatedResponse(KioskResponse):
    device_secret: str