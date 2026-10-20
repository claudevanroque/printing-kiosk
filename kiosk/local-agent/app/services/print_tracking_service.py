
from sqlalchemy.orm import Session

from app.repositories.print_execution_repository import (
    PrintExecutionRepository,
)
from app.services.windows_print_service import (
    get_spooler_jobs,
)


def get_execution_tracking(
    db: Session,
    execution_id: str,
) -> dict:
    """
    Retrieve a print execution and any matching
    Windows spooler job.

    An absent spooler job does not prove that
    physical printing has completed.
    """
    repository = PrintExecutionRepository(db)
    execution = repository.get_by_id(execution_id)

    if execution is None:
        raise ValueError("Print execution not found.")

    spooler_job = None
    tracking_state = "not_available"

    if execution.spooler_job_id is not None:
        jobs = get_spooler_jobs(execution.printer_name)

        spooler_job = next(
            (
                job
                for job in jobs
                if job["job_id"] == execution.spooler_job_id
            ),
            None,
        )

        tracking_state = (
            "visible_in_spooler"
            if spooler_job is not None
            else "not_visible_in_spooler"
        )

    return {
        "execution_id": execution.id,
        "service_job_id": execution.service_job_id,
        "printer_name": execution.printer_name,
        "execution_status": execution.status,
        "spooler_job_id": execution.spooler_job_id,
        "tracking_state": tracking_state,
        "spooler_job": spooler_job,
        "submitted_at": (
            execution.submitted_at.isoformat()
            if execution.submitted_at
            else None
        ),
        "completed_at": (
            execution.completed_at.isoformat()
            if execution.completed_at
            else None
        ),
    }
