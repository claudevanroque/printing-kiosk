from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import utc_now
from app.models.base import Base


class ServiceJob(Base):
    __tablename__ = "service_jobs"

    __table_args__ = (
        CheckConstraint(
            "service_type IN ('print', 'xerox', 'scan')",
            name="ck_service_jobs_service_type",
        ),
        CheckConstraint(
            "page_count > 0 AND copies > 0 AND total_pages > 0",
            name="ck_service_jobs_positive_pages",
        ),
        CheckConstraint(
            "price_per_page >= 0 AND total_price >= 0",
            name="ck_service_jobs_nonnegative_price",
        ),
        CheckConstraint(
            "status IN ('pending_payment', 'paid', "
            "'queued', 'printing', 'completed', "
            "'failed', 'cancelled')",
            name="ck_service_jobs_status",
        ),
        CheckConstraint(
            "orientation IN ('auto', 'portrait', 'landscape')",
            name="ck_service_jobs_orientation",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    document_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    service_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    paper_size: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    color_mode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    orientation: Mapped[str | None] = mapped_column(
        String(20),
        nullable=False,
        default="auto",
        server_default="auto",
    )

    page_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    copies: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_pages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    price_per_page: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PHP",
    )

    pricing_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    document_sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending_payment",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )