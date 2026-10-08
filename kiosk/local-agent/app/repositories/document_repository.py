from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.upload_session import UploadSession

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: str) -> Document | None:
        return self.db.get(Document, document_id)

    def get_all(self) -> list[Document]:
        stmt = select(Document).order_by(Document.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.flush()
        return document
    
    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.flush()

    def unlink_upload_session(self, document_id: str) -> None:
        stmt = (
            update(UploadSession)
            .where(UploadSession.document_id == document_id)
            .values(document_id=None)
        )
        self.db.execute(stmt)
        self.db.flush()