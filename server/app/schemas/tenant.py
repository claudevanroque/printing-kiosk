from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class TenantMembershipResponse(BaseModel):
    tenant_id: UUID
    role: str

    model_config = ConfigDict(
        from_attributes=True
    )