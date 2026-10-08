from fastapi import APIRouter

from app.services.hotspot_service import (
    hotspot_service,
)


router = APIRouter(
    prefix="/hotspot",
    tags=["Hotspot"],
)


@router.post("/start")
async def start_hotspot():
    return await hotspot_service.start()


@router.post("/stop")
async def stop_hotspot():
    return await hotspot_service.stop()


@router.get("/status")
async def hotspot_status():
    return await hotspot_service.status()