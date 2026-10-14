from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from PIL import Image
from pypdf import PdfReader

from app.core.config import settings
from app.core.utils import as_utc, utc_now
from app.models.document import Document
from app.schemas.document import (
    DocumentResponse,
    DocumentSource,
    DocumentPricingRequest,
    DocumentPricingResponse,
)
from app.schemas.pricing_calculation import PricingCalculationRequest
from app.services.pricing_calculation_service import PricingCalculationService
from app.repositories.document_repository import DocumentRepository
from app.repositories.service_job_repository import ServiceJobRepository


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}


CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def _to_document_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        original_filename=document.original_filename,
        content_type=document.content_type,
        extension=document.extension,
        file_size=document.file_size,
        page_count=document.page_count,
        source=document.source,
        created_at=as_utc(document.created_at),
        preview_url=f"/api/documents/{document.id}/file",
    )

def _validate_pdf(path: Path) -> int:
    try:
        with path.open("rb") as file:
            signature = file.read(5)

        if signature != b"%PDF-":
            raise ValueError("Invalid PDF signature")

        reader = PdfReader(str(path))

        if reader.is_encrypted:
            try:
                result = reader.decrypt("")

                if result == 0:
                    raise ValueError(
                        "Password protected PDF"
                    )
            except Exception as exc:
                raise ValueError(
                    "Password protected PDF"
                ) from exc

        page_count = len(reader.pages)

        if page_count < 1:
            raise ValueError(
                "PDF does not contain any pages"
            )

        return page_count

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid or unsupported PDF document.",
        ) from exc


def _validate_image(path: Path, extension: str) -> int:

    expected_formats = {
        ".jpg": {"JPEG"},
        ".jpeg": {"JPEG"},
        ".png": {"PNG"},
    }

    try:
        with Image.open(path) as image:
            detected_format = image.format

            image.verify()

        if detected_format not in expected_formats[extension]:
            raise ValueError(
                "Image format does not match extension"
            )

        return 1

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid image document.",
        ) from exc


def get_document(db: Session, document_id: str) -> DocumentResponse | None:
    repository = DocumentRepository(db)
    document = repository.get_by_id(document_id)

    if not document:
        return None

    return _to_document_response(document)


def get_document_record(db: Session, document_id: str) -> Document | None:
    repository = DocumentRepository(db)
    document = repository.get_by_id(document_id)

    if not document:
        return None

    return document


async def save_document(db: Session, upload: UploadFile, source: DocumentSource) -> DocumentResponse:

    if not upload.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    original_filename = Path(upload.filename).name
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported document type. "
                "Supported files: PDF, JPG, JPEG and PNG."
            ),
        )

    document_id = str(uuid4())

    stored_filename = (f"{document_id}{extension}")

    settings.temp_path.mkdir(parents=True,exist_ok=True,)

    destination = (settings.temp_path /stored_filename)

    total_size = 0

    try:
        with destination.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                total_size += len(chunk)

                if (total_size >settings.max_file_size_bytes):
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"Maximum file size is "
                            f"{settings.max_file_size_mb} MB."
                        ),
                    )

                output.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded document is empty.",
            )

        if extension == ".pdf":
            page_count = _validate_pdf(destination)
        else:
            page_count = _validate_image(destination,extension,)

        content_type = CONTENT_TYPES[extension]

        created_at = utc_now()

        repository = DocumentRepository(db)

        document = repository.create(
            Document(
                id=document_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                content_type=content_type,
                extension=extension,
                file_size=total_size,
                page_count=page_count,
                source=source,
                created_at=created_at,
            )
        )

        document = get_document(db, document_id)

        if not document:
            raise RuntimeError(
                "Document could not be created."
            )

        return document

    except Exception:
        destination.unlink(
            missing_ok=True
        )
        raise

    finally:
        await upload.close()


def delete_document(db: Session, document_id: str,) -> None:
    service_repository = ServiceJobRepository(db)
    record = get_document_record(db, document_id)

    if service_repository.document_has_jobs(document_id):
        raise HTTPException(
            status_code=400,
            detail="Document has associated service jobs and cannot be deleted.",
        )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    path = settings.temp_path / record.stored_filename

    repository = DocumentRepository(db)

    try:
        repository.unlink_upload_session(document_id)
        repository.delete(record)
        db.commit()
    except Exception:
        db.rollback()
        raise

    path.unlink(
        missing_ok=True
    )


def calculate_document_price(db: Session, document_id: str, payload: DocumentPricingRequest) -> DocumentPricingResponse:
    """
    Calculate a document's printing cost using
    its validated page count and local SQLite pricing.
    """

    document = get_document_record(db, document_id,)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # Verify the uploaded file is still available.
    path = settings.temp_path / document.stored_filename

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Document file is missing.",
        )

    if document.page_count < 1:
        raise HTTPException(
            status_code=422,
            detail="Document has an invalid page count.",
        )

    # Never trust a page count submitted by the frontend.
    pricing_request = PricingCalculationRequest(
        service_type=payload.service_type,
        paper_size=payload.paper_size,
        color_mode=payload.color_mode,
        page_count=document.page_count,
        copies=payload.copies,
    )

    # Reuse the tested Phase 5.4 pricing engine.
    pricing_service = PricingCalculationService(db)

    result = pricing_service.calculate(pricing_request)

    return DocumentPricingResponse(
        **result.model_dump(),
        document_id=document.id,
        original_filename=document.original_filename,
    )