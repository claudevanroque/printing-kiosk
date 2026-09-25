import secrets
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.kiosk import Kiosk
from app.repositories import kiosk_repository
from app.schemas.kiosk import KioskCreate


def create_kiosk(db: Session, *, tenant_id: UUID, payload: KioskCreate) -> Kiosk:
    existing = kiosk_repository.get_by_code(
        db,
        tenant_id=tenant_id,
        code=payload.code,
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Kiosk with this code already exists"
        )
    
    device_secret = secrets.token_urlsafe(32)

    device_secret_hash = hash_password(device_secret)

    try:
        kiosk = kiosk_repository.create(
        db,
        tenant_id=tenant_id,
        code=payload.code,
        name=payload.name,
        location=payload.location,
        device_secret_hash=device_secret_hash,
        )

        db.commit()
        db.refresh(kiosk)

        return kiosk, device_secret
    except Exception as e:
        db.rollback()
        print(f"Error occurred while creating kiosk: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )