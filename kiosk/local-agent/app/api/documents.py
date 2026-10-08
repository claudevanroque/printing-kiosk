from typing import Annotated
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    Depends,
)
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.document import (
    DocumentResponse,
    DocumentSource,
)

from app.services import document_service

from app.core.database import get_db


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.post("/upload",response_model=DocumentResponse)
async def upload_document(db: DbSession, file: UploadFile = File(...)):
    document = await document_service.save_document(
        db,
        file,
        DocumentSource.USB,
    )
    db.commit()

    return document


@router.get("/{document_id}",response_model=DocumentResponse)
def document_details(document_id: str, db: DbSession):
    document = document_service.get_document(db, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document


@router.get("/{document_id}/file")
def document_file(document_id: str, db: DbSession):
    record = document_service.get_document_record(db, document_id)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    path = settings.temp_path / record.stored_filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document file is missing.",
        )

    return FileResponse(
        path=path,
        media_type=record.content_type,
        filename=record.original_filename,
        content_disposition_type="inline",
    )


@router.delete("/{document_id}",status_code=204)
def remove_document(document_id: str, db: DbSession):
    document_service.delete_document(db, document_id)