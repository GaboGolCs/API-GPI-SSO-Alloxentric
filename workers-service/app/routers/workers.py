"""Router — /v1/workers endpoints.

Endpoints
─────────
GET  /v1/workers/me/stats
GET  /v1/workers/me/notifications
PATCH /v1/workers/me/notifications/{id}/read
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import CurrentUser, get_current_user, get_db, verify_role
from app.repositories.workers_repository import WorkersRepository
from app.schemas.workers import (
    MarkNotificationReadResponse,
    NotificationListResponse,
    WorkerStatsResponse,
)
from app.services.workers_service import WorkersService
from google.cloud import firestore

router = APIRouter(prefix="/v1/workers", tags=["App Móvil — Perfil Worker"])


# ─── Dependency helpers ───────────────────────────────────────────────────


def get_workers_service(
    db: Annotated[firestore.AsyncClient, Depends(get_db)],
) -> WorkersService:
    repo = WorkersRepository(db)
    return WorkersService(repo)


# ─── Endpoints ────────────────────────────────────────────────────────────


@router.get(
    "/me/stats",
    response_model=WorkerStatsResponse,
    summary="Get current worker performance stats",
    description=(
        "Returns aggregated statistics for the authenticated worker: total reports submitted, "
        "breakdown by status and shift, per-area metrics, and average resolution time. "
        "Accepts an optional `period_days` query param (default: 30)."
    ),
)
async def get_my_stats(
    current_user: Annotated[CurrentUser, Depends(verify_role("worker", "supervisor", "admin"))],
    service: Annotated[WorkersService, Depends(get_workers_service)],
    period_days: int = Query(default=30, ge=1, le=365, description="Stats window in days"),
) -> WorkerStatsResponse:
    return await service.get_my_stats(
        client_id=current_user.client_id,
        worker_id=current_user.id,
        period_days=period_days,
    )


@router.get(
    "/me/notifications",
    response_model=NotificationListResponse,
    summary="List notifications for the current worker",
    description=(
        "Returns the most recent notifications for the authenticated worker. "
        "Optionally filter by status (`unread` | `read`). Ordered newest-first."
    ),
)
async def list_my_notifications(
    current_user: Annotated[CurrentUser, Depends(verify_role("worker", "supervisor", "admin"))],
    service: Annotated[WorkersService, Depends(get_workers_service)],
    limit: int = Query(default=50, ge=1, le=200, description="Max notifications to return"),
    status: str | None = Query(
        default=None, pattern="^(unread|read)$", description="Filter by status"
    ),
) -> NotificationListResponse:
    return await service.list_my_notifications(
        client_id=current_user.client_id,
        worker_id=current_user.id,
        limit=limit,
        status_filter=status,
    )


@router.patch(
    "/me/notifications/{notification_id}/read",
    response_model=MarkNotificationReadResponse,
    summary="Mark a notification as read",
    description=(
        "Marks the specified notification as read for the authenticated worker. "
        "Idempotent — calling it multiple times on an already-read notification is safe."
    ),
)
async def mark_notification_read(
    notification_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_role("worker", "supervisor", "admin"))],
    service: Annotated[WorkersService, Depends(get_workers_service)],
) -> MarkNotificationReadResponse:
    return await service.mark_notification_as_read(
        client_id=current_user.client_id,
        worker_id=current_user.id,
        notification_id=notification_id,
        requesting_user_id=current_user.id,
    )
