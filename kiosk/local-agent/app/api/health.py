from fastapi import APIRouter

from app.core.database import get_connection


router = APIRouter(prefix="/health", tags=["Health"])


def _database_status() -> str:
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")

        return "connected"
    except Exception:
        return "disconnected"


@router.get("")
def health():
    return {
        "status": "ok",
        "service": "kiosk-local-agent",
        "database": _database_status(),
    }