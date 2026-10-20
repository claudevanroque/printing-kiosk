from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_local_db
from app.schemas.printer import PrinterResponse, PrinterAssignmentRequest, PrinterAssignmentResponse
from app.services import printer_service, print_preparation_service
from app.services.printer_status_service import PrinterStatusError, get_printer_jobs, get_printer_status

from app.services.windows_print_service import get_installed_printer_names

router = APIRouter(
    prefix="/printers",
    tags=["printers"]
)

@router.get("/assignments", response_model=list[PrinterAssignmentResponse])
def list_assignments(db: Session = Depends(get_local_db)):
    return printer_service.get_printer_assignments(db)


@router.put("/assignments", response_model=PrinterAssignmentResponse,)
def update_assignment(payload: PrinterAssignmentRequest, db: Session = Depends(get_local_db)):
    return printer_service.assign_printer(db, payload)

@router.get("/assignments/{paper_size}", response_model=PrinterAssignmentResponse)
def get_assignment(paper_size: str, db: Session = Depends(get_local_db)):
    return printer_service.get_assigned_printer(db, paper_size)

@router.get("/", response_model=list[PrinterResponse])
def list_printers():
    return printer_service.list_windows_printers()

@router.post("/prepare/{service_job_id}", response_model=dict)
def prepare_job(service_job_id: str, db: Session = Depends(get_local_db)):
    return print_preparation_service.prepare_print_job(db, service_job_id)


@router.get("/status")
def printer_status(printer_name: str = Query(min_length=1)):
    try:
        if printer_name not in get_installed_printer_names():
            raise HTTPException(
                status_code=404,
                detail="Printer not installed.",
            )

        return get_printer_status(printer_name)

    except PrinterStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


@router.get("/jobs")
def printer_jobs(printer_name: str = Query(min_length=1),):
    try:
        if printer_name not in get_installed_printer_names():
            raise HTTPException(
                status_code=404,
                detail="Printer not installed.",
            )

        return {
            "printer_name": printer_name,
            "jobs": get_printer_jobs(printer_name),
        }

    except PrinterStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
