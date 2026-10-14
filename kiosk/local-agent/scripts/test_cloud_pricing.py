
import asyncio

import httpx

from app.core.config import settings
from app.services.cloud_auth_service import cloud_auth_service


async def main():
    token = await cloud_auth_service.get_access_token()

    url = (
        settings.cloud_api_url.rstrip("/")
        + "/kiosk/pricing"
    )

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

    print("Status:", response.status_code)

    response.raise_for_status()

    data = response.json()

    print("Tenant:", data["tenant_id"])
    print("Version:", data["version"])
    print("Last synced:", data["synced_at"])

    for service in data["services"]:
        print(
            f"\nService: {service['name']}"
        )

        for price in service["prices"]:
            print(
                "  ",
                price["paper_size"],
                price["color_mode"],
                price["price_per_page"],
            )

    print("\nCloud pricing test successful!")


if __name__ == "__main__":
    asyncio.run(main())
