from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (
    require_platform_admin,
    require_tenant_access,
)

from app.models.tenant_membership import (
    TenantMembership,
)

from app.repositories import kiosk_repository

from app.schemas.kiosk import (
    KioskCreate,
    KioskCreatedResponse,
    KioskResponse,
)

from app.services import kiosk_service
from app.models.user import User

router = APIRouter(
    prefix="/kiosks/{tenant_id}/kiosks",
    tags=["Kiosks"],
)

@router.get("", response_model=list[KioskResponse])
def list_kiosks(
    tenant_id: UUID, 
    membership: TenantMembership = Depends(require_tenant_access), 
    db: Session = Depends(get_db), 
    platform_admin: User = Depends(require_platform_admin)
    ):
    return kiosk_repository.get_all(db, tenant_id=tenant_id)

@router.post("", response_model=KioskCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_kiosk(
    tenant_id: UUID, 
    kiosk: KioskCreate, 
    membership: TenantMembership = Depends(require_tenant_access), 
    db: Session = Depends(get_db),
    platform_admin: User = Depends(require_platform_admin)
    ):
    if membership.role not in {"admin", "owner"}:

        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    try:
        return kiosk_service.create_kiosk(db, tenant_id=tenant_id, kiosk=kiosk)
        
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )