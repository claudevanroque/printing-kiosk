from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.document import (
    DocumentResponse,
    DocumentSource,
)

from app.services.document_service import (
    delete_document,
    get_document,
    get_document_record,
    save_document,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post("/upload",response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
):
    return await save_document(
        file,
        DocumentSource.USB,
    )


@router.get("/{document_id}",response_model=DocumentResponse)
def document_details(document_id: str):
    document = get_document(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document


@router.get("/{document_id}/file")
def document_file(document_id: str,):
    record = get_document_record(document_id)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    path = (
        settings.temp_path /
        record["stored_filename"]
    )

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document file is missing.",
        )

    return FileResponse(
        path=path,
        media_type=record["content_type"],
        filename=record["original_filename"],
        content_disposition_type="inline",
    )


@router.delete(
    "/{document_id}",
    status_code=204,
)
def remove_document(
    document_id: str,
):
    delete_document(
        document_id
    )