from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.tenant_membership import TenantMembership

def get_by_slug(db: Session, slug: str) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.slug == slug)
    return db.scalar(stmt)

def create(db: Session, name: str, slug: str) -> Tenant:
    tenant = Tenant(name=name, slug=slug)
    db.add(tenant)
    db.flush()
    return tenant

def create_membership(db: Session, tenant_id: UUID, user_id: UUID, role: str) -> TenantMembership:
    membership = TenantMembership(tenant_id=tenant_id, user_id=user_id, role=role)
    db.add(membership)
    return membership

def get_membership( db: Session, *, user_id: UUID, tenant_id: UUID ) -> TenantMembership | None:

    stmt = (
        select(TenantMembership)
        .join(
            Tenant,
            Tenant.id == TenantMembership.tenant_id,
        )
        .where(
            TenantMembership.user_id == user_id,
            TenantMembership.tenant_id == tenant_id,
            Tenant.is_active.is_(True),
        )
    )
    return db.scalar(stmt)


def get_user_memberships(db: Session, *, user_id: UUID) -> list[TenantMembership]:

    stmt = (
        select(TenantMembership)
        .join(
            Tenant,
            Tenant.id == TenantMembership.tenant_id,
        )
        .where(
            TenantMembership.user_id == user_id,
            Tenant.is_active.is_(True),
        )
        .order_by(
            TenantMembership.created_at.asc()
        )
    )

    return list(
        db.scalars(stmt).all()
    )

# def get_membership(db: Session, tenant_id: UUID, user_id: UUID) -> TenantMembership | None:
#     stmt = select(TenantMembership).where(
#         TenantMembership.tenant_id == tenant_id,
#         TenantMembership.user_id == user_id
#     )
#     return db.scalar(stmt)

# def get_user_memberships(db: Session, user_id: UUID) -> list[TenantMembership]:
#     stmt = select(TenantMembership).where(TenantMembership.user_id == user_id)
#     return db.scalars(stmt).all()

def get_by_id(db: Session, tenant_id: UUID) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    return db.scalar(stmt)

def get_all_tenants(db: Session) -> list[Tenant]:
    stmt = select(Tenant)
    return db.scalars(stmt).all()