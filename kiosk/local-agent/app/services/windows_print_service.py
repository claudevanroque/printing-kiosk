import time
import datetime
import subprocess
import sys
from pathlib import Path
import win32print
from fastapi import HTTPException

from app.schemas.windows_print import WindowsPrintResult
from app.core.config import settings
from app.services import printer_service

SUMATRA_PATH = Path(settings.sumatra_path)


def get_installed_printer_names() -> list[str]:
    printer_data = printer_service.list_windows_printers()
    return [printer["name"] for printer in printer_data]


def get_spooler_jobs(
    printer_name: str,
) -> list[dict]:
    """
    Inspect currently visible jobs in a Windows print queue.
    """

    handle = None

    try:
        handle = win32print.OpenPrinter(printer_name)

        jobs = win32print.EnumJobs(
            handle,
            0,
            100,
            1,
        )

        return [
            {
                "job_id": job["JobId"],
                "document": job.get("pDocument"),
                "status": job.get("Status", 0),
                "pages_printed": job.get("PagesPrinted", 0),
                "total_pages": job.get("TotalPages", 0),
            }
            for job in jobs
        ]

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to inspect Windows print queue.",
        ) from exc

    finally:
        if handle is not None:
            win32print.ClosePrinter(handle)

def get_spooler_job_snapshot(printer_name: str,) -> dict[int, dict]:
    """
    Return currently visible Windows spooler jobs,
    indexed by their job IDs.

    This is diagnostic data, not proof of physical
    printing or completion.
    """
    jobs = get_spooler_jobs(printer_name)

    return {
        int(job["job_id"]): job
        for job in jobs
    }


def find_new_spooler_jobs(printer_name: str, before_job_ids: set[int]) -> list[dict]:
    """
    Find jobs visible after submission that were
    not present in the earlier queue snapshot.
    """
    current_jobs = get_spooler_jobs(printer_name)

    return [
        job
        for job in current_jobs
        if int(job["job_id"]) not in before_job_ids
    ]


def submit_test_pdf_with_tracking(
    pdf_path: Path,
    printer_name: str,
    copies: int = 1,
    paper_size: str = "A4",
    orientation: str = "portrait",
    color_mode: str = "bw",
) -> dict:
    """
    Submit a test PDF and inspect newly visible
    Windows spooler jobs.

    Newly observed jobs are candidates only.
    Their ownership is not verified.
    """

    before = get_spooler_job_snapshot(
        printer_name
    )

    result = submit_test_pdf(
        pdf_path=pdf_path,
        printer_name=printer_name,
        copies=copies,
        paper_size=paper_size,
        orientation=orientation,
        color_mode=color_mode,
    )

    candidates = []

    # The spooler may process a job before we inspect it.
    # Poll briefly, without assuming a missing job means
    # the document was physically printed.
    for _ in range(5):
        candidates = find_new_spooler_jobs(
            printer_name=printer_name,
            before_job_ids=set(before),
        )

        if candidates:
            break

        time.sleep(0.2)

    return {
        "printer_name": printer_name,
        "submitted": result.submitted,
        "spooler_job_id": None,
        "candidate_spooler_jobs": candidates,
        "tracking_verified": False,
        "message": (
            "Print command submitted. Newly observed "
            "spooler jobs are unverified candidates."
        ),
    }



def submit_test_pdf(
    pdf_path: Path,
    printer_name: str,
    copies: int = 1,
    paper_size: str = "A4",
    orientation: str = "portrait",
    color_mode: str = "bw",
) -> WindowsPrintResult:
    """
    Submit a local test PDF through SumatraPDF.

    This function is not connected to ServiceJob
    or customer payment processing.
    """

    if sys.platform != "win32":
        raise HTTPException(
            status_code=501,
            detail="Windows printing is required.",
        )

    pdf_path = Path(pdf_path).resolve()

    if not SUMATRA_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="SumatraPDF.exe is missing.",
        )

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Test PDF file not found.",
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=422,
            detail="Only PDF documents are supported.",
        )

    if not 1 <= copies <= 1000:
        raise HTTPException(
            status_code=422,
            detail="Copies must be between 1 and 1000.",
        )

    supported_papers = {
        "A4": "paper=A4",
        "SHORT": "paper=letter",
        "LONG": None,
    }

    if paper_size not in supported_papers:
        raise HTTPException(
            status_code=422,
            detail="Unsupported paper size.",
        )

    if orientation not in ("portrait", "landscape"):
        raise HTTPException(
            status_code=422,
            detail="Unsupported orientation.",
        )

    if color_mode not in ("bw", "color"):
        raise HTTPException(
            status_code=422,
            detail="Unsupported color mode.",
        )

    printers = get_installed_printer_names()

    if printer_name not in printers:
        raise HTTPException(
            status_code=404,
            detail="Selected printer is not installed.",
        )

    # SumatraPDF accepts comma-separated print settings.
    # LONG (8.5 x 13) is not mapped to Legal (8.5 x 14).
    # Custom-size printing requires printer-specific support.
    settings_parts = [
        f"{copies}x",
        orientation,
        "monochrome" if color_mode == "bw" else "color",
        "fit",
    ]

    paper_setting = supported_papers[paper_size]

    if paper_setting is not None:
        settings_parts.append(paper_setting)
    else:
        raise HTTPException(
            status_code=422,
            detail=(
                "LONG paper requires a configured "
                "8.5 x 13 printer form. "
                "Custom paper support will be handled "
                "during printer capability integration."
            ),
        )

    print_settings = ",".join(settings_parts)

    command = [
        str(SUMATRA_PATH),
        "-print-to",
        printer_name,
        "-print-settings",
        print_settings,
        "-silent",
        str(pdf_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=504,
            detail=(
                "Print command timed out. "
                "Inspect the Windows print queue "
                "before retrying."
            ),
        ) from exc

    except OSError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to launch SumatraPDF.",
        ) from exc

    if result.returncode != 0:
        raise HTTPException(
            status_code=502,
            detail=(
                "SumatraPDF reported a printing error. "
                "Check printer status and driver settings."
            ),
        )

    return WindowsPrintResult(
        printer_name=printer_name,
        submitted=True,
        spooler_job_id=None,
        message=(
            "Print command completed. "
            "Check the Windows print queue "
            "and physical printer."
        ),
    )

def submit_prepared_pdf(
    pdf_path: Path,
    printer_name: str,
    copies: int,
    paper_size: str,
    orientation: str,
    color_mode: str,
) -> WindowsPrintResult:
    """
    Submit an already-prepared customer PDF.

    Payment authorization is handled by the queue
    service, not by this low-level print adapter.
    """

    if paper_size not in ("A4", "SHORT"):
        raise ValueError(
            "Unsupported paper size for this print adapter."
        )

    if orientation not in ("portrait", "landscape"):
        raise ValueError(
            "Unsupported orientation for this print adapter."
        )

    return submit_test_pdf(
        pdf_path=pdf_path,
        printer_name=printer_name,
        copies=copies,
        paper_size=paper_size,
        orientation=orientation,
        color_mode=color_mode,
    )