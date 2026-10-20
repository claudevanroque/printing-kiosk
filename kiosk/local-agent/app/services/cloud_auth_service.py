
import asyncio
import time

import httpx

from app.core.config import settings


class CloudAuthenticationError(Exception):
    pass


class CloudConnectionError(CloudAuthenticationError):
    pass


class CloudTimeoutError(CloudAuthenticationError):
    pass


class CloudCredentialsError(CloudAuthenticationError):
    pass


class CloudServerError(CloudAuthenticationError):
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

        except httpx.TimeoutException as exc:
            raise CloudTimeoutError(
                "Cloud authentication timed out"
            ) from exc

        except httpx.ConnectError as exc:
            raise CloudConnectionError(
                "Cannot connect to cloud server"
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code in (401, 403):
                raise CloudCredentialsError(
                    "Kiosk authentication rejected by cloud"
                ) from exc

            if status_code >= 500:
                raise CloudServerError(
                    f"Cloud server error (HTTP {status_code})"
                ) from exc

            raise CloudAuthenticationError(
                f"Cloud authentication failed (HTTP {status_code})"
            ) from exc

        except httpx.RequestError as exc:
            raise CloudConnectionError(
                "Cloud authentication network request failed"
            ) from exc

        except ValueError as exc:
            raise CloudAuthenticationError(
                "Invalid cloud authentication response"
            ) from exc

        if not isinstance(data, dict):
            raise CloudAuthenticationError(
                "Invalid cloud authentication response"
            )

        try:
            token_type = data["token_type"]
            access_token = data["access_token"]
            expires_in = int(data["expires_in"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CloudAuthenticationError(
                "Incomplete cloud authentication response"
            ) from exc

        if (
            not isinstance(token_type, str)
            or token_type.lower() != "bearer"
        ):
            raise CloudAuthenticationError(
                "Invalid cloud token type"
            )

        if not isinstance(access_token, str) or not access_token:
            raise CloudAuthenticationError(
                "Invalid cloud access token"
            )

        if expires_in <= 60:
            raise CloudAuthenticationError(
                "Invalid token expiration"
            )

        self._access_token = access_token
        self._expires_at = time.monotonic() + expires_in

        return self._access_token


cloud_auth_service = CloudAuthService()
