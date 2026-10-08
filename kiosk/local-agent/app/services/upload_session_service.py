import secrets
import sqlite3

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.database import get_connection
from app.schemas.document import DocumentSource
from app.schemas.upload_session import (
    UploadSessionResponse,
    UploadSessionStatus,
)
from app.services.document_service import (
    get_document,
    save_document,
)
from app.core import network


def _now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def _create_upload_url(token: str,) -> str:
    base_url = (settings.local_public_base_url.rstrip("/"))
    return (f"{base_url}/upload/{token}")


def _row_to_session(row: sqlite3.Row,) -> UploadSessionResponse:
    document = None

    if row["document_id"]:
        document = get_document(row["document_id"])

    return UploadSessionResponse(
        id=row["id"],
        status=row["status"],
        upload_url=_create_upload_url(row["token"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]),
        document=document,
    )


def create_upload_session() -> UploadSessionResponse:
    from uuid import uuid4
    session_id = str(uuid4())
    token = secrets.token_urlsafe(32)

    created_at = _now()

    expires_at = (created_at +timedelta(minutes=settings.session_ttl_minutes))

    with get_connection() as connection:
        try:
            connection.execute(
                """
                INSERT INTO upload_sessions (
                    id,
                    token,
                    status,
                    document_id,
                    created_at,
                    expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    token,
                    UploadSessionStatus.WAITING.value,
                    None,
                    created_at.isoformat(),
                    expires_at.isoformat(),
                ),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    return get_upload_session(
        session_id
    )


def get_upload_session(session_id: str,) -> UploadSessionResponse:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM upload_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Upload session not found.",
        )

    if (row["status"] == UploadSessionStatus.WAITING.value):
        expires_at = datetime.fromisoformat(row["expires_at"])

        if _now() >= expires_at:
            with get_connection() as connection:
                connection.execute(
                    """
                    UPDATE upload_sessions
                    SET status = ?
                    WHERE id = ?
                    """,
                    (
                        UploadSessionStatus.EXPIRED.value,
                        session_id,
                    ),
                )

                connection.commit()

            return get_upload_session(session_id)

    return _row_to_session(row)


def get_session_by_token(token: str) -> sqlite3.Row:

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM upload_sessions
            WHERE token = ?
            """,
            (token,),
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Invalid upload session.",
        )

    expires_at = datetime.fromisoformat(
        row["expires_at"]
    )

    if _now() >= expires_at:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE upload_sessions
                SET status = ?
                WHERE id = ?
                """,
                (
                    UploadSessionStatus.EXPIRED.value,
                    row["id"],
                ),
            )

            connection.commit()

        raise HTTPException(
            status_code=410,
            detail="Upload session expired.",
        )

    return row


async def upload_to_session(token: str, upload: UploadFile,) -> UploadSessionResponse:
    row = get_session_by_token(token)

    if (row["status"] != UploadSessionStatus.WAITING.value):
        raise HTTPException(
            status_code=409,
            detail=(
                "This upload session "
                "has already been used."
            ),
        )

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE upload_sessions
            SET status = ?
            WHERE id = ?
            """,
            (
                UploadSessionStatus.UPLOADING.value,
                row["id"],
            ),
        )

        connection.commit()

    try:
        document = await save_document(
            upload,
            DocumentSource.QR,
        )

        with get_connection() as connection:
            try:
                connection.execute(
                    """
                    UPDATE upload_sessions
                    SET
                        status = ?,
                        document_id = ?
                    WHERE id = ?
                    """,
                    (
                        UploadSessionStatus.READY.value,
                        document.id,
                        row["id"],
                    ),
                )

                connection.commit()

            except Exception:
                connection.rollback()
                raise

    except Exception:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE upload_sessions
                SET status = ?
                WHERE id = ?
                """,
                (
                    UploadSessionStatus.FAILED.value,
                    row["id"],
                ),
            )

            connection.commit()

        raise

    return get_upload_session(
        row["id"]
    )