"""Router — /v1/plant y /v1/zones endpoints.

Endpoints
─────────
POST  /v1/plant/floor-plan          → Sube imagen del plano de planta
GET   /v1/plant/floor-plan          → Obtiene URL del plano actual

GET   /v1/zones                     → Lista todas las zonas del cliente
POST  /v1/zones                     → Crea una zona nueva
PATCH /v1/zones/{zone_id}           → Actualiza una zona existente
DELETE /v1/zones/{zone_id}          → Elimina una zona
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import CurrentUser, get_current_user, get_db, get_storage_client, verify_role
from app.repositories.digital_twin_repository import DigitalTwinRepository
from app.schemas.digital_twin import (
    DeleteResponse,
    FloorPlanResponse,
    FloorPlanUploadResponse,
    ZoneCreateRequest,
    ZoneListResponse,
    ZoneResponse,
    ZoneUpdateRequest,
)
from app.services.digital_twin_service import DigitalTwinService

router = APIRouter(tags=["Digital Twin /V1/PLANT & /V1/ZONES"])


# ─── Dependency ───────────────────────────────────────────────────────────────

def get_service(
    db=Depends(get_db),
    storage_client=Depends(get_storage_client),
) -> DigitalTwinService:
    repo = DigitalTwinRepository(db)
    return DigitalTwinService(repo, storage_client)


# ─── Floor Plan ───────────────────────────────────────────────────────────────

@router.post(
    "/v1/plant/floor-plan",
    response_model=FloorPlanUploadResponse,
    summary="Subir plano de planta",
    description=(
        "Sube una imagen (PNG, JPG, SVG) como plano base de la planta. "
        "La imagen se almacena en Cloud Storage y la URL se guarda en el "
        "documento raíz del cliente en Firestore. Solo admin y supervisor."
    ),
)
async def upload_floor_plan(
    file:         UploadFile = File(..., description="Imagen del plano (PNG, JPG, SVG)"),
    current_user: CurrentUser = Depends(verify_role("admin", "supervisor")),
    service:      DigitalTwinService = Depends(get_service),
) -> FloorPlanUploadResponse:
    file_bytes   = await file.read()
    content_type = file.content_type or "image/png"
    filename     = file.filename or "floor_plan.png"

    return await service.upload_floor_plan(
        client_id    = current_user.client_id,
        file_bytes   = file_bytes,
        content_type = content_type,
        filename     = filename,
    )


@router.get(
    "/v1/plant/floor-plan",
    response_model=FloorPlanResponse,
    summary="Obtener plano de planta",
    description="Retorna la URL del plano de planta actual del cliente.",
)
async def get_floor_plan(
    current_user: CurrentUser = Depends(get_current_user),
    service:      DigitalTwinService = Depends(get_service),
) -> FloorPlanResponse:
    return await service.get_floor_plan(client_id=current_user.client_id)


# ─── Zones ────────────────────────────────────────────────────────────────────

@router.get(
    "/v1/zones",
    response_model=ZoneListResponse,
    summary="Listar zonas",
    description=(
        "Retorna todas las zonas del gemelo digital de la planta para el cliente autenticado. "
        "Cada zona incluye su polígono de coordenadas, color y proceso asociado."
    ),
)
async def list_zones(
    current_user: CurrentUser = Depends(get_current_user),
    service:      DigitalTwinService = Depends(get_service),
) -> ZoneListResponse:
    return await service.list_zones(client_id=current_user.client_id)


@router.post(
    "/v1/zones",
    response_model=ZoneResponse,
    status_code=201,
    summary="Crear zona",
    description=(
        "Crea una nueva zona en el gemelo digital. "
        "El polígono debe tener al menos 3 puntos {x, y}. "
        "El color debe ser un hex válido (#RRGGBB). Solo admin y supervisor."
    ),
)
async def create_zone(
    payload:      ZoneCreateRequest,
    current_user: CurrentUser = Depends(verify_role("admin", "supervisor")),
    service:      DigitalTwinService = Depends(get_service),
) -> ZoneResponse:
    return await service.create_zone(
        client_id = current_user.client_id,
        payload   = payload,
    )


@router.patch(
    "/v1/zones/{zone_id}",
    response_model=ZoneResponse,
    summary="Actualizar zona",
    description=(
        "Actualiza parcialmente una zona existente (PATCH). "
        "Solo se actualizan los campos incluidos en el body. "
        "Solo admin y supervisor."
    ),
)
async def update_zone(
    zone_id:      str,
    payload:      ZoneUpdateRequest,
    current_user: CurrentUser = Depends(verify_role("admin", "supervisor")),
    service:      DigitalTwinService = Depends(get_service),
) -> ZoneResponse:
    return await service.update_zone(
        client_id = current_user.client_id,
        zone_id   = zone_id,
        payload   = payload,
    )


@router.delete(
    "/v1/zones/{zone_id}",
    response_model=DeleteResponse,
    summary="Eliminar zona",
    description="Elimina permanentemente una zona del gemelo digital. Solo admin.",
)
async def delete_zone(
    zone_id:      str,
    current_user: CurrentUser = Depends(verify_role("admin")),
    service:      DigitalTwinService = Depends(get_service),
) -> DeleteResponse:
    return await service.delete_zone(
        client_id       = current_user.client_id,
        zone_id         = zone_id,
        requesting_role = current_user.role,
    )
