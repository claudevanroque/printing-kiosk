from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreateServiceJobRequest(BaseModel):
    document_id: str = Field(min_length=1)

    service_type: Literal["print", "xerox", "scan"]

    paper_size: str = Field(min_length=1)
    color_mode: str = Field(min_length=1)

    copies: int = Field(default=1, ge=1, le=1000)

    expected_pricing_version: str = Field(min_length=1)
    expected_total_price: Decimal = Field(
        ge=0,
        decimal_places=2,
    )

    model_config = ConfigDict(extra="forbid")


class ServiceJobResponse(BaseModel):
    id: str
    document_id: str | None

    service_type: str
    paper_size: str | None
    color_mode: str | None

    page_count: int
    copies: int
    total_pages: int

    price_per_page: Decimal
    total_price: Decimal
    currency: str

    pricing_version: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)