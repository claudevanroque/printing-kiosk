from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.api import (
    documents,
    health,
    hotspot,
    upload_sessions,
)

from app.core.config import settings
from app.core.database import (
    initialize_database,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    settings.temp_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    initialize_database()

    yield


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
)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "running",
    }