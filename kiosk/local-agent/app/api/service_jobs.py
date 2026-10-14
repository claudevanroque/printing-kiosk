from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_local_db
from app.schemas.service_job import (
    CreateServiceJobRequest,
    ServiceJobResponse,
)
from app.services.service_job_service import ServiceJobService


router = APIRouter(
    prefix="/service-jobs",
    tags=["Service Jobs"],
)

DbSession = Annotated[
    Session,
    Depends(get_local_db),
]


@router.post("", response_model=ServiceJobResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: CreateServiceJobRequest, db: DbSession):
    service = ServiceJobService(db)
    return service.create_service_job(payload)


@router.get("/{job_id}", response_model=ServiceJobResponse)
def get_job(job_id: str, db: DbSession):
    service = ServiceJobService(db)
    return service.get_service_job(job_id)