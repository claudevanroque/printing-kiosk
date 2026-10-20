
import hashlib
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.print_execution import PrintExecution
from app.models.service_job import ServiceJob
from app.repositories.print_execution_repository import (
    PrintExecutionRepository,
)
from app.services.print_preparation_service import (
    prepare_print_job,
)
from app.core.utils import calculate_sha256

def get_prepared_path(filename: str) -> Path:
    prepared_dir = (
        Path(settings.temp_path).resolve() / "prepared"
    )

    path = (prepared_dir / filename).resolve()

    if (
        path.parent != prepared_dir
        or path.suffix.lower() != ".pdf"
    ):
        raise ValueError("Invalid prepared PDF path.")

    return path


def enqueue_paid_job(db: Session,job_id: str) -> PrintExecution:
    """
    Internal operation only.

    The caller must be a trusted payment-confirmation
    workflow, not a customer-controlled API endpoint.
    """

    job = db.get(ServiceJob, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="ServiceJob not found.",
        )

    if job.service_type != "print":
        raise HTTPException(
            status_code=422,
            detail="Only print jobs are supported.",
        )

    if job.status != "paid":
        raise HTTPException(
            status_code=409,
            detail="Verified payment is required.",
        )

    if job.orientation not in ("portrait", "landscape"):
        raise HTTPException(
            status_code=422,
            detail=(
                "Phase 6.5 currently requires an explicitly "
                "tested portrait or landscape orientation."
            ),
        )

    if job.paper_size not in ("A4", "SHORT"):
        raise HTTPException(
            status_code=422,
            detail=(
                "Only A4 and SHORT are currently supported "
                "by the verified Windows print adapter."
            ),
        )

    if job.color_mode not in ("bw", "color"):
        raise HTTPException(
            status_code=422,
            detail="Invalid color mode.",
        )

    repo = PrintExecutionRepository(db)

    previous = repo.get_by_service_job_id(job_id)

    # Initial production policy: one attempt only.
    # Explicitly authorized reprints will be added later.
    if previous:
        raise HTTPException(
            status_code=409,
            detail="Print attempt already exists for this job.",
        )

    preparation = prepare_print_job(
        db=db,
        job_id=job_id,
    )

    filename = preparation["prepared_file"]

    try:
        pdf_path = get_prepared_path(filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Prepared PDF not found.",
        )

    execution = PrintExecution(
        service_job_id=job.id,
        attempt_number=1,
        printer_name=preparation["printer_name"],
        prepared_file=filename,
        prepared_sha256=calculate_sha256(pdf_path),
        status="queued",
    )

    db.add(execution)
    job.status = "queued"

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Duplicate print execution.",
        ) from exc

    db.refresh(execution)

    return execution
