from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.service import (
    Service,
    ServiceType,
)
from app.models.service_price import ServicePrice

from app.repositories import (
    service_price_repository,
    service_repository,
)

from app.schemas.service import (
    PriceCalculationRequest,
    ServiceCreate,
    ServicePriceCreate,
    ServicePriceUpdate,
    ServiceUpdate,
)

def get_service(db: Session, tenant_id: UUID, service_id: UUID) -> Service:
    service = service_repository.get_by_id(db, tenant_id=tenant_id, service_id=service_id)

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    return service

def get_price(db: Session, service_id: UUID, price_id: UUID) -> ServicePrice:
    price = service_price_repository.get_by_id(db, service_id=service_id, price_id=price_id)

    if not price:
        raise HTTPException(
            status_code=404,
            detail="Service price not found",
        )

    return price

def get_services(db: Session, tenant_id: UUID) -> list[Service]:
    services = service_repository.get_all(db, tenant_id=tenant_id)

    return services

def create_service(db: Session, *, tenant_id: UUID, payload: ServiceCreate) -> Service:

    existing = service_repository.get_by_type(db, tenant_id=tenant_id, service_type=payload.service_type)

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Service with this type already exists",
        )

    name = payload.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Service name is required",
        )
    
    try:
        service = service_repository.create(
            db,
            tenant_id=tenant_id,
            service_type=payload.service_type,
            name=name,
        )

        db.commit()
        db.refresh(service)

        return service
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Service with this type already exists",
        )
    
def update_service(db: Session, *, tenant_id: UUID, service_id: UUID, payload: ServiceUpdate) -> Service:
    
    service = get_service(db, tenant_id=tenant_id, service_id=service_id)

    name = payload.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Service name is required",
        )

    try:
        service_repository.update_name(
            db,
            service=service,
            name=name,
        )

        db.commit()
        db.refresh(service)

        return service

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Service with this type already exists",
        )
    
def update_service_status(db: Session, *, tenant_id: UUID, service_id: UUID, is_active: bool) -> Service:
    
    service = get_service(db, tenant_id=tenant_id, service_id=service_id)

    try:
        service_repository.update_status(
            db,
            service=service,
            is_active=is_active,
        )

        db.commit()
        db.refresh(service)

        return service

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to update service status due to integrity error",
        )

def get_prices(db: Session, *, service_id: UUID) -> list[ServicePrice]:
    return service_price_repository.get_all(db, service_id=service_id)

def validate_price_options(*, service: Service, payload: ServicePriceCreate) -> None:

    if service.service_type == ServiceType.SCAN:
        if payload.paper_size is not None or payload.color_mode is not None:
            raise HTTPException(
                status_code=400,
                detail="Scan service should not have paper size or color mode options",
            )
    else:    
        if payload.paper_size is None:
            raise HTTPException(
                status_code=400,
                detail="Paper size is required",
            )
        
        if payload.color_mode is None:
            raise HTTPException(
                status_code=400,
                detail="Color mode is required",
            )

def check_service_active(service: Service) -> None:
    if not service.is_active:
        raise HTTPException(
            status_code=400,
            detail="Service is not active",
        )

def create_price(db: Session, *, tenant_id: UUID, service_id: UUID, payload: ServicePriceCreate) -> ServicePrice:

    service = get_service(db, tenant_id=tenant_id, service_id=service_id)

    check_service_active(service)

    validate_price_options(service=service, payload=payload)

    existing = service_price_repository.get_by_options(
        db,
        service_id=service.id,
        paper_size=payload.paper_size,
        color_mode=payload.color_mode,
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Price with these options already exists",
        )

    try:
        price = service_price_repository.create(
            db,
            service_id=service.id,
            color_mode=payload.color_mode,
            paper_size=payload.paper_size,
            price_per_page=payload.price_per_page,
        )

        db.commit()
        db.refresh(price)

        return price

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to create price due to integrity error",
        )
    
def update_price(db: Session, *, tenant_id: UUID, service_id: UUID, price_id: UUID, payload: ServicePriceUpdate) -> ServicePrice:

    service = get_service(db, tenant_id=tenant_id, service_id=service_id)

    check_service_active(service)

    price = get_price(db, service_id=service.id, price_id=price_id)

    try:
        service_price_repository.update_price(
            db,
            price=price,
            new_price_per_page=payload.price_per_page,
        )

        db.commit()
        db.refresh(price)

        return price

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to update price due to integrity error",
        )

def update_price_status(db: Session, *, tenant_id: UUID, service_id: UUID, price_id: UUID, new_status: bool) -> ServicePrice:
    service = get_service(db, tenant_id=tenant_id, service_id=service_id)

    check_service_active(service)

    price = get_price(db, service_id=service.id, price_id=price_id)

    try:
        service_price_repository.update_status(
            db,
            price=price,
            new_status=new_status,
        )

        db.commit()
        db.refresh(price)

        return price

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to update price status due to integrity error",
        )

def calculate_price(db: Session, *, tenant_id: UUID, service_id: UUID, payload: PriceCalculationRequest) -> float:
    service = get_service(db, tenant_id=tenant_id, service_id=service_id)

    if not service.is_active:
        raise HTTPException(
            status_code=400,
            detail="Service is not active",
        )
    
    if service.service_type == ServiceType.SCAN:

        if(payload.paper_size is not None or payload.color_mode is not None):
            raise HTTPException(
                status_code=400,
                detail="Paper size and color mode should not be specified for scan services",
            )
        
        if payload.copies != 1:
            raise HTTPException(
                status_code=400,
                detail="Copies should be 1 for scan services",
            )
        
        paper_size = None
        color_mode = None
    
    else:
        if payload.paper_size is None:
            raise HTTPException(
                status_code=400,
                detail="Paper size must be specified for non-scan services",
            )
        
        if payload.color_mode is None:
            raise HTTPException(
                status_code=400,
                detail="Color mode must be specified for non-scan services",
            )
        
        paper_size = payload.paper_size
        color_mode = payload.color_mode

        price = service_price_repository.get_by_options(db, service_id=service.id, paper_size=paper_size, color_mode=color_mode)

        if not price:
            raise HTTPException(
                status_code=400,
                detail="Price not found for the specified paper size and color mode",
            )
        
        if not price.is_active:
            raise HTTPException(
                status_code=400,
                detail="Price for the specified paper size and color mode is not active",
            )
        
        total_pages = payload.pages * payload.copies

        total_amount = (price.price_per_page * Decimal(total_pages)).quantize(Decimal("0.01"))

        return {
            "service_id": service.id,
            "service_type": service.service_type,
            "paper_size": paper_size,
            "color_mode": color_mode,
            "price_per_page": price.price_per_page,
            "pages": payload.pages,
            "copies": payload.copies,
            "total_pages": total_pages,
            "total_amount": total_amount,
        }