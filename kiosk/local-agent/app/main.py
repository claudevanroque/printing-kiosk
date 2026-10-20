import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)
import asyncio
import threading

from app.api import (
    documents,
    health,
    hotspot,
    upload_sessions,
    pricing,
    service_jobs,
    printers,
    print_queue,
)

from app.core.config import settings
from app.core.logging import setup_logging
from app.services.pricing_sync_service import pricing_sync_service
from app.services.print_worker_service import run_print_worker
from app.core.database import engine

setup_logging()

logger = logging.getLogger(__name__)

async def sync_pricing_on_startup():
    try:
        pricing = await pricing_sync_service.sync()

        logger.info(
            "Cloud pricing synchronized successfully. "
            "Tenant: %s | Version: %s",
            pricing.tenant_id,
            pricing.version,
        )

    except Exception:
        logger.exception(
            "Cloud pricing synchronization failed. "
            "Existing local pricing will be preserved."
        )


@asynccontextmanager
async def lifespan(app: FastAPI,):
    settings.temp_path.mkdir(parents=True, exist_ok=True)
    await sync_pricing_on_startup()
    
    stop_event = threading.Event()
    worker_task = asyncio.create_task(
        run_print_worker(
            engine=engine,
            stop_event=stop_event,
        )
    )
    try:
        yield
    finally:
        try:
            stop_event.set()
            await asyncio.wait_for(worker_task, timeout=130)
        except Exception:
            logger.exception("Print worker shutdown timed out.")
    


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health.router,
    prefix="/api",
)

app.include_router(
    hotspot.router,
    prefix="/api",
)

app.include_router(
    documents.router,
    prefix="/api",
)

app.include_router(
    upload_sessions.router,
    prefix="/api",
)

app.include_router(
    pricing.router,
    prefix="/api",
)

app.include_router(
    service_jobs.router,
    prefix="/api",
)

app.include_router(
    printers.router,
    prefix="/api",
)

app.include_router(
    print_queue.router,
    prefix="/api",
)



@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "running",
    }