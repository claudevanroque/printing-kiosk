from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pricing import LocalService
from app.models.pricing import LocalServicePrice
from app.repositories.local_pricing_repository import LocalPricingRepository
from app.core.config import settings

def get_local_services(db: Session) -> list[LocalService]:
    repository = LocalPricingRepository(db)
    return repository.get_services(settings.kiosk_tenant_id)


def get_local_prices(db: Session) -> list[LocalServicePrice]:
    repository = LocalPricingRepository(db)
    return repository.get_all_prices()

def get_local_prices_by_service(db: Session, service_id: str) -> list[LocalServicePrice]:
    repository = LocalPricingRepository(db)
    return repository.get_prices(service_id)
