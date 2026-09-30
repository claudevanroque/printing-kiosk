from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories import (
    tenant_repository,
    user_repository,
)

def register_tenant(db: Session, *, business_name: str, business_slug: str, email: str, password: str):
    business_slug = business_slug.strip().lower()
    business_name = business_name.strip()
    email = email.strip().lower()

    if tenant_repository.get_by_slug(db, slug=business_slug):
        raise HTTPException(
            status_code=400,
            detail="Tenant with this slug already exists"
        )
    
    if user_repository.get_by_email(db, email=email):
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    try:
        tenant = tenant_repository.create(db, name=business_name, slug=business_slug)
        hashed_password = hash_password(password)
        user = user_repository.create(db, email=email, hashed_password=hashed_password)
        
        db.flush()

        tenant_repository.create_membership(db, tenant_id=tenant.id, user_id=user.id, role="owner")

        db.commit()
        db.refresh(tenant)
        db.refresh(user)    

        return tenant, user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while registering the tenant: {str(e)}"
        )
    
def get_tenant_by_id(db: Session, tenant_id: int):
    tenant = tenant_repository.get_by_id(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    return tenant

def get_all_tenants(db: Session):
    return tenant_repository.get_all_tenants(db)