from uuid import UUID

import jwt

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
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