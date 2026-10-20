
import hashlib
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.repositories.service_job_repository import (
    ServiceJobRepository,
)
from app.repositories.printer_assignment_repository import (
    PrinterAssignmentRepository,
)
from app.services.printer_service import list_windows_printers
from app.core.utils import calculate_sha256


# PDF dimensions use points: 72 points = 1 inch.
PAPER_SIZES = {
    "A4": (595.44, 841.68),
    "SHORT": (612.0, 792.0),  # 8.5 x 11
    "LONG": (612.0, 936.0),   # 8.5 x 13
}

SUPPORTED_ORIENTATIONS = {
    "auto",
    "portrait",
    "landscape",
}

SUPPORTED_COLORS = {"bw", "color"}


def get_paper_dimensions(paper_size: str, orientation: str) -> tuple[float, float]:
    dimensions = PAPER_SIZES.get(paper_size.upper())

    if dimensions is None:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported paper size: {paper_size}",
        )

    width, height = dimensions

    if orientation == "landscape":
        return height, width

    if orientation == "portrait":
        return width, height

    raise HTTPException(
        status_code=422,
        detail=f"Unsupported orientation: {orientation}",
    )


def prepare_pdf(source_path: Path, destination_path: Path, paper_size: str, orientation: str) -> int:
    try:
        reader = PdfReader(str(source_path), strict=False)

        if reader.is_encrypted:
            raise HTTPException(
                status_code=422,
                detail="Encrypted PDFs are not supported.",
            )

        if len(reader.pages) == 0:
            raise HTTPException(
                status_code=422,
                detail="PDF contains no pages.",
            )

        writer = PdfWriter()

        for source_page in reader.pages:
            # Normalize PDF rotation before fitting.
            if source_page.rotation:
                source_page.transfer_rotation_to_content()

            source_box = source_page.cropbox

            source_width = float(source_box.width)
            source_height = float(source_box.height)

            if source_width <= 0 or source_height <= 0:
                raise HTTPException(
                    status_code=422,
                    detail="Invalid PDF page dimensions.",
                )

            effective_orientation = orientation

            if orientation == "auto":
                effective_orientation = (
                    "landscape"
                    if source_width > source_height
                    else "portrait"
                )

            target_width, target_height = get_paper_dimensions(
                paper_size,
                effective_orientation,
            )

            margin = 18.0

            available_width = target_width - 2 * margin
            available_height = target_height - 2 * margin

            scale = min(
                available_width / source_width,
                available_height / source_height,
            )

            draw_width = source_width * scale
            draw_height = source_height * scale

            offset_x = (target_width - draw_width) / 2
            offset_y = (target_height - draw_height) / 2

            left = float(source_box.left)
            bottom = float(source_box.bottom)

            transform = (
                Transformation()
                .translate(-left, -bottom)
                .scale(scale)
                .translate(offset_x, offset_y)
            )

            output_page = writer.add_blank_page(
                width=target_width,
                height=target_height,
            )

            output_page.merge_transformed_page(
                source_page,
                transform,
                expand=False,
            )

        with destination_path.open("wb") as file:
            writer.write(file)

        return len(writer.pages)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Unable to prepare PDF.",
        ) from exc


def prepare_image(source_path: Path, destination_path: Path, paper_size: str, orientation: str, color_mode: str) -> int:
    try:
        with Image.open(source_path) as original:
            image = ImageOps.exif_transpose(original)

            width, height = image.size

            if width <= 0 or height <= 0:
                raise ValueError("Invalid image dimensions.")

            effective_orientation = orientation

            if orientation == "auto":
                effective_orientation = (
                    "landscape"
                    if width > height
                    else "portrait"
                )

            paper_width, paper_height = get_paper_dimensions(
                paper_size,
                effective_orientation,
            )

            if color_mode == "bw":
                image = image.convert("L")
            else:
                image = image.convert("RGB")

            margin = 18.0

            available_width = paper_width - 2 * margin
            available_height = paper_height - 2 * margin

            scale = min(
                available_width / width,
                available_height / height,
            )

            draw_width = width * scale
            draw_height = height * scale

            x = (paper_width - draw_width) / 2
            y = (paper_height - draw_height) / 2

            image_buffer = BytesIO()
            image.save(image_buffer, format="PNG")
            image_buffer.seek(0)

            pdf = canvas.Canvas(
                str(destination_path),
                pagesize=(paper_width, paper_height),
            )

            pdf.drawImage(
                ImageReader(image_buffer),
                x,
                y,
                width=draw_width,
                height=draw_height,
            )

            pdf.showPage()
            pdf.save()

        return 1

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Unable to prepare image.",
        ) from exc


def prepare_print_job(db: Session, service_job_id: str) -> dict:
    service_job_repository = ServiceJobRepository(db)

    job = service_job_repository.get_by_id(service_job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Service job not found.",
        )

    if job.service_type != "print":
        raise HTTPException(
            status_code=422,
            detail="Only print jobs are supported.",
        )

    if not job.document_id:
        raise HTTPException(
            status_code=422,
            detail="Print job has no document.",
        )

    if job.status not in ("pending_payment", "paid"):
        raise HTTPException(
            status_code=409,
            detail="Job cannot be prepared in its current state.",
        )

    if job.orientation not in SUPPORTED_ORIENTATIONS:
        raise HTTPException(
            status_code=422,
            detail="Unsupported orientation.",
        )

    if job.color_mode not in SUPPORTED_COLORS:
        raise HTTPException(
            status_code=422,
            detail="Unsupported color mode.",
        )

    if not job.paper_size:
        raise HTTPException(
            status_code=422,
            detail="Paper size is missing.",
        )

    # Validate the configured paper size.
    get_paper_dimensions(job.paper_size, job.orientation)

    document = db.get(Document, job.document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    storage_directory = Path(settings.temp_path).resolve()

    source_path = (
        storage_directory / document.stored_filename
    ).resolve()

    # Do not allow a stored filename to escape its directory.
    if source_path.parent != storage_directory:
        raise HTTPException(
            status_code=422,
            detail="Invalid stored document path.",
        )

    if not source_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Original document file is missing.",
        )

    try:
        actual_hash = calculate_sha256(source_path)
    except OSError as exc:
        raise HTTPException(
            status_code=409,
            detail="Cannot read original document.",
        ) from exc

    if (
        not job.document_sha256
        or actual_hash != job.document_sha256
    ):
        raise HTTPException(
            status_code=409,
            detail="Document does not match locked job.",
        )

    assignment_repository = PrinterAssignmentRepository(db)

    assignment = assignment_repository.get_by_paper_size(
        job.paper_size
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="No printer assigned to this paper size.",
        )

    installed_printers = list_windows_printers()

    if not any(
        printer["name"] == assignment.printer_name
        for printer in installed_printers
    ):
        raise HTTPException(
            status_code=503,
            detail="Assigned printer is not installed.",
        )

    prepared_directory = storage_directory / "prepared"
    prepared_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # UUID job IDs should contain no path separators.
    # Reject unexpected IDs before using them in filenames.
    from uuid import UUID

    try:
        safe_job_id = str(UUID(str(job.id)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Invalid job ID.",
        ) from exc

    destination_path = (
        prepared_directory / f"{safe_job_id}.pdf"
    )

    temporary_path = (
        prepared_directory / f"{safe_job_id}.partial.pdf"
    )

    try:
        extension = document.extension.lower().lstrip(".")

        if extension == "pdf":
            prepared_pages = prepare_pdf(
                source_path=source_path,
                destination_path=temporary_path,
                paper_size=job.paper_size,
                orientation=job.orientation,
            )

        elif extension in ("jpg", "jpeg", "png"):
            prepared_pages = prepare_image(
                source_path=source_path,
                destination_path=temporary_path,
                paper_size=job.paper_size,
                orientation=job.orientation,
                color_mode=job.color_mode,
            )

        else:
            raise HTTPException(
                status_code=422,
                detail="Unsupported document format.",
            )

        if prepared_pages != job.page_count:
            raise HTTPException(
                status_code=409,
                detail="Prepared page count differs from locked job.",
            )

        # Validate the output before publishing it.
        prepared_reader = PdfReader(str(temporary_path))

        if len(prepared_reader.pages) != job.page_count:
            raise HTTPException(
                status_code=409,
                detail="Prepared PDF page count mismatch.",
            )

        temporary_path.replace(destination_path)

    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return {
        "job_id": job.id,
        "document_id": document.id,
        "printer_name": assignment.printer_name,
        "paper_size": job.paper_size,
        "color_mode": job.color_mode,
        "orientation": job.orientation,
        "copies": job.copies,
        "page_count": job.page_count,
        "total_pages": job.total_pages,
        "prepared_file": destination_path.name,
        "prepared_page_count": prepared_pages,
        "status": "prepared",
    }
