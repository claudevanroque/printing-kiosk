
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class LocalService(Base):
    __tablename__ = "local_services"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "service_type",
            name="uq_local_tenant_service_type",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    service_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class LocalServicePrice(Base):
    __tablename__ = "local_service_prices"

    __table_args__ = (
        UniqueConstraint(
            "service_id",
            "paper_size",
            "color_mode",
            name="uq_local_service_price_option",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    service_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "local_services.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    paper_size: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    color_mode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    price_per_page: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class PricingSyncState(Base):
    __tablename__ = "pricing_sync_state"

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    pricing_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
