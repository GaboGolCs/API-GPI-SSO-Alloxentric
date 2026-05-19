from pydantic import BaseModel
from typing import List, Optional


# ─── HEATMAP ──────────────────────────────────────────────────────────────────

class ZoneHeatmap(BaseModel):
    zone_id:        str
    name:           str
    risk_score:     int           # 0-100
    risk_level:     str           # low | medium | high | critical
    open_reports:   int
    iap_count:      int
    trend:          str           # rising | stable | falling
    last_updated:   Optional[str] = None


class HeatmapResponse(BaseModel):
    period:     str
    updated_at: str
    zones:      List[ZoneHeatmap]


# ─── KPIs ─────────────────────────────────────────────────────────────────────

class KpisResponse(BaseModel):
    period:               str
    total_reports:        int
    total_reports_delta:  float   # % cambio vs período anterior
    active_iap:           int
    active_iap_delta:     float
    sla_compliance_rate:  float   # % reportes cerrados a tiempo
    overdue_actions:      int     # reportes abiertos hace más de 48h
    closed_total:         int
    global_risk_score:    int     # 0-100


# ─── TRENDS ───────────────────────────────────────────────────────────────────

class TrendDataPoint(BaseModel):
    date:              str
    global_risk_score: int
    open_reports:      int
    new_reports:       int
    closed_reports:    int


class TrendsResponse(BaseModel):
    days: int
    data: List[TrendDataPoint]


# ─── TOP AREAS ────────────────────────────────────────────────────────────────

class TopAreaItem(BaseModel):
    rank:         int
    zone_id:      str
    name:         str
    risk_score:   int
    risk_level:   str
    trend:        str
    open_reports: int
    iap_count:    int


class TopAreasResponse(BaseModel):
    data: List[TopAreaItem]
