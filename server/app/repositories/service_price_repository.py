from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service_price import (
    ColorMode,
    PaperSize,
    ServicePrice,
)

def get_all(db: Session, *, service_id: UUID) -> list[ServicePrice]:
    stmt = select(ServicePrice).where(ServicePrice.service_id == service_id).order_by(ServicePrice.created_at.asc())
    return list(db.scalars(stmt).all())

def get_by_id(db: Session, *, service_id: UUID, price_id: UUID ) -> ServicePrice | None:
    stmt = select(ServicePrice).where(
        ServicePrice.service_id == service_id,
        ServicePrice.id == price_id
    )
    return db.scalar(stmt)

def get_by_options(db: Session, *, service_id: UUID, color_mode: ColorMode, paper_size: PaperSize) -> ServicePrice | None:
    stmt = select(ServicePrice).where(
        ServicePrice.service_id == service_id,
        ServicePrice.color_mode == color_mode,
        ServicePrice.paper_size == paper_size
    )
    return db.scalar(stmt)

def create(db: Session, *, service_id: UUID, color_mode: ColorMode, paper_size: PaperSize, price_per_page: Decimal) -> ServicePrice:
    service_price = ServicePrice(
        service_id=service_id,
        color_mode=color_mode,
        paper_size=paper_size,
        price_per_page=price_per_page
    )
    db.add(service_price)
    db.flush()
    return service_price

def update_price(db: Session, *, price: ServicePrice, new_price_per_page: Decimal) -> ServicePrice:
    price.price_per_page = new_price_per_page
    db.flush()
    return price

def update_status(db: Session, *, price: ServicePrice, new_status: bool) -> ServicePrice:
    price.is_active = new_status
    db.flush()
    return price