from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (
    get_current_membership,
    require_tenant_manager,
)
from app.models.tenant_membership import TenantMembership

from app.schemas.service import (
    PriceCalculationRequest,
    PriceCalculationResponse,
    ServiceCreate,
    ServicePriceCreate,
    ServicePriceResponse,
    ServicePriceStatusUpdate,
    ServicePriceUpdate,
    ServiceResponse,
    ServiceStatusUpdate,
    ServiceUpdate,
)

from app.services import pricing_service


router = APIRouter(
    prefix="/services",
    tags=["Services & Pricing"],
)

@router.get("", response_model=list[ServiceResponse])
def get_services(db: Session = Depends(get_db), membership: TenantMembership = Depends(get_current_membership)):
    return pricing_service.get_services(db, tenant_id=membership.tenant_id)

@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db), membership: TenantMembership = Depends(require_tenant_manager)):
    return pricing_service.create_service(db, tenant_id=membership.tenant_id, payload=payload)

@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: UUID, db: Session = Depends(get_db), membership: TenantMembership = Depends(get_current_membership)):
    return pricing_service.get_service(db, tenant_id=membership.tenant_id, service_id=service_id)

@router.patch("/{service_id}", response_model=ServiceResponse)
def update_service(service_id: UUID, payload: ServiceUpdate, db: Session = Depends(get_db), membership: TenantMembership = Depends(require_tenant_manager)):
    return pricing_service.update_service(db, tenant_id=membership.tenant_id, service_id=service_id, payload=payload)

@router.patch("/{service_id}/status", response_model=ServiceResponse)
def update_service_status(service_id: UUID, payload: ServiceStatusUpdate, db: Session = Depends(get_db), membership: TenantMembership = Depends(require_tenant_manager)):
    return pricing_service.update_service_status(db, tenant_id=membership.tenant_id, service_id=service_id, is_active=payload.is_active)

@router.get("/{service_id}/prices", response_model=list[ServicePriceResponse])
def get_service_prices(service_id: UUID, db: Session = Depends(get_db), membership: TenantMembership = Depends(get_current_membership)):
    return pricing_service.get_prices(db, service_id=service_id)

@router.post("/{service_id}/prices", response_model=ServicePriceResponse, status_code=status.HTTP_201_CREATED)
def create_price(service_id: UUID, payload: ServicePriceCreate, db: Session = Depends(get_db), membership: TenantMembership = Depends(require_tenant_manager)):
    return pricing_service.create_price(db, tenant_id=membership.tenant_id, service_id=service_id, payload=payload)

@router.patch("/{service_id}/prices/{price_id}", response_model=ServicePriceResponse)
def update_price(service_id: UUID, price_id: UUID, payload: ServicePriceUpdate, db: Session = Depends(get_db), membership: TenantMembership = Depends(require_tenant_manager)):
    return pricing_service.update_price(db, tenant_id=membership.tenant_id, service_id=service_id, price_id=price_id, payload=payload)

@router.patch("/{service_id}/prices/{price_id}/status", response_model=ServicePriceResponse)
def update_price_status(service_id: UUID, price_id: UUID, payload: ServicePriceStatusUpdate, db: Session = Depends(get_db), membership: TenantMembership = Depends(require_tenant_manager)):
    return pricing_service.update_price_status(db, tenant_id=membership.tenant_id, service_id=service_id, price_id=price_id, new_status=payload.is_active)

@router.post("/{service_id}/calculate-price", response_model=PriceCalculationResponse)
def calculate_price(service_id: UUID, payload: PriceCalculationRequest, db: Session = Depends(get_db), membership: TenantMembership = Depends(get_current_membership)):
    return pricing_service.calculate_price(db, tenant_id=membership.tenant_id, service_id=service_id, payload=payload)
    