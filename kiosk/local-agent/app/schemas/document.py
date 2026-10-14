from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.pricing_calculation import PricingCalculationResponse
from typing import Literal


class DocumentSource(StrEnum):
    QR = "QR"
    USB = "USB"


class DocumentResponse(BaseModel):
    id: str

    original_filename: str

    content_type: str
    extension: str

    file_size: int
    page_count: int

    source: DocumentSource

    created_at: datetime

    preview_url: str

    
class DocumentPricingRequest(BaseModel):
    service_type: Literal["print", "xerox", "scan"]

    paper_size: str | None = None
    color_mode: str | None = None

    copies: int = Field(default=1, ge=1, le=1000)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_service_options(self):
        if self.service_type == "scan":
            if self.paper_size is not None or self.color_mode is not None:
                raise ValueError(
                    "Scan service must not have paper size or color mode."
                )
        else:
            if not self.paper_size or not self.color_mode:
                raise ValueError(
                    "Paper size and color mode are required for print and xerox."
                )

        return self


class DocumentPricingResponse(PricingCalculationResponse):
    document_id: str
    original_filename: str
