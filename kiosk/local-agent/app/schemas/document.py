from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


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