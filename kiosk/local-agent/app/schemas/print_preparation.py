from typing import Literal

from pydantic import BaseModel, ConfigDict


class PrintPreparationResponse(BaseModel):
    job_id: str
    document_id: str
    printer_name: str

    paper_size: str
    color_mode: str
    orientation: Literal["auto", "portrait", "landscape"]

    copies: int
    page_count: int
    total_pages: int

    prepared_file: str
    prepared_page_count: int

    status: Literal["prepared"] = "prepared"

    model_config = ConfigDict(extra="forbid")