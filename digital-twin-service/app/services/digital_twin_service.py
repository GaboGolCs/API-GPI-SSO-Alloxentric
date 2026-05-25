"""Service — lógica de negocio para el digital-twin-service."""

from __future__ import annotations

from datetime import datetime, timezone

from google.cloud import storage
from ulid import ULID

from app.config import settings
from app.exceptions import ForbiddenError
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


def _to_zone_response(data: dict) -> ZoneResponse:
    """Convierte un dict de Firestore a ZoneResponse."""
    polygon_raw = data.get("polygon", [])
    polygon = [
        {"x": p["x"], "y": p["y"]}
        if isinstance(p, dict)
        else {"x": p.x, "y": p.y}
        for p in polygon_raw
    ]
    return ZoneResponse(
        zone_id        = data["zone_id"],
        client_id      = data.get("client_id", ""),
        name           = data.get("name", ""),
        process        = data.get("process", ""),
        color          = data.get("color", "#000000"),
        polygon        = polygon,
        floor_plan_url = data.get("floor_plan_url"),
        created_at     = data.get("created_at"),
        updated_at     = data.get("updated_at"),
    )


class DigitalTwinService:

    def __init__(
        self,
        repo: DigitalTwinRepository,
        storage_client: storage.Client,
    ) -> None:
        self._repo    = repo
        self._storage = storage_client

    # ─── Floor Plan ───────────────────────────────────────────────────────

    async def upload_floor_plan(
        self,
        client_id: str,
        file_bytes: bytes,
        content_type: str,
        filename: str,
    ) -> FloorPlanUploadResponse:
        """
        Sube la imagen del plano a Cloud Storage y guarda la URL pública
        en el documento raíz del cliente en Firestore.
        """
        ext        = filename.rsplit(".", 1)[-1] if "." in filename else "png"
        blob_name  = f"floor-plans/{client_id}/floor_plan.{ext}"
        bucket     = self._storage.bucket(settings.GCS_BUCKET_NAME)
        blob       = bucket.blob(blob_name)

        blob.upload_from_string(file_bytes, content_type=content_type)
        blob.make_public()

        public_url = blob.public_url
        await self._repo.save_floor_plan_url(client_id, public_url)

        return FloorPlanUploadResponse(
            client_id      = client_id,
            floor_plan_url = public_url,
            uploaded_at    = datetime.now(tz=timezone.utc).isoformat(),
        )

    async def get_floor_plan(self, client_id: str) -> FloorPlanResponse:
        url = await self._repo.get_floor_plan_url(client_id)
        return FloorPlanResponse(
            client_id      = client_id,
            floor_plan_url = url,
            has_floor_plan = url is not None,
        )

    # ─── Zones ────────────────────────────────────────────────────────────

    async def list_zones(self, client_id: str) -> ZoneListResponse:
        zones = await self._repo.list_zones(client_id)
        items = [_to_zone_response(z) for z in zones]
        return ZoneListResponse(data=items, total=len(items))

    async def create_zone(
        self, client_id: str, payload: ZoneCreateRequest
    ) -> ZoneResponse:
        zone_id = f"zone_{ULID()}"
        data = {
            "name":           payload.name,
            "process":        payload.process,
            "color":          payload.color,
            "polygon":        [p.model_dump() for p in payload.polygon],
            "floor_plan_url": payload.floor_plan_url,
        }
        created = await self._repo.create_zone(client_id, zone_id, data)
        return _to_zone_response(created)

    async def update_zone(
        self,
        client_id: str,
        zone_id: str,
        payload: ZoneUpdateRequest,
    ) -> ZoneResponse:
        # Solo incluir campos que el cliente envió (PATCH parcial)
        data: dict = {}
        if payload.name is not None:
            data["name"] = payload.name
        if payload.process is not None:
            data["process"] = payload.process
        if payload.color is not None:
            data["color"] = payload.color
        if payload.polygon is not None:
            data["polygon"] = [p.model_dump() for p in payload.polygon]
        if payload.floor_plan_url is not None:
            data["floor_plan_url"] = payload.floor_plan_url

        updated = await self._repo.update_zone(client_id, zone_id, data)
        return _to_zone_response(updated)

    async def delete_zone(
        self,
        client_id: str,
        zone_id: str,
        requesting_role: str,
    ) -> DeleteResponse:
        # Solo admin y supervisor pueden eliminar zonas
        if requesting_role not in ("admin", "supervisor"):
            raise ForbiddenError("Solo administradores pueden eliminar zonas.")

        await self._repo.delete_zone(client_id, zone_id)
        return DeleteResponse(
            zone_id = zone_id,
            deleted = True,
            message = f"Zona '{zone_id}' eliminada exitosamente.",
        )
