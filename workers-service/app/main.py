"""Workers Service — FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.middleware.logging import RequestIdMiddleware
from app.routers import workers

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Workers Service",
    description=(
        "Microservice que expone los endpoints de App Móvil — Perfil Worker: "
        "estadísticas personales y gestión de notificaciones."
    ),
    version=settings.app_version,
    docs_url="/docs" if settings.sso_environment != "production" else None,
    redoc_url="/redoc" if settings.sso_environment != "production" else None,
)

# ─── Middlewares ──────────────────────────────────────────────────────────

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ["*"] en desarrollo
    allow_credentials=False,                 # debe ser False cuando allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception handlers ───────────────────────────────────────────────────

register_exception_handlers(app)

# ─── Routers ──────────────────────────────────────────────────────────────

app.include_router(workers.router)


# ─── Health check ─────────────────────────────────────────────────────────


@app.get("/health", tags=["Health"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "workers-service",
        "version": settings.app_version,
        "environment": settings.sso_environment,
    }
