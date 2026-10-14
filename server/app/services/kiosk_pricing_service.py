
import uuid
import json
import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service import Service
from app.models.service_price import ServicePrice
from app.repositories.kiosk_pricing_repository import KioskPricingRepository



class KioskPricingService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = KioskPricingRepository(self.db)

    def get_services(self, tenant_id: uuid.UUID) -> list[Service]:

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

    def get_prices(self, service_ids: list[uuid.UUID],) -> list[ServicePrice]:

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
    
    def get_kiosk_pricing(self, tenant_id: uuid.UUID) -> dict:
        services = self.repository.get_services(tenant_id=tenant_id)
        service_ids = [service.id for service in services]
        prices = self.repository.get_prices(service_ids=service_ids)
        prices_by_service = {}

        for price in prices:
            prices_by_service.setdefault(
                price.service_id, []
            ).append({
                "id": str(price.id),
                "paper_size": (
                    price.paper_size.value
                    if hasattr(price.paper_size, "value")
                    else price.paper_size
                ),
                "color_mode": (
                    price.color_mode.value
                    if hasattr(price.color_mode, "value")
                    else price.color_mode
                ),
                "price_per_page": str(price.price_per_page),
                "is_active": price.is_active,
            })

        service_data = []

        for service in services:
            service_data.append({
                "id": str(service.id),
                "service_type": (
                    service.service_type.value
                    if hasattr(service.service_type, "value")
                    else service.service_type
                ),
                "name": service.name,
                "is_active": service.is_active,
                "prices": prices_by_service.get(
                    service.id, []
                ),
            })

        version_data = json.dumps(
            service_data,
            sort_keys=True,
            separators=(",", ":"),
        )

        pricing_digest = hashlib.sha256(
            version_data.encode("utf-8")
        ).hexdigest()
        version = f"pricing-{pricing_digest[:12]}"

        return {
            "tenant_id": tenant_id,
            "version": version,
            "synced_at": datetime.now(timezone.utc),
            "services": service_data,
        }

