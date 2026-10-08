from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.upload_session import UploadSession
from app.schemas.upload_session import UploadSessionStatus

class UploadSessionRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, session_id: str) -> UploadSession | None:
        statement = select(UploadSession).where(UploadSession.id == session_id)
        return self.db.scalar(statement)
    
    def get_by_token(self, token: str) -> UploadSession | None:
        statement = select(UploadSession).where(UploadSession.token == token)
        return self.db.scalar(statement)
    
    def create(self, upload_session: UploadSession) -> UploadSession:
        self.db.add(upload_session)
        self.db.flush()
        return upload_session
    
    def update_status(self, session_id: str, status: UploadSessionStatus) -> UploadSession | None:
        statement = (
            update(UploadSession)
            .where(UploadSession.id == session_id)
            .values(status=status)
        )
        self.db.execute(statement)
    
    def claim_for_upload(self, session_id: str, now: datetime) -> bool:
        statement = (
            update(UploadSession)
            .where(
                UploadSession.id == session_id,
                UploadSession.status
                == UploadSessionStatus.WAITING.value,
                UploadSession.expires_at > now,
            )
            .values(
                status=UploadSessionStatus.UPLOADING.value
            )
        )
        result = self.db.execute(
            statement,
            execution_options={"synchronize_session": "fetch"},
        )
        return result.rowcount ==1
    
    def mark_ready(self, session_id: str, document_id: str) -> bool:
        statement = (
            update(UploadSession)
            .where(
                UploadSession.id == session_id,
                UploadSession.status == UploadSessionStatus.UPLOADING.value,
            )
            .values(
                status=UploadSessionStatus.READY.value,
                document_id=document_id,
            )
        )
        result = self.db.execute(statement)
        return result.rowcount == 1
    
    def mark_failed(self, session_id: str) -> bool:
        statement = (
            update(UploadSession)
            .where(
                UploadSession.id == session_id,
                UploadSession.status == UploadSessionStatus.UPLOADING.value,
            )
            .values(
                status=UploadSessionStatus.FAILED.value,
            )
        )
        result = self.db.execute(statement)
        return result.rowcount == 1
    
    def expire_waiting(self, session_id: str, now: datetime) -> bool:
        statement = (
            update(UploadSession)
            .where(
                UploadSession.id == session_id,
                UploadSession.status == UploadSessionStatus.WAITING.value,
                UploadSession.expires_at <= now,
            )
            .values(
                status=UploadSessionStatus.EXPIRED.value,
            )
        )
        result = self.db.execute(
            statement,
            execution_options={"synchronize_session": "fetch"},
        )
        return result.rowcount == 1