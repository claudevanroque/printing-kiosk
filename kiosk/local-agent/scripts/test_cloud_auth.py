
import asyncio

from app.services.cloud_auth_service import cloud_auth_service


async def main():
    print("Testing kiosk cloud authentication...")

    # First request: authenticates with cloud.
    token1 = await cloud_auth_service.get_access_token()
    print("[OK] First authentication successful")

    # Second request: should reuse cached token.
    token2 = await cloud_auth_service.get_access_token()

    assert token1 == token2
    print("[OK] Cached token reused")

    # Simulate an expired token.
    cloud_auth_service._expires_at = 0

    # Third request: authenticates again.
    token3 = await cloud_auth_service.get_access_token()

    assert token3 != token1
    print("[OK] Token renewed successfully")

    print("\nAll cloud authentication tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
