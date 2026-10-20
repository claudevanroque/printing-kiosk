
from pydantic import BaseModel


class WindowsPrintResult(BaseModel):
    printer_name: str
    submitted: bool
    spooler_job_id: int | None = None
    message: str
