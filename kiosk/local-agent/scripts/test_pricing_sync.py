
import asyncio

from app.core.database import SessionLocal
from app.repositories.local_pricing_repository import (
    LocalPricingRepository,
)
from app.services.pricing_sync_service import (
    pricing_sync_service,
)


async def main():
    print("Starting cloud pricing synchronization...")

    pricing = await pricing_sync_service.sync()

    print("[OK] Cloud pricing downloaded")

    tenant_id = str(pricing.tenant_id)

    with SessionLocal() as db:
        repository = LocalPricingRepository(db)

        state = repository.get_sync_state(
            tenant_id
        )

        services = repository.get_services(
            tenant_id
        )

        assert state is not None
        assert state.pricing_version == pricing.version
        assert len(services) == len(pricing.services)

        for service in services:
            prices = repository.get_prices(
                service.id
            )

            print(
                f"{service.name}: {len(prices)} prices"
            )

    print("[OK] SQLite pricing verified")
    print("Tenant:", tenant_id)
    print("Version:", pricing.version)
    print("\nPhase 5.3 synchronization test passed!")


if __name__ == "__main__":
    asyncio.run(main())
