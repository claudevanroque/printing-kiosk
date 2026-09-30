from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import APP_NAME, DEBUG
from app.core.database import get_db

from app.api.auth import router as auth_router
from app.api.kiosks import router as kiosks_router
from app.api.tenants import router as tenants_router
from app.api.users import router as users_router
from app.api.services import router as services_router

app = FastAPI(title=APP_NAME, debug=DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth_router,
    prefix="/api",
)

app.include_router(
    users_router,
    prefix="/api",
)

app.include_router(
    tenants_router,
    prefix="/api",
)

app.include_router(
    kiosks_router,
    prefix="/api",
)

app.include_router(
    services_router,
    prefix="/api",
)

@app.get("/api")
def read_root():
    return {"message": f"Welcome to the {APP_NAME} API"}

@app.get("/api/health")
def health_check(
    db: Session = Depends(get_db),
):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }