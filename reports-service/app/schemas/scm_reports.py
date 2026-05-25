from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ─── REPORTS ──────────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    area_id: str = Field(..., example="area_01")
    type: str = Field(..., example="Acto Inseguro")
    is_iap: bool = Field(default=False)
    description: str
    shift: str = Field(..., example="Turno A")
    evidences: Optional[List[str]] = []


class ReportResponse(ReportCreate):
    report_id: str
    status: str = "open"
    reported_by: str
    created_at: datetime


# ─── WORKER STATS ─────────────────────────────────────────────────────────────

class WorkerStats(BaseModel):
    period: str
    total_reports: int
    reports_this_period: int
    closed_reports: int
    effectiveness_rate: float
    iap_reports: int


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: str
    type: str           # report_status_change | area_alert | comment
    title: str
    body: str
    report_id: Optional[str] = None
    read: bool
    created_at: str


class NotificationListResponse(BaseModel):
    data: List[NotificationResponse]
    unread_count: int
