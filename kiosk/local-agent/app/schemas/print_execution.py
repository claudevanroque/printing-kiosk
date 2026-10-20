from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PrintExecutionResponse(BaseModel):
    id: str
    service_job_id: str
    attempt_number: int

    printer_name: str
    prepared_file: str
    prepared_sha256: str

    status: str
    spooler_job_id: int | None
    error_message: str | None

    created_at: datetime
    started_at: datetime | None
    submitted_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )