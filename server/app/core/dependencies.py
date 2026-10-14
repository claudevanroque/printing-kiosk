from uuid import UUID

import jwt

from fastapi import (
    Depends,
    HTTPException,
    status,
    Header,
)

from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.kiosk import Kiosk
from app.repositories import user_repository
from app.models.tenant_membership import TenantMembership
from app.repositories import tenant_repository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: UUID = payload.get("sub")

        if payload.get("type") != "access":
            raise credentials_exception
        
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        
        user_id = UUID(subject)
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = user_repository.get_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

def require_tenant_access(tenant_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TenantMembership:
    
    membership = tenant_repository.get_membership(db, tenant_id=tenant_id, user_id=current_user.id)
    
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tenant",
        )
    
    return membership

def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have platform administrator privileges",
        )
    return current_user

def get_current_membership(
    tenant_id: UUID = Header(
        alias="X-Tenant-ID"
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> TenantMembership:

    membership = tenant_repository.get_membership(
        db,
        user_id=current_user.id,
        tenant_id=tenant_id,
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tenant",
        )

    return membership


def require_tenant_manager(
    membership: TenantMembership = Depends(
        get_current_membership
    ),
) -> TenantMembership:

    if membership.role.lower() not in {
        "owner",
        "admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner or administrator required",
        )

    return membership


kiosk_bearer = HTTPBearer(auto_error=False)
def get_current_kiosk(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        kiosk_bearer
    ),
    db: Session = Depends(get_db),
) -> Kiosk:

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired kiosk token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_token(credentials.credentials)

        if payload.get("type") != "kiosk_access":
            raise unauthorized

        if not all(
            claim in payload
            for claim in ("sub", "iat", "exp", "jti")
        ):
            raise unauthorized

        kiosk_id = UUID(payload["sub"])

    except (
        jwt.InvalidTokenError,
        ValueError,
        KeyError,
        TypeError,
    ):
        raise unauthorized

    kiosk = db.scalar(
        select(Kiosk).where(Kiosk.id == kiosk_id)
    )

    if (
        kiosk is None
        or not kiosk.is_active
        or not kiosk.device_secret_hash
    ):
        raise unauthorized

    return kiosk
