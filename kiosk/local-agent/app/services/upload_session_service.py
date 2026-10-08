
import secrets

from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.datetime_utils import as_utc, utc_now
from app.models.upload_session import UploadSession
from app.repositories.upload_session_repository import (
    UploadSessionRepository,
)
from app.schemas.document import DocumentSource
from app.schemas.upload_session import (
    UploadSessionResponse,
    UploadSessionStatus,
)
from app.services.document_service import (
    get_document,
    save_document,
)


def _create_upload_url(token: str) -> str:
    base_url = settings.local_public_base_url.rstrip("/")
    return f"{base_url}/upload/{token}"


def _to_session_response(db: Session, upload_session: UploadSession) -> UploadSessionResponse:
    document = None

    if upload_session.document_id:
        document = get_document(
            db,
            upload_session.document_id,
        )

    return UploadSessionResponse(
        id=upload_session.id,
        document=document,
        status=upload_session.status,
        upload_url=_create_upload_url(
            upload_session.token
        ),
        created_at=as_utc(upload_session.created_at),
        expires_at=as_utc(upload_session.expires_at),
    )


def create_upload_session(db: Session,) -> UploadSessionResponse:
    repository = UploadSessionRepository(db)

    created_at = utc_now()
    expires_at = created_at + timedelta(
        minutes=settings.session_ttl_minutes
    )

    upload_session = UploadSession(
        id=str(uuid4()),
        token=secrets.token_urlsafe(32),
        status=UploadSessionStatus.WAITING.value,
        document_id=None,
        created_at=created_at,
        expires_at=expires_at,
    )

    try:
        repository.create(upload_session)
        response = _to_session_response(
            db,
            upload_session,
        )
        db.commit()

        return response

    except Exception:
        db.rollback()
        raise


def get_upload_session(db: Session,session_id: str,) -> UploadSessionResponse:
    repository = UploadSessionRepository(db)

    upload_session = repository.get_by_id(session_id)

    if upload_session is None:
        raise HTTPException(
            status_code=404,
            detail="Upload session not found.",
        )

    expires_at = as_utc(upload_session.expires_at)

    if (upload_session.status == UploadSessionStatus.WAITING.value and utc_now() >= expires_at):
        try:
            repository.expire_waiting(
                session_id,
                utc_now(),
            )
            db.commit()
            db.refresh(upload_session)

        except Exception:
            db.rollback()
            raise

    return _to_session_response(
        db,
        upload_session,
    )


def get_session_by_token(db: Session, token: str) -> UploadSession:
    repository = UploadSessionRepository(db)

    upload_session = repository.get_by_token(token)

    if upload_session is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid upload session.",
        )

    expires_at = as_utc(upload_session.expires_at)

    if utc_now() >= expires_at:
        if (
            upload_session.status
            == UploadSessionStatus.WAITING.value
        ):
            try:
                repository.expire_waiting(
                    upload_session.id,
                    utc_now(),
                )
                db.commit()

            except Exception:
                db.rollback()
                raise

        raise HTTPException(
            status_code=410,
            detail="Upload session expired.",
        )

    return upload_session


async def upload_to_session(db: Session, token: str, upload: UploadFile) -> UploadSessionResponse:
    repository = UploadSessionRepository(db)

    upload_session = get_session_by_token(db, token)

    session_id = upload_session.id

    if (
        upload_session.status
        != UploadSessionStatus.WAITING.value
    ):
        raise HTTPException(
            status_code=409,
            detail="This upload session has already been used.",
        )

    try:
        claimed = repository.claim_for_upload(session_id, utc_now())

        db.commit()

    except Exception:
        db.rollback()
        raise

    if not claimed:
        raise HTTPException(
            status_code=409,
            detail="Upload session is no longer available.",
        )

    try:
        document = await save_document(db, upload, DocumentSource.QR)

        updated = repository.mark_ready(session_id, document.id)

        if not updated:
            raise RuntimeError(
                "Could not finalize upload session."
            )

        db.commit()

    except Exception:
        db.rollback()

        try:
            repository.mark_failed(session_id)
            db.commit()
        except Exception:
            db.rollback()
            raise

        raise

    return get_upload_session(
        db,
        session_id,
    )
