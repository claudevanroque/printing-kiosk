from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import utc_now
from app.models.base import Base


class PrinterAssignment(Base):
    __tablename__ = "printer_assignments"

    paper_size: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    printer_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )