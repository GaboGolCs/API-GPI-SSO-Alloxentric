"""Pydantic schemas for the workers endpoints."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ─── Enums ─────────────────────────────────────────────────────────────────


class NotificationStatus(str, Enum):
    unread = "unread"
    read = "read"


class NotificationType(str, Enum):
    alert = "alert"
    assignment = "assignment"
    comment = "comment"
    status_change = "status_change"
    reminder = "reminder"


# ─── Stats schemas ─────────────────────────────────────────────────────────


class AreaStats(BaseModel):
    area_id: str
    area_name: str
    total_reports: int
    resolved_reports: int
    pending_reports: int
    avg_resolution_hours: float | None = None


class WorkerStatsResponse(BaseModel):
    worker_id: str
    period_days: int = Field(description="Number of days the stats cover")
    total_reports_submitted: int
    reports_by_status: dict[str, int]
    reports_by_shift: dict[str, int]
    assigned_areas: list[AreaStats]
    avg_resolution_hours: float | None = None
    last_activity_at: datetime | None = None


# ─── Notification schemas ──────────────────────────────────────────────────


class NotificationResponse(BaseModel):
    notification_id: str
    type: NotificationType
    title: str
    body: str
    status: NotificationStatus
    related_report_id: str | None = None
    related_alert_id: str | None = None
    created_at: datetime
    read_at: datetime | None = None


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class MarkNotificationReadResponse(BaseModel):
    notification_id: str
    status: NotificationStatus
    read_at: datetime
