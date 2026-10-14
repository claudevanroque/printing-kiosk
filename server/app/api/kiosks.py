from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
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
    KioskSecretRotatedResponse,
)

from app.services import kiosk_service
from app.models.user import User

router = APIRouter(
    prefix="/kiosks",
    tags=["Kiosks"],
)

@router.get("/{tenant_id}", response_model=list[KioskResponse])
def list_kiosks(
    tenant_id: UUID,  
    db: Session = Depends(get_db), 
    platform_admin: User = Depends(require_platform_admin)
    ):
    return kiosk_repository.get_all(db, tenant_id=tenant_id)

@router.post("/{tenant_id}", response_model=KioskCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_kiosk(
    tenant_id: UUID, 
    kiosk: KioskCreate, 
    db: Session = Depends(get_db),
    platform_admin: User = Depends(require_platform_admin)
    ):
    if not platform_admin.is_platform_admin:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    try:
        kiosk, device_secret = kiosk_service.create_kiosk(db, tenant_id=tenant_id, payload=kiosk)
        return KioskCreatedResponse(
            id=kiosk.id,
            tenant_id=kiosk.tenant_id,
            code=kiosk.code,
            name=kiosk.name,
            location=kiosk.location,
            is_active=kiosk.is_active,
            device_secret=device_secret,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/{tenant_id}/{kiosk_id}/rotate-secret", response_model=KioskSecretRotatedResponse)
def rotate_kiosk_secret(
    tenant_id: UUID,
    kiosk_id: UUID,
    db: Session = Depends(get_db),
    platform_admin: User = Depends(require_platform_admin)
    ):
    if not platform_admin.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    try:
        kiosk, device_secret = kiosk_service.rotate_kiosk_secret(db, tenant_id=tenant_id, kiosk_id=kiosk_id)
        return KioskSecretRotatedResponse(
            kiosk_id=kiosk.id,
            device_secret=device_secret,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )