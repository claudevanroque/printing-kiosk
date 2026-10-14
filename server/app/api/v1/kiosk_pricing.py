
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_kiosk
from app.models.kiosk import Kiosk
from app.schemas.kiosk_pricing import KioskPricingResponse
from app.services.kiosk_pricing_service import KioskPricingService


router = APIRouter(
    prefix="/kiosk",
    tags=["Kiosk Pricing"],
)


@router.get("/pricing",response_model=KioskPricingResponse,)
def retrieve_kiosk_pricing(response: Response, db: Session = Depends(get_db), kiosk: Kiosk = Depends(get_current_kiosk)):
    response.headers["Cache-Control"] = "no-store"
    service = KioskPricingService(db)
    
    return service.get_kiosk_pricing(
        tenant_id=kiosk.tenant_id
    )
