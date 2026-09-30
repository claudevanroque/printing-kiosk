import enum
import uuid

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ServiceType(str, enum.Enum):
    PRINT = "print"
    XEROX = "xerox"
    SCAN = "scan"

class Service(Base):
    __tablename__ = "services"

    __table_args__ = (
        UniqueConstraint("tenant_id", "service_type", name="uq_tenant_service_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    service_type: Mapped[ServiceType] = mapped_column(
        Enum(
            ServiceType, 
            name="service_type", 
            values_callable=lambda enum_cls: [item.value for item in enum_cls]), 
            nullable=False
        )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)