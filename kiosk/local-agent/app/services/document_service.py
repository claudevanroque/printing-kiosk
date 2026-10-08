import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import Image
from pypdf import PdfReader

from app.core.config import settings
from app.core.database import get_connection
from app.schemas.document import (
    DocumentResponse,
    DocumentSource,
)


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


def _row_to_document(row: sqlite3.Row) -> DocumentResponse:
    return DocumentResponse(
        id=row["id"],
        original_filename=row["original_filename"],
        content_type=row["content_type"],
        extension=row["extension"],
        file_size=row["file_size"],
        page_count=row["page_count"],
        source=row["source"],
        created_at=datetime.fromisoformat(
            row["created_at"]
        ),
        preview_url=f"/api/documents/{row['id']}/file",
    )


def get_document(document_id: str) -> DocumentResponse | None:

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()

    if not row:
        return None

    return _row_to_document(row)


def get_document_record(document_id: str) -> sqlite3.Row | None:

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()


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


def _validate_image(
    path: Path,
    extension: str,
) -> int:

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


async def save_document(upload: UploadFile, source: DocumentSource) -> DocumentResponse:

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

        created_at = datetime.now(timezone.utc)

        try:
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO documents (
                        id,
                        original_filename,
                        stored_filename,
                        content_type,
                        extension,
                        file_size,
                        page_count,
                        source,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        original_filename,
                        stored_filename,
                        content_type,
                        extension,
                        total_size,
                        page_count,
                        source.value,
                        created_at.isoformat(),
                    ),
                )

                connection.commit()

        except Exception:
            destination.unlink(missing_ok=True)
            raise

        document = get_document(document_id)

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


def delete_document(document_id: str,) -> None:
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

    with get_connection() as connection:
        try:
            connection.execute(
                """
                DELETE FROM documents
                WHERE id = ?
                """,
                (document_id,),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    path.unlink(
        missing_ok=True
    )