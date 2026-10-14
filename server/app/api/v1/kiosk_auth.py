
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_kiosk_access_token
from app.schemas.kiosk_auth import (
    KioskTokenRequest,
    KioskTokenResponse,
)
from app.services.kiosk_auth_service import authenticate_kiosk


router = APIRouter(
    prefix="/kiosk/auth",
    tags=["Kiosk Authentication"],
)


@router.post("/token", response_model=KioskTokenResponse)
def issue_kiosk_token(payload: KioskTokenRequest, response: Response, db: Session = Depends(get_db)):
    kiosk = authenticate_kiosk(db, code=payload.code, device_secret=payload.device_secret,)
    response.headers["Cache-Control"] = "no-store"

    return KioskTokenResponse(
        access_token=create_kiosk_access_token(kiosk.id),
        expires_in=1800,
    )
