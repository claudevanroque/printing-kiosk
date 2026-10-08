import asyncio

from fastapi import HTTPException

from app.core import windows_hotspot
from app.core.config import settings


class HotspotService:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def start(self) -> dict:
        if settings.hotspot_mode == "manual":
            return {
                "enabled": True,
                "mode": "manual",
                "ssid": settings.hotspot_ssid,
                "password": settings.hotspot_password,
                "message": (
                    "Enable Windows Mobile Hotspot "
                    "manually during development."
                ),
            }

        if settings.hotspot_mode == "automatic":
            try:
                async with self._lock:
                    hotspot = await windows_hotspot.start_hotspot()
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to start Windows Mobile Hotspot: {exc}",
                ) from exc

            return {
                "enabled": True,
                "mode": "automatic",
                "ssid": hotspot.get("ssid"),
                "password": hotspot.get("password"),
                "message": "Windows Mobile Hotspot started automatically.",
            }

        raise HTTPException(
            status_code=500,
            detail=f"Unsupported hotspot mode: {settings.hotspot_mode}",
        )

    async def stop(self) -> dict:
        if settings.hotspot_mode == "manual":
            return {
                "enabled": False,
                "mode": "manual",
                "message": (
                    "Disable Windows Mobile Hotspot "
                    "manually during development."
                ),
            }

        if settings.hotspot_mode == "automatic":
            try:
                async with self._lock:
                    await windows_hotspot.stop_hotspot()
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to stop Windows Mobile Hotspot: {exc}",
                ) from exc

            return {
                "enabled": False,
                "mode": "automatic",
                "message": "Windows Mobile Hotspot stopped automatically.",
            }

        raise HTTPException(
            status_code=500,
            detail=f"Unsupported hotspot mode: {settings.hotspot_mode}",
        )

    def status(self) -> dict:
        if settings.hotspot_mode == "automatic":
            try:
                status = windows_hotspot.hotspot_status()
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get Windows Mobile Hotspot status: {exc}",
                ) from exc

            return {
                "mode": "automatic",
                "enabled": status.get("running"),
                "state": status.get("state"),
            }

        return {
            "mode": settings.hotspot_mode,
            "ssid": settings.hotspot_ssid,
            "password": settings.hotspot_password,
        }


hotspot_service = HotspotService()