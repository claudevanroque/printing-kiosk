import enum
import uuid

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class PaperSize(str, enum.Enum):
    A4 = "A4"
    SHORT = "Short"
    LONG = "Long"

class ColorMode(str, enum.Enum):
    BW = "bw"
    COLOR = "color"

class ServicePrice(Base):
    __tablename__ = "service_prices"

    __table_args__ = (
        UniqueConstraint("service_id", "paper_size", "color_mode", name="uq_service_price_option"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_size: Mapped[PaperSize] = mapped_column(
        Enum(
            PaperSize, 
            name="paper_size", 
            values_callable=lambda enum_cls: [item.value for item in enum_cls]
        ), 
        nullable=True
    )
    color_mode: Mapped[ColorMode] = mapped_column(
        Enum(
            ColorMode, 
            name="color_mode", 
            values_callable=lambda enum_cls: [item.value for item in enum_cls]
        ), 
        nullable=True
    )
    price_per_page: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)