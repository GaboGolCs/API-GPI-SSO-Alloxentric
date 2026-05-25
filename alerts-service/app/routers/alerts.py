from fastapi import APIRouter, Depends, HTTPException, Query
from google.cloud.firestore import AsyncClient
from app.dependencies import get_db, get_current_user
from app.repositories.alert_repo import AlertRepository
from app.schemas import (
    AlertsListResponse, AlertStatsResponse,
    ResolveAlertRequest, ManualAlertRequest, ManualAlertResponse,
)

router = APIRouter(prefix="/v1/alerts", tags=["Alerts"])


def get_repo(db: AsyncClient = Depends(get_db)) -> AlertRepository:
    return AlertRepository(db)


# GET /v1/alerts
@router.get("/", response_model=AlertsListResponse)
async def list_alerts(
    status:    str         = Query("active"),
    type:      str | None  = Query(None),
    zone_id:   str | None  = Query(None),
    page:      int         = Query(1),
    page_size: int         = Query(25),
    repo:      AlertRepository = Depends(get_repo),
    user:      dict        = Depends(get_current_user),
):
    data, total = await repo.list_alerts(
        client_id=user["client_id"],
        status=status,
        alert_type=type,
        zone_id=zone_id,
        page=page,
        page_size=page_size,
    )
    return AlertsListResponse(data=data, total=total, page=page, page_size=page_size)


# GET /v1/alerts/stats
@router.get("/stats", response_model=AlertStatsResponse)
async def get_stats(
    repo: AlertRepository = Depends(get_repo),
    user: dict            = Depends(get_current_user),
):
    return await repo.get_stats(client_id=user["client_id"])


# PATCH /v1/alerts/{alert_id}/resolve
@router.patch("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    body:     ResolveAlertRequest,
    repo:     AlertRepository = Depends(get_repo),
    user:     dict            = Depends(get_current_user),
):
    result = await repo.resolve_alert(
        client_id=user["client_id"],
        alert_id=alert_id,
        resolution_note=body.resolution_note or "",
    )
    if not result:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return result


# POST /v1/alerts/manual
@router.post("/manual", status_code=201, response_model=ManualAlertResponse)
async def create_manual_alert(
    body: ManualAlertRequest,
    repo: AlertRepository = Depends(get_repo),
    user: dict            = Depends(get_current_user),
):
    if not body.zone_id and not body.recipient_ids:
        raise HTTPException(status_code=400, detail="Se requiere zone_id o recipient_ids")

    result = await repo.create_manual_alert(
        client_id=user["client_id"],
        title=body.title,
        body=body.body,
        severity=body.severity,
        zone_id=body.zone_id,
        recipient_ids=body.recipient_ids,
    )
    return result
