from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.kiosk import Kiosk

def get_by_code(db: Session, *, tenant_id: UUID, code: str) -> Kiosk | None:
    stmt = select(Kiosk).where(
        Kiosk.tenant_id == tenant_id,
        Kiosk.code == code
    )
    return db.scalar(stmt)

def get_all(db: Session, *, tenant_id: UUID) -> list[Kiosk]:
    stmt = select(Kiosk).where(Kiosk.tenant_id == tenant_id)
    return db.scalars(stmt).all()

def create(db: Session, *, tenant_id: UUID, code: str, name: str, location: str | None, device_secret_hash: str) -> Kiosk:
    kiosk = Kiosk(
        tenant_id=tenant_id,
        code=code,
        name=name,
        location=location,
        device_secret_hash=device_secret_hash
    )
    db.add(kiosk)
    return kiosk