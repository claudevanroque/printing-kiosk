from fastapi import (
    APIRouter,
    Depends,
    status,
    Header,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from uuid import UUID
from app.core.dependencies import require_platform_admin
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterTenantRequest,
    TokenResponse,
)

from app.services import (
    auth_service,
    tenant_service,
)
from app.models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterTenantRequest, db: Session = Depends(get_db), platform_admin: User = Depends(require_platform_admin)):
    tenant, user = tenant_service.register_tenant(
        db,
        bussiness_name=payload.bussiness_name,
        bussiness_slug=payload.bussiness_slug,
        email=payload.email,
        password=payload.password,
    )
    return {
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
        },
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db), device_id: str = Header(..., alias="X-Device-ID"),):
    return auth_service.login(
        db,
        email=payload.email,
        password=payload.password,
        device_id=device_id,
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh(
        db,
        refresh_token=payload.refresh_token,
    )

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    auth_service.logout(
        db,
        refresh_token=payload.refresh_token,
    )
    return None