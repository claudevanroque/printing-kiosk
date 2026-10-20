
import asyncio
import logging
import threading

from sqlalchemy.orm import Session

from app.models.service_job import ServiceJob
from app.repositories.print_execution_repository import (
    PrintExecutionRepository,
)
from app.services.print_queue_service import (
    get_prepared_path,
)
from app.services.windows_print_service import (
    get_installed_printer_names,
    submit_prepared_pdf,
)
from app.services.printer_status_service import (
    PrinterStatusError,
    get_printer_status,
)
from app.core.utils import calculate_sha256


logger = logging.getLogger(__name__)


def process_next_execution(db: Session) -> bool:
    repo = PrintExecutionRepository(db)

    execution = repo.claim_next()

    if execution is None:
        return False

    job = db.get(
        ServiceJob,
        execution.service_job_id,
    )

    if job is None or job.status != "queued":
        repo.mark_failed(
            execution.id,
            "Missing ServiceJob or invalid job state.",
        )
        return True

    # 1. Validate prepared PDF and settings.
    try:
        pdf_path = get_prepared_path(
            execution.prepared_file
        )

        if not pdf_path.is_file():
            raise ValueError("Prepared PDF not found.")

        if calculate_sha256(pdf_path) != execution.prepared_sha256:
            raise ValueError(
                "Prepared PDF integrity check failed."
            )

        if job.orientation not in ("portrait", "landscape"):
            raise ValueError("Unsupported orientation.")

        if job.paper_size not in ("A4", "SHORT"):
            raise ValueError("Unsupported paper size.")

        if job.color_mode not in ("bw", "color"):
            raise ValueError("Unsupported color mode.")

        if not 1 <= job.copies <= 1000:
            raise ValueError("Invalid number of copies.")

    except (ValueError, OSError) as exc:
        logger.error("Print validation failed: %s", exc)
        repo.mark_failed(execution.id, str(exc))
        return True

    # 2. Printer health check before submission.
    try:
        installed = get_installed_printer_names()

        if execution.printer_name not in installed:
            reason = "Assigned printer is not installed."
        else:
            printer_status = get_printer_status(
                execution.printer_name
            )

            if printer_status["is_blocked"]:
                reason = (
                    "Printer reports a blocking condition: "
                    + ", ".join(
                        printer_status["status_flags"]
                    )
                )
            else:
                reason = None

    except (PrinterStatusError, OSError) as exc:
        reason = (
            "Unable to inspect printer health: "
            + str(exc)
        )

    if reason is not None:
        logger.warning(
            "Deferring PrintExecution %s: %s",
            execution.id,
            reason,
        )

        repo.defer_before_submission(
            execution.id,
            reason,
        )

        return False

    # 3. Submit to Windows.
    # Never automatically retry after this point.
    logger.info(
        "Submitting ServiceJob %s to %s",
        job.id,
        execution.printer_name,
    )

    try:
        result = submit_prepared_pdf(
            pdf_path=pdf_path,
            printer_name=execution.printer_name,
            copies=job.copies,
            paper_size=job.paper_size,
            orientation=job.orientation,
            color_mode=job.color_mode,
        )

        if not result.submitted:
            raise RuntimeError(
                "Print submission was not confirmed."
            )

        repo.mark_submitted(
            execution.id,
            spooler_job_id=result.spooler_job_id,
        )

        logger.info(
            "Print command submitted: %s",
            execution.id,
        )

    except Exception:
        logger.exception(
            "Print outcome uncertain for %s",
            execution.id,
        )

        db.rollback()

        repo.mark_unknown(
            execution.id,
            "Print outcome uncertain. "
            "Inspect Windows spooler before retrying.",
        )

    return True


def _worker_loop(engine, stop_event):
    logger.info("Print worker starting.")

    with Session(engine) as db:
        recovered = (
            PrintExecutionRepository(db)
            .recover_interrupted_submissions()
        )

        if recovered:
            logger.warning(
                "%s interrupted executions need review.",
                recovered,
            )

    logger.info("Print worker ready.")

    while not stop_event.is_set():
        try:
            with Session(engine) as db:
                processed = process_next_execution(db)

            if not processed:
                stop_event.wait(2)

        except Exception:
            logger.exception("Print worker error.")
            stop_event.wait(5)

    logger.info("Print worker stopped.")


async def run_print_worker(engine, stop_event: threading.Event):
    await asyncio.to_thread(
        _worker_loop,
        engine,
        stop_event,
    )
