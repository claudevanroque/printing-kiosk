
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service import Service
from app.models.service_price import ServicePrice


class KioskPricingRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_services(self, tenant_id: uuid.UUID,) -> list[Service]:
        stmt = (
            select(Service)
            .where(
                Service.tenant_id == tenant_id
            )
            .order_by(Service.service_type)
        )
        return list(
            self.db.scalars(stmt).all()
        )

    def get_prices(self, service_ids: list[uuid.UUID]) -> list[ServicePrice]:
        if not service_ids:
            return []
        
        stmt = (
            select(ServicePrice)
            .where(
                ServicePrice.service_id.in_(
                    service_ids
                )
            )
            .order_by(ServicePrice.id)
        )

        return list(
            self.db.scalars(stmt).all()
        )
