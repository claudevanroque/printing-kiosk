from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user

from app.models.user import User

from app.repositories import (
    tenant_repository,
)

from app.schemas.user import UserResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/me/tenants")
def get_my_tenants(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    memberships = tenant_repository.get_user_memberships(db, current_user.id)

    return memberships