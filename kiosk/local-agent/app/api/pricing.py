
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.local_pricing import LocalServiceResponse, LocalServicePriceResponse
from app.services import local_pricing_service
from app.core.database import get_local_db
from app.schemas.pricing_calculation import (
    PricingCalculationRequest,
    PricingCalculationResponse,
)
from app.services.pricing_calculation_service import (
    PricingCalculationService,
)


router = APIRouter(
    prefix="/pricing",
    tags=["Local Pricing"],
)


@router.post("/calculate",response_model=PricingCalculationResponse,)
def calculate_pricing(payload: PricingCalculationRequest, db: Session = Depends(get_local_db)):
    service = PricingCalculationService(db)
    return service.calculate(payload)

@router.get("/services", response_model=list[LocalServiceResponse])
def get_local_services(db: Session = Depends(get_local_db)):
    return local_pricing_service.get_local_services(db)

@router.get("", response_model=list[LocalServicePriceResponse])
def get_local_prices(db: Session = Depends(get_local_db)):
    return local_pricing_service.get_local_prices(db)

@router.get("/{service_id}", response_model=list[LocalServicePriceResponse])
def get_local_prices_by_service(service_id: str, db: Session = Depends(get_local_db)):
    return local_pricing_service.get_local_prices_by_service(db, service_id)