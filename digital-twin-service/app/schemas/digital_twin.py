from pydantic import BaseModel, Field
from typing import List, Optional


# ─── FLOOR PLAN ───────────────────────────────────────────────────────────────

class FloorPlanUploadResponse(BaseModel):
    client_id:     str
    floor_plan_url: str
    uploaded_at:   str


class FloorPlanResponse(BaseModel):
    client_id:      str
    floor_plan_url: str | None = None
    has_floor_plan: bool


# ─── ZONES ────────────────────────────────────────────────────────────────────

class PolygonPoint(BaseModel):
    x: float
    y: float


class ZoneCreateRequest(BaseModel):
    name:          str               = Field(..., min_length=1, max_length=100)
    process:       str               = Field(..., min_length=1, max_length=100)
    color:         str               = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    polygon:       List[PolygonPoint] = Field(..., min_length=3)
    floor_plan_url: Optional[str]    = None


class ZoneUpdateRequest(BaseModel):
    name:           Optional[str]               = Field(None, min_length=1, max_length=100)
    process:        Optional[str]               = Field(None, min_length=1, max_length=100)
    color:          Optional[str]               = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    polygon:        Optional[List[PolygonPoint]] = Field(None, min_length=3)
    floor_plan_url: Optional[str]               = None


class ZoneResponse(BaseModel):
    zone_id:        str
    client_id:      str
    name:           str
    process:        str
    color:          str
    polygon:        List[PolygonPoint]
    floor_plan_url: Optional[str] = None
    created_at:     Optional[str] = None
    updated_at:     Optional[str] = None


class ZoneListResponse(BaseModel):
    data:  List[ZoneResponse]
    total: int


class DeleteResponse(BaseModel):
    zone_id: str
    deleted: bool
    message: str
