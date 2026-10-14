
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PricingCalculationRequest(BaseModel):
    service_type: Literal["print", "xerox", "scan"]
    paper_size: str | None = None
    color_mode: str | None = None

    page_count: int = Field(ge=1, le=10000)
    copies: int = Field(default=1, ge=1, le=1000)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_options(self):
        if self.service_type == "scan":
            if self.paper_size is not None or self.color_mode is not None:
                raise ValueError(
                    "Scan service must not have paper size or color mode."
                )
        else:
            if not self.paper_size or not self.color_mode:
                raise ValueError(
                    "Paper size and color mode are required."
                )

        if self.page_count * self.copies > 100000:
            raise ValueError("Too many total pages.")

        return self


class PricingCalculationResponse(BaseModel):
    service_type: str
    service_name: str

    paper_size: str | None
    color_mode: str | None

    page_count: int
    copies: int
    total_pages: int

    price_per_page: Decimal
    total_price: Decimal

    currency: str = "PHP"
    pricing_version: str
