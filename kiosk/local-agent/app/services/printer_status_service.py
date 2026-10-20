
import logging
import sys

import win32print

logger = logging.getLogger(__name__)


class PrinterStatusError(Exception):
    pass


# Driver-reported status flags.
PRINTER_STATUS_FLAGS = {
    "paused": win32print.PRINTER_STATUS_PAUSED,
    "error": win32print.PRINTER_STATUS_ERROR,
    "pending_deletion": win32print.PRINTER_STATUS_PENDING_DELETION,
    "paper_jam": win32print.PRINTER_STATUS_PAPER_JAM,
    "paper_out": win32print.PRINTER_STATUS_PAPER_OUT,
    "manual_feed": win32print.PRINTER_STATUS_MANUAL_FEED,
    "paper_problem": win32print.PRINTER_STATUS_PAPER_PROBLEM,
    "offline": win32print.PRINTER_STATUS_OFFLINE,
    "io_active": win32print.PRINTER_STATUS_IO_ACTIVE,
    "busy": win32print.PRINTER_STATUS_BUSY,
    "printing": win32print.PRINTER_STATUS_PRINTING,
    "output_bin_full": win32print.PRINTER_STATUS_OUTPUT_BIN_FULL,
    "not_available": win32print.PRINTER_STATUS_NOT_AVAILABLE,
    "waiting": win32print.PRINTER_STATUS_WAITING,
    "processing": win32print.PRINTER_STATUS_PROCESSING,
    "initializing": win32print.PRINTER_STATUS_INITIALIZING,
    "warming_up": win32print.PRINTER_STATUS_WARMING_UP,
    "toner_low": win32print.PRINTER_STATUS_TONER_LOW,
    "no_toner": win32print.PRINTER_STATUS_NO_TONER,
    "page_punt": win32print.PRINTER_STATUS_PAGE_PUNT,
    "user_intervention": win32print.PRINTER_STATUS_USER_INTERVENTION,
    "out_of_memory": win32print.PRINTER_STATUS_OUT_OF_MEMORY,
    "door_open": win32print.PRINTER_STATUS_DOOR_OPEN,
    "server_unknown": win32print.PRINTER_STATUS_SERVER_UNKNOWN,
    "power_save": win32print.PRINTER_STATUS_POWER_SAVE,
}

BLOCKING_FLAGS = {
    "paused",
    "error",
    "pending_deletion",
    "paper_jam",
    "paper_out",
    "paper_problem",
    "offline",
    "output_bin_full",
    "not_available",
    "no_toner",
    "user_intervention",
    "out_of_memory",
    "door_open",
    "server_unknown",
}




def get_printer_status(printer_name: str) -> dict:
    if sys.platform != "win32":
        raise PrinterStatusError(
            "Windows printer monitoring is required."
        )

    handle = None

    try:
        handle = win32print.OpenPrinter(printer_name)
        printer = win32print.GetPrinter(handle, 2)

        status_code = int(
            printer.get("Status") or 0
        )

        active_flags = [
            name
            for name, flag in PRINTER_STATUS_FLAGS.items()
            if status_code & flag
        ]

        is_paused = "paused" in active_flags

        is_blocked = bool(
            BLOCKING_FLAGS.intersection(active_flags)
        )

        return {
            "printer_name": printer_name,
            "reachable_via_spooler": True,
            "status_code": status_code,
            "status_flags": active_flags,
            "is_paused": is_paused,
            "is_blocked": is_blocked,
            "can_submit": not is_blocked,
            "status_known": status_code != 0,
        }

    except Exception as exc:
        logger.exception(
            "Unable to inspect printer %s",
            printer_name,
        )

        raise PrinterStatusError(
            f"Unable to inspect printer: {printer_name}"
        ) from exc

    finally:
        if handle is not None:
            win32print.ClosePrinter(handle)

def get_printer_jobs(printer_name: str) -> list[dict]:
    handle = None

    try:
        handle = win32print.OpenPrinter(printer_name)

        jobs = win32print.EnumJobs(handle, 0, 100, 1)

        return [
            {
                "job_id": job["JobId"],
                "document": job.get("pDocument"),
                "status_code": job.get("Status", 0),
                "status_text": job.get("pStatus"),
                "pages_printed": job.get("PagesPrinted", 0),
                "total_pages": job.get("TotalPages", 0),
            }
            for job in jobs
        ]

    except Exception as exc:
        raise PrinterStatusError(
            f"Unable to inspect print jobs: {printer_name}"
        ) from exc

    finally:
        if handle is not None:
            win32print.ClosePrinter(handle)
