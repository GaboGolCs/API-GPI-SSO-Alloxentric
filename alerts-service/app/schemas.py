from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AlertResponse(BaseModel):
    id:              str
    type:            str   # iap | sla | zone | manual | auto
    title:           str
    body:            str
    zone_id:         Optional[str] = None
    zone_name:       Optional[str] = None
    incident_id:     Optional[str] = None
    severity:        str = "medium"   # low | medium | high | critical
    status:          str = "active"   # active | resolved
    resolution_note: Optional[str] = None
    created_at:      str
    resolved_at:     Optional[str] = None


class AlertsListResponse(BaseModel):
    data:        List[AlertResponse]
    total:       int
    page:        int
    page_size:   int


class AlertStatsResponse(BaseModel):
    active_alerts:   int
    pending_review:  int
    resolved_today:  int
    auto_sent_today: int


class ResolveAlertRequest(BaseModel):
    resolution_note: Optional[str] = None


class ManualAlertRequest(BaseModel):
    title:         str
    body:          str
    zone_id:       Optional[str] = None
    recipient_ids: Optional[List[str]] = None
    severity:      str = "medium"


class ManualAlertResponse(BaseModel):
    id:                str
    type:              str = "manual"
    title:             str
    status:            str = "active"
    recipients_count:  int
    created_at:        str
