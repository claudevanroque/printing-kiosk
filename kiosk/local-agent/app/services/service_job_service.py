import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.service_job import ServiceJob
from app.repositories.service_job_repository import (
    ServiceJobRepository,
)
from app.schemas.service_job import CreateServiceJobRequest
from app.services import document_service
from app.services.pricing_calculation_service import (
    PricingCalculationService,
)

# Use the same PricingCalculationRequest class
# already used by your Phase 5.5 document_service.
from app.schemas.pricing_calculation import PricingCalculationRequest

class ServiceJobService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def calculate_file_sha256(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as file:
            while chunk := file.read(1024 * 1024):
                digest.update(chunk)

        return digest.hexdigest()


    def create_service_job(self, payload: CreateServiceJobRequest,) -> ServiceJob:

        document = document_service.get_document_record(self.db, payload.document_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        document_path = (
            settings.temp_path / document.stored_filename
        )

        if not document_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Document file is missing.",
            )

        if document.page_count <= 0:
            raise HTTPException(
                status_code=422,
                detail="Document page count is invalid.",
            )

        # Always calculate the current price on the server.
        pricing_request = PricingCalculationRequest(
            service_type=payload.service_type,
            paper_size=payload.paper_size,
            color_mode=payload.color_mode,
            page_count=document.page_count,
            copies=payload.copies,
        )

        calculator = PricingCalculationService(self.db)
        quotation = calculator.calculate(pricing_request)

        # Require the customer to accept the exact quotation.
        if (
            quotation.pricing_version is None
            or quotation.pricing_version
            != payload.expected_pricing_version
            or quotation.total_price
            != payload.expected_total_price
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Quotation has changed or is missing a "
                    "pricing version. Please calculate and "
                    "confirm the price again."
                ),
            )

        # Fingerprint the actual document.
        try:
            document_hash = self.calculate_file_sha256(document_path)
        except OSError as exc:
            raise HTTPException(
                status_code=409,
                detail="Unable to read document.",
            ) from exc

        job = ServiceJob(
            id=str(uuid4()),
            document_id=document.id,
            service_type=quotation.service_type,
            paper_size=quotation.paper_size,
            color_mode=quotation.color_mode,
            page_count=quotation.page_count,
            copies=quotation.copies,
            total_pages=quotation.total_pages,
            price_per_page=quotation.price_per_page,
            total_price=quotation.total_price,
            currency=quotation.currency,
            pricing_version=quotation.pricing_version,
            document_sha256=document_hash,
            status="pending_payment",
        )

        repository = ServiceJobRepository(self.db)

        try:
            repository.create(job)
            self.db.commit()
            self.db.refresh(job)
        except Exception:
            self.db.rollback()
            raise

        return job


    def get_service_job(self, job_id: str,) -> ServiceJob:
        repository = ServiceJobRepository(self.db)
        job = repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Service job not found.",
            )

        return job
