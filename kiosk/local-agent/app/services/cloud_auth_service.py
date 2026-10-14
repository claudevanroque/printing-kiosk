import asyncio
import time

import httpx

from app.core.config import settings


class CloudAuthenticationError(Exception):
    pass


class CloudAuthService:
    def __init__(self):
        self.base_url = settings.cloud_api_url.rstrip("/")
        self.kiosk_code = settings.kiosk_code
        self.device_secret = settings.kiosk_device_secret

        self._access_token: str | None = None
        self._expires_at: float = 0
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        async with self._lock:
            if (
                self._access_token is not None
                and time.monotonic() < self._expires_at - 60
            ):
                return self._access_token

            return await self._authenticate()

    async def _authenticate(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/kiosk/auth/token",
                    json={
                        "code": self.kiosk_code,
                        "device_secret": self.device_secret,
                    },
                )

                response.raise_for_status()
                data = response.json()

        except (httpx.HTTPError, ValueError) as exc:
            raise CloudAuthenticationError(
                "Unable to authenticate kiosk with cloud"
            ) from exc

        if data.get("token_type", "").lower() != "bearer":
            raise CloudAuthenticationError(
                "Invalid cloud token type"
            )

        expires_in = int(data["expires_in"])

        if expires_in <= 60:
            raise CloudAuthenticationError(
                "Invalid token expiration"
            )

        self._access_token = data["access_token"]
        self._expires_at = time.monotonic() + expires_in

        return self._access_token


cloud_auth_service = CloudAuthService()
