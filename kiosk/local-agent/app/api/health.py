from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db


router = APIRouter(prefix="/health", tags=["Health"])


def _database_status(db: Session) -> str:
    try:
        db.execute(text("SELECT 1"))
        return "connected"
    except Exception:
        return "disconnected"


@router.get("")
def health(db: Session = Depends(get_db)):
    return {
        "status": "ok",
        "service": "kiosk-local-agent",
        "database": _database_status(db),
    }