from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from app.schemas.document import DocumentResponse


class UploadSessionStatus(StrEnum):
    WAITING = "WAITING"
    UPLOADING = "UPLOADING"
    READY = "READY"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CONSUMED = "CONSUMED"


class UploadSessionResponse(BaseModel):
    id: str

    status: UploadSessionStatus

    upload_url: str

    created_at: datetime
    expires_at: datetime

    document: DocumentResponse | None = None