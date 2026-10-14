
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pricing import (
    LocalService,
    LocalServicePrice,
    PricingSyncState,
)
from app.schemas.pricing_calculation import (
    PricingCalculationRequest,
    PricingCalculationResponse,
)


class PricingCalculationService:
    def __init__(self, db: Session):
        self.db = db

    def calculate(self, payload: PricingCalculationRequest) -> PricingCalculationResponse:

        # The local-agent must have one identifiable
        # tenant's synchronized pricing.
        sync_states = list(self.db.scalars(select(PricingSyncState)).all())

        if len(sync_states) != 1:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Local pricing is unavailable or "
                    "the kiosk tenant is ambiguous."
                ),
            )

        sync_state = sync_states[0]

        if not sync_state.pricing_version:
            raise HTTPException(
                status_code=503,
                detail="Pricing has not been synchronized.",
            )

        # Find the active service for this tenant.
        service = self.db.scalar(
            select(LocalService).where(
                LocalService.tenant_id == sync_state.tenant_id,
                LocalService.service_type == payload.service_type,
                LocalService.is_active.is_(True),
            )
        )

        if service is None:
            raise HTTPException(
                status_code=404,
                detail="Service is unavailable.",
            )

        # Find the exact pricing option.
        price = self.db.scalar(
            select(LocalServicePrice).where(
                LocalServicePrice.service_id == service.id,
                LocalServicePrice.paper_size == payload.paper_size,
                LocalServicePrice.color_mode == payload.color_mode,
                LocalServicePrice.is_active.is_(True),
            )
        )

        if price is None:
            raise HTTPException(
                status_code=404,
                detail="Pricing option is unavailable.",
            )

        total_pages = payload.page_count * payload.copies

        price_per_page = Decimal(str(price.price_per_page))

        total_price = (price_per_page * Decimal(total_pages)).quantize(Decimal("0.01"))

        return PricingCalculationResponse(
            service_type=service.service_type,
            service_name=service.name,
            paper_size=price.paper_size,
            color_mode=price.color_mode,
            page_count=payload.page_count,
            copies=payload.copies,
            total_pages=total_pages,
            price_per_page=price_per_page,
            total_price=total_price,
            pricing_version=sync_state.pricing_version,
        )
