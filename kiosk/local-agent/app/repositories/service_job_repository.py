from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service_job import ServiceJob


class ServiceJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, job: ServiceJob) -> ServiceJob:
        self.db.add(job)
        self.db.flush()
        return job

    def get_by_id(self, job_id: str) -> ServiceJob | None:
        return self.db.get(ServiceJob, job_id)

    def document_has_jobs(self, document_id: str) -> bool:
        statement = (
            select(ServiceJob.id)
            .where(
                ServiceJob.document_id == document_id
            )
            .limit(1)
        )

        return self.db.scalar(statement) is not None