
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.utils import utc_now
from app.models.print_execution import PrintExecution
from app.models.service_job import ServiceJob


ACTIVE_STATUSES = (
    "queued",
    "submitting",
    "submitted",
    "submission_unknown",
)


class PrintExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, execution_id: str):
        return self.db.get(PrintExecution, execution_id)

    def get_by_service_job_id(self, job_id: str):
        return self.db.scalars(
            select(PrintExecution)
            .where(PrintExecution.service_job_id == job_id)
            .order_by(PrintExecution.attempt_number.desc())
        ).all()

    def get_active_by_service_job_id(self, job_id: str):
        return self.db.scalar(
            select(PrintExecution).where(
                PrintExecution.service_job_id == job_id,
                PrintExecution.status.in_(ACTIVE_STATUSES),
            )
        )

    def list_all(self, limit: int = 100):
        return self.db.scalars(
            select(PrintExecution)
            .order_by(PrintExecution.created_at.desc())
            .limit(limit)
        ).all()

    def claim_next(self):
        """
        Atomically claim the oldest queued execution.
        """

        while True:
            execution_id = self.db.scalar(
                select(PrintExecution.id)
                .where(PrintExecution.status == "queued")
                .order_by(
                    PrintExecution.created_at,
                    PrintExecution.id,
                )
                .limit(1)
            )

            if execution_id is None:
                self.db.rollback()
                return None

            result = self.db.execute(
                update(PrintExecution)
                .where(
                    PrintExecution.id == execution_id,
                    PrintExecution.status == "queued",
                )
                .values(
                    status="submitting",
                    started_at=utc_now(),
                )
            )

            if result.rowcount == 1:
                self.db.commit()
                return self.get_by_id(execution_id)

            self.db.rollback()

    def defer_before_submission(
        self,
        execution_id: str,
        reason: str,
    ):
        """
        Return a claimed execution to queued when
        printer health fails before submission.
        """

        execution = self.get_by_id(execution_id)

        if execution is None or execution.status != "submitting":
            raise ValueError("Invalid execution state.")

        job = self.db.get(
            ServiceJob,
            execution.service_job_id,
        )

        if job is None or job.status != "queued":
            raise ValueError("Invalid ServiceJob state.")

        execution.status = "queued"
        execution.started_at = None
        execution.error_message = reason[:1000]

        self.db.commit()

    def mark_submitted(
        self,
        execution_id: str,
        spooler_job_id: int | None = None,
    ):
        execution = self.get_by_id(execution_id)

        if execution is None or execution.status != "submitting":
            raise ValueError("Invalid execution state.")

        job = self.db.get(
            ServiceJob,
            execution.service_job_id,
        )

        if job is None or job.status != "queued":
            raise ValueError("Invalid ServiceJob state.")

        execution.status = "submitted"
        execution.spooler_job_id = spooler_job_id
        execution.submitted_at = utc_now()
        execution.error_message = None

        job.status = "printing"

        self.db.commit()

    def mark_unknown(self, execution_id: str, message: str):
        execution = self.get_by_id(execution_id)

        if execution is None:
            raise ValueError("Execution not found.")

        if execution.status not in (
            "submitting",
            "submission_unknown",
        ):
            raise ValueError("Invalid execution state.")

        execution.status = "submission_unknown"
        execution.error_message = message[:1000]

        # The printer might have received the document.
        # Never automatically retry.
        self.db.commit()

    def mark_failed(self, execution_id: str, message: str):
        """
        Only use when failure occurred before submission.
        """

        execution = self.get_by_id(execution_id)

        if execution is None or execution.status != "submitting":
            raise ValueError("Invalid execution state.")

        execution.status = "failed"
        execution.error_message = message[:1000]

        job = self.db.get(
            ServiceJob,
            execution.service_job_id,
        )

        if job is not None and job.status == "queued":
            job.status = "failed"

        self.db.commit()

    def recover_interrupted_submissions(self):
        """
        Preserve uncertain submissions after worker crash.
        """

        result = self.db.execute(
            update(PrintExecution)
            .where(PrintExecution.status == "submitting")
            .values(
                status="submission_unknown",
                error_message=(
                    "Worker interrupted during submission. "
                    "Inspect Windows spooler before retrying."
                ),
            )
        )

        self.db.commit()
        return result.rowcount
    
    def list_submitted(self, limit: int = 100):
        """
        List executions successfully submitted to Windows.
        """
        if not 1 <= limit <= 1000:
            raise ValueError("Limit must be between 1 and 1000.")

        return self.db.scalars(
            select(PrintExecution)
            .where(PrintExecution.status == "submitted")
            .order_by(
                PrintExecution.submitted_at,
                PrintExecution.id,
            )
            .limit(limit)
        ).all()

    def mark_completed(self, execution_id: str):
        """
        Mark an execution completed after an
        authorized confirmation of physical output.

        Do not call automatically when a Windows
        spooler job disappears.
        """
        execution = self.get_by_id(execution_id)

        if execution is None or execution.status != "submitted":
            raise ValueError(
                "Only submitted executions can be completed."
            )

        job = self.db.get(
            ServiceJob,
            execution.service_job_id,
        )

        if job is None or job.status != "printing":
            raise ValueError(
                "ServiceJob must be in printing state."
            )

        execution.status = "completed"
        execution.completed_at = utc_now()

        job.status = "completed"

        self.db.commit()
        return execution

