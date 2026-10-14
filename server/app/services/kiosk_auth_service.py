
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.kiosk import Kiosk


def authenticate_kiosk(db: Session, *, code: str, device_secret: str) -> Kiosk:
    kiosk = db.scalar(select(Kiosk).where(Kiosk.code == code))

    if (kiosk is None or not kiosk.is_active or not kiosk.device_secret_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid kiosk credentials",
        )

    if not verify_password(device_secret, kiosk.device_secret_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid kiosk credentials",
        )

    return kiosk
