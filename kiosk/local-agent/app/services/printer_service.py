
import sys

from fastapi import HTTPException
import win32print
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.printer_assignment_repository import PrinterAssignmentRepository
from app.repositories.local_pricing_repository import LocalPricingRepository
from app.schemas.printer import PrinterAssignmentRequest


def get_printer_assignments(db: Session):
    repository = PrinterAssignmentRepository(db)
    return repository.get_all()


def assign_printer(db: Session,  payload: PrinterAssignmentRequest,):
    paper_size = payload.paper_size.strip()
    printer_name = payload.printer_name.strip()
    valid_paper_size = LocalPricingRepository(db).valid_paper_size(paper_size)

    if not paper_size or not printer_name:
        raise HTTPException(
            status_code=422,
            detail="Paper size and printer name cannot be blank.",
        )

    if not valid_paper_size:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid paper size: {paper_size}. This paper size is not supported.",
        )

    available_printers = list_windows_printers()

    if not any(
        printer["name"] == printer_name
        for printer in available_printers
    ):
        raise HTTPException(
            status_code=404,
            detail="Printer is not installed in Windows.",
        )

    repository = PrinterAssignmentRepository(db)

    try:
        assignment = repository.save(
            paper_size=paper_size,
            printer_name=printer_name,
        )

        db.commit()
        db.refresh(assignment)

        return assignment

    except Exception:
        db.rollback()
        raise


def get_assigned_printer(db: Session, paper_size: str):
    repository = PrinterAssignmentRepository(db)

    assignment = repository.get_by_paper_size(paper_size)

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail=f"No printer assigned for {paper_size}.",
        )

    available_printers = list_windows_printers()

    if not any(
        printer["name"] == assignment.printer_name
        for printer in available_printers
    ):
        raise HTTPException(
            status_code=503,
            detail="Assigned printer is no longer installed.",
        )

    return assignment

def list_windows_printers() -> list[dict]:
    if sys.platform != "win32":
        raise HTTPException(
            status_code=501,
            detail="Printer discovery requires Windows.",
        )

    try:
        flags = (
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )

        printers = win32print.EnumPrinters(flags, None, 2)

        try:
            default_printer = win32print.GetDefaultPrinter()
        except Exception:
            default_printer = None

        results = []

        for printer in printers:
            name = printer["pPrinterName"]

            results.append(
                {
                    "name": name,
                    "driver_name": printer.get("pDriverName"),
                    "port_name": printer.get("pPortName"),
                    "is_default": name == default_printer,
                    "status_code": printer.get("Status", 0),
                    "jobs_count": printer.get("cJobs", 0),
                }
            )

        return sorted(
            results,
            key=lambda printer: printer["name"].lower()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to enumerate Windows printers.",
        ) from exc
