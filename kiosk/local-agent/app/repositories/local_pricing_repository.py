
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.pricing import (
    LocalService,
    LocalServicePrice,
    PricingSyncState,
)
from app.schemas.cloud_pricing import CloudPricing


class LocalPricingRepository:
    def __init__(self, db: Session):
        self.db = db

    def replace_pricing(self, pricing: CloudPricing) -> None:
        tenant_id = str(pricing.tenant_id)

        service_ids = list(
            self.db.scalars(
                select(LocalService.id).where(
                    LocalService.tenant_id == tenant_id
                )
            ).all()
        )

        if service_ids:
            self.db.execute(
                delete(LocalServicePrice).where(
                    LocalServicePrice.service_id.in_(
                        service_ids
                    )
                )
            )

        self.db.execute(
            delete(LocalService).where(
                LocalService.tenant_id == tenant_id
            )
        )

        # Complete deletions before inserting replacements.
        self.db.flush()

        for service in pricing.services:
            self.db.add(
                LocalService(
                    id=str(service.id),
                    tenant_id=tenant_id,
                    service_type=service.service_type,
                    name=service.name,
                    is_active=service.is_active,
                )
            )

            for price in service.prices:
                self.db.add(
                    LocalServicePrice(
                        id=str(price.id),
                        service_id=str(service.id),
                        paper_size=price.paper_size,
                        color_mode=price.color_mode,
                        price_per_page=price.price_per_page,
                        is_active=price.is_active,
                    )
                )

        state = self.db.get(PricingSyncState, tenant_id)

        if state is None:
            state = PricingSyncState(
                tenant_id=tenant_id
            )
            self.db.add(state)

        state.pricing_version = pricing.version
        state.last_synced_at = pricing.synced_at

        self.db.flush()

    def get_sync_state(self, tenant_id: str) -> PricingSyncState | None:
        return self.db.get(PricingSyncState, tenant_id,)

    def get_services(self, tenant_id: str) -> list[LocalService]:
        stmt = (
            select(LocalService)
            .where(
                LocalService.tenant_id == tenant_id
            )
            .order_by(LocalService.service_type)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def get_prices(self, service_id: str) -> list[LocalServicePrice]:
        stmt = (
            select(LocalServicePrice)
            .where(
                LocalServicePrice.service_id == service_id
            )
            .order_by(LocalServicePrice.id)
        )

        return list(
            self.db.scalars(stmt).all()
        )
    
    def get_all_prices(self) -> list[LocalServicePrice]:
        stmt = (select(LocalServicePrice))
        
        return list(
            self.db.scalars(stmt).all()
        )
