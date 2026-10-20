from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class PrinterAssignmentRequest(BaseModel):
    paper_size: str
    printer_name: str

    model_config = ConfigDict(
        extra="forbid"
    )

class PrinterAssignmentResponse(BaseModel):
    paper_size: str
    printer_name: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PrinterResponse(BaseModel):
    name: str
    driver_name: str | None
    port_name: str | None
    is_default: bool
    status_code: int
    jobs_count: int
