from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.service import ServiceType
from app.models.service_price import PaperSize, ColorMode


class KioskPriceResponse(BaseModel):
    id: UUID
    paper_size: PaperSize | None
    color_mode: ColorMode | None
    price_per_page: Decimal = Field(ge=0)
    is_active: bool


class KioskServiceResponse(BaseModel):
    id: UUID
    service_type: ServiceType
    name: str
    is_active: bool
    prices: list[KioskPriceResponse]


class KioskPricingResponse(BaseModel):
    tenant_id: UUID
    version: str
    synced_at: datetime
    services: list[KioskServiceResponse]