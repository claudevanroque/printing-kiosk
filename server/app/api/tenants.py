from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (
    require_tenant_access,
    require_platform_admin,
)
from app.models.user import User

from app.services import tenant_service
from app.models.tenant_membership import (
    TenantMembership,
)

from app.schemas.tenant import TenantResponse


router = APIRouter(
    prefix="/tenants",
    tags=["Tenants"],
)

@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: UUID, membership: TenantMembership = Depends(require_tenant_access), db: Session = Depends(get_db)):
    tenant = tenant_service.get_tenant_by_id(db, tenant_id=tenant_id)
    return tenant

@router.get("/", response_model=list[TenantResponse])
def get_all_tenants(db: Session = Depends(get_db), platform_admin: User = Depends(require_platform_admin)):
    return tenant_service.get_all_tenants(db)