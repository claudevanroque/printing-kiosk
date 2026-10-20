
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import utc_now
from app.models.base import Base


class PrintExecution(Base):
    __tablename__ = "print_executions"

    __table_args__ = (
        CheckConstraint(
            "attempt_number > 0",
            name="ck_print_executions_positive_attempt",
        ),
        CheckConstraint(
            "status IN ("
            "'queued', 'submitting', 'submitted', "
            "'submission_unknown', 'failed', 'completed'"
            ")",
            name="ck_print_executions_status",
        ),
        UniqueConstraint(
            "service_job_id",
            "attempt_number",
            name="uq_print_executions_attempt",
        ),
        Index(
            "uq_print_executions_active_service_job",
            "service_job_id",
            unique=True,
            sqlite_where=text(
                "status IN ("
                "'queued', 'submitting', 'submitted', "
                "'submission_unknown'"
                ")"
            ),
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    service_job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("service_jobs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    printer_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    prepared_file: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    prepared_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="queued",
        server_default="queued",
        index=True,
    )

    spooler_job_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
