
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class CloudPrice(BaseModel):
    id: UUID
    paper_size: str | None
    color_mode: str | None
    price_per_page: Decimal = Field(
        ge=0,
        decimal_places=2,
    )
    is_active: bool

    model_config = ConfigDict(extra="forbid")


class CloudService(BaseModel):
    id: UUID
    service_type: str
    name: str
    is_active: bool
    prices: list[CloudPrice]

    model_config = ConfigDict(extra="forbid")


class CloudPricing(BaseModel):
    tenant_id: UUID
    version: str = Field(min_length=1)
    synced_at: datetime
    services: list[CloudService]

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_unique_records(self):
        service_ids = set()
        service_types = set()
        price_ids = set()

        for service in self.services:
            if service.id in service_ids:
                raise ValueError(
                    "Duplicate service ID"
                )

            if service.service_type in service_types:
                raise ValueError(
                    "Duplicate service type"
                )

            service_ids.add(service.id)
            service_types.add(service.service_type)

            options = set()

            for price in service.prices:
                if price.id in price_ids:
                    raise ValueError(
                        "Duplicate price ID"
                    )

                option = (
                    price.paper_size,
                    price.color_mode,
                )

                if option in options:
                    raise ValueError(
                        "Duplicate pricing option"
                    )

                price_ids.add(price.id)
                options.add(option)

        return self
