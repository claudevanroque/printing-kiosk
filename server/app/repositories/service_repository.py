from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service import (
    Service,
    ServiceType,
)

def get_all(db: Session, *, tenant_id: UUID) -> list[Service]:
    stmt = select(Service).where(Service.tenant_id == tenant_id).order_by(Service.created_at.asc())
    return list(db.scalars(stmt).all())

def get_by_id(db: Session, *, tenant_id: UUID, service_id: UUID) -> Service | None:
    stmt = select(Service).where(
        Service.tenant_id == tenant_id,
        Service.id == service_id,
        Service.is_active == True
    )
    return db.scalar(stmt)

def get_by_type(db: Session, *, tenant_id: UUID, service_type: ServiceType) -> Service | None:
    stmt = select(Service).where(
        Service.tenant_id == tenant_id,
        Service.service_type == service_type
    )
    return db.scalar(stmt)

def create(db: Session, *, tenant_id: UUID, service_type: ServiceType, name: str) -> Service:
    service = Service(tenant_id=tenant_id, service_type=service_type, name=name)
    db.add(service)
    db.flush()
    return service

def update_name(db: Session, *, service: Service, name: str) -> Service | None:
    service.name = name
    db.add(service)
    db.flush()
    return service

def update_status(db: Session, *, service: Service, is_active: bool) -> Service | None:
    service.is_active = is_active
    db.add(service)
    db.flush()
    return service