from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

class LocalServiceResponse(BaseModel):
    id: str
    tenant_id: str
    service_type: str
    name: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )

class LocalServicePriceResponse(BaseModel):
    id: str
    service_id: str
    paper_size: str | None
    color_mode: str | None
    price_per_page: Decimal
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )

