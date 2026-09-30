from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.service import ServiceType

from app.models.service_price import (
    ColorMode,
    PaperSize,
)


# =========================================================
# SERVICE
# =========================================================


class ServiceCreate(BaseModel):
    service_type: ServiceType

    name: str = Field(
        min_length=1,
        max_length=100,
    )


class ServiceUpdate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )


class ServiceStatusUpdate(BaseModel):
    is_active: bool


class ServiceResponse(BaseModel):
    id: UUID
    tenant_id: UUID

    service_type: ServiceType
    name: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# SERVICE PRICE
# =========================================================


class ServicePriceCreate(BaseModel):
    paper_size: PaperSize | None = None
    color_mode: ColorMode | None = None

    price_per_page: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )


class ServicePriceUpdate(BaseModel):
    price_per_page: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )


class ServicePriceStatusUpdate(BaseModel):
    is_active: bool


class ServicePriceResponse(BaseModel):
    id: UUID
    service_id: UUID

    paper_size: PaperSize | None
    color_mode: ColorMode | None

    price_per_page: Decimal
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# CALCULATOR
# =========================================================


class PriceCalculationRequest(BaseModel):
    paper_size: PaperSize | None = None
    color_mode: ColorMode | None = None

    pages: int = Field(
        ge=1,
        le=10000,
    )

    copies: int = Field(
        ge=1,
        le=1000,
    )


class PriceCalculationResponse(BaseModel):
    service_id: UUID
    service_type: ServiceType

    paper_size: PaperSize | None
    color_mode: ColorMode | None

    price_per_page: Decimal

    pages: int
    copies: int

    total_pages: int
    total_amount: Decimal