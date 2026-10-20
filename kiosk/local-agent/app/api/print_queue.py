
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_local_db
from app.repositories.print_execution_repository import (
    PrintExecutionRepository,
)
from app.schemas.print_execution import (
    PrintExecutionResponse,
)
from app.services.print_tracking_service import (
    get_execution_tracking,
)
from app.services.windows_print_service import (
    get_spooler_jobs,
)


router = APIRouter(
    prefix="/print-queue",
    tags=["Print Queue"],
)

DbSession = Annotated[
    Session,
    Depends(get_local_db),
]


@router.get(
    "",
    response_model=list[PrintExecutionResponse],
)
def list_print_queue(db: DbSession):
    return PrintExecutionRepository(db).list_all()


@router.get(
    "/service-jobs/{job_id}",
    response_model=list[PrintExecutionResponse],
)
def get_job_executions(
    job_id: str,
    db: DbSession,
):
    return (
        PrintExecutionRepository(db)
        .get_by_service_job_id(job_id)
    )


@router.get(
    "/{execution_id}/tracking",
)
def get_print_execution_tracking(
    execution_id: str,
    db: DbSession,
):
    """
    Read-only tracking endpoint.

    Does not print, retry, or complete jobs.
    """

    try:
        return get_execution_tracking(
            db=db,
            execution_id=execution_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve print tracking information.",
        ) from exc


@router.get(
    "/{execution_id}",
    response_model=PrintExecutionResponse,
)
def get_execution(
    execution_id: str,
    db: DbSession,
):
    execution = (
        PrintExecutionRepository(db)
        .get_by_id(execution_id)
    )

    if execution is None:
        raise HTTPException(
            status_code=404,
            detail="Print execution not found.",
        )

    return execution
