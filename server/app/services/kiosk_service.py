
import secrets
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.kiosk import Kiosk
from app.repositories import kiosk_repository
from app.schemas.kiosk import KioskCreate


def create_kiosk(db: Session, *, tenant_id: UUID, payload: KioskCreate,) -> tuple[Kiosk, str]:

    existing = kiosk_repository.get_by_code(db,tenant_id=tenant_id,code=payload.code,)

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Kiosk with this code already exists",
        )

    # Generate a secure secret for this physical kiosk.
    device_secret = secrets.token_urlsafe(32)

    # Store only the hash in PostgreSQL.
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

        # Plaintext secret is returned only at registration.
        return kiosk, device_secret

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Kiosk code or name already exists",
        )

    except Exception:
        db.rollback()
        raise

def rotate_kiosk_secret(db: Session, *, tenant_id: UUID, kiosk_id: UUID) -> tuple[Kiosk, str]:
    kiosk = kiosk_repository.get_by_id_and_tenant_id(db, tenant_id=tenant_id, kiosk_id=kiosk_id)

    if not kiosk:
        raise HTTPException(
            status_code=404,
            detail="Kiosk not found",
        )

    device_secret = secrets.token_urlsafe(32)
    device_secret_hash = hash_password(device_secret)
    try:
        kiosk = kiosk_repository.update_device_secret_hash(
            db,
            kiosk=kiosk,
            device_secret_hash=device_secret_hash,
        )
        db.commit()
        db.refresh(kiosk)

        return kiosk, device_secret

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Kiosk code or name already exists",
        )

    except Exception:
        db.rollback()
        raise