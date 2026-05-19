from fastapi import APIRouter, Depends
from app.dependencies import get_db, get_current_user, verify_role, CurrentUser
from app.services.dashboard_service import DashboardService
from app.repositories.dashboard_repo import DashboardRepository
from app.schemas.dashboard import (
    HeatmapResponse, KpisResponse, TrendsResponse, TopAreasResponse,
)

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard & Heat Map"])


def get_service(db=Depends(get_db)) -> DashboardService:
    return DashboardService(DashboardRepository(db))


# GET /v1/dashboard/heatmap?period=7d
@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    period:       str = "7d",
    service:      DashboardService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Devuelve el mapa de calor con el score de riesgo por zona.
    Usado por W-01 Command Center para renderizar el mapa interactivo.
    """
    return await service.get_heatmap(
        client_id = current_user.client_id,
        period    = period,
    )


# GET /v1/dashboard/kpis?period=30d
@router.get("/kpis", response_model=KpisResponse)
async def get_kpis(
    period:       str = "30d",
    service:      DashboardService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Devuelve los KPIs globales del dashboard:
    total reportes, IAP activos, tasa SLA, score global.
    """
    return await service.get_kpis(
        client_id = current_user.client_id,
        period    = period,
    )


# GET /v1/dashboard/trends?days=7
@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    days:         int = 7,
    service:      DashboardService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Devuelve la evolución del score de riesgo global día a día.
    Usado por el gráfico de tendencias del Command Center.
    """
    return await service.get_trends(
        client_id = current_user.client_id,
        days      = days,
    )


# GET /v1/dashboard/top-areas?limit=5
@router.get("/top-areas", response_model=TopAreasResponse)
async def get_top_areas(
    limit:        int = 5,
    service:      DashboardService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Devuelve el ranking de áreas con mayor score de riesgo.
    Usado por el panel de Áreas Críticas del Command Center.
    """
    return await service.get_top_areas(
        client_id = current_user.client_id,
        limit     = limit,
    )
