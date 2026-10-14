
import logging

import httpx

from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.local_pricing_repository import (
    LocalPricingRepository,
)
from app.schemas.cloud_pricing import CloudPricing
from app.services.cloud_auth_service import (
    cloud_auth_service,
)

logger = logging.getLogger(__name__)


class PricingSyncService:
    async def sync(self) -> CloudPricing:
        token = await cloud_auth_service.get_access_token()

        url = (
            settings.cloud_api_url.rstrip("/")
            + "/kiosk/pricing"
        )

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )
            response.raise_for_status()

        # Validate the cloud response before modifying SQLite.
        pricing = CloudPricing.model_validate(
            response.json()
        )

        with SessionLocal() as db:
            repository = LocalPricingRepository(db)

            try:
                repository.replace_pricing(pricing)
                db.commit()

            except Exception:
                db.rollback()
                logger.exception(
                    "Failed to synchronize local pricing"
                )
                raise

        return pricing


pricing_sync_service = PricingSyncService()
