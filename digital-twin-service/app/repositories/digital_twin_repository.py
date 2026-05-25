"""Repository — acceso a Firestore para el digital-twin-service.

Estructura de colecciones:
─────────────────────────────────────────────────────────────────
clients/{client_id}
    ├── floor_plan_url: str          ← campo en el documento raíz
    └── zones/{zone_id}              ← subcolección de zonas
            ├── zone_id
            ├── client_id
            ├── name
            ├── process
            ├── color
            ├── polygon: [{x, y}, ...]
            ├── floor_plan_url
            ├── created_at
            └── updated_at
─────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime, timezone

from google.cloud import firestore

from app.exceptions import NotFoundError


class DigitalTwinRepository:

    def __init__(self, db: firestore.AsyncClient) -> None:
        self._db = db

    # ─── Helpers de rutas ─────────────────────────────────────────────────

    def _client_ref(self, client_id: str) -> firestore.AsyncDocumentReference:
        return self._db.collection("clients").document(client_id)

    def _zones_col(self, client_id: str) -> firestore.AsyncCollectionReference:
        return self._client_ref(client_id).collection("zones")

    def _zone_ref(self, client_id: str, zone_id: str) -> firestore.AsyncDocumentReference:
        return self._zones_col(client_id).document(zone_id)

    # ─── Floor Plan ───────────────────────────────────────────────────────

    async def get_floor_plan_url(self, client_id: str) -> str | None:
        """Lee el campo floor_plan_url del documento raíz del cliente."""
        snap = await self._client_ref(client_id).get()
        if not snap.exists:
            return None
        return (snap.to_dict() or {}).get("floor_plan_url")

    async def save_floor_plan_url(self, client_id: str, url: str) -> None:
        """Guarda o actualiza el floor_plan_url en el documento raíz del cliente."""
        await self._client_ref(client_id).set(
            {"floor_plan_url": url},
            merge=True,  # no sobreescribe otros campos del cliente
        )

    # ─── Zones ────────────────────────────────────────────────────────────

    async def list_zones(self, client_id: str) -> list[dict]:
        """Lista todas las zonas de un cliente."""
        results: list[dict] = []
        async for doc in self._zones_col(client_id).stream():
            data = doc.to_dict() or {}
            data["zone_id"] = doc.id
            results.append(data)
        return results

    async def get_zone(self, client_id: str, zone_id: str) -> dict:
        """Retorna una zona. Lanza NotFoundError si no existe."""
        snap = await self._zone_ref(client_id, zone_id).get()
        if not snap.exists:
            raise NotFoundError("Zone", zone_id)
        data = snap.to_dict() or {}
        data["zone_id"] = snap.id
        return data

    async def create_zone(self, client_id: str, zone_id: str, data: dict) -> dict:
        """
        Crea un documento en:
            clients/{client_id}/zones/{zone_id}
        """
        now = datetime.now(tz=timezone.utc).isoformat()
        payload = {
            **data,
            "zone_id":   zone_id,
            "client_id": client_id,
            "created_at": now,
            "updated_at": now,
        }
        await self._zone_ref(client_id, zone_id).set(payload)
        return payload

    async def update_zone(self, client_id: str, zone_id: str, data: dict) -> dict:
        """
        Actualiza campos de una zona existente (PATCH — solo campos enviados).
        Lanza NotFoundError si no existe.
        """
        snap = await self._zone_ref(client_id, zone_id).get()
        if not snap.exists:
            raise NotFoundError("Zone", zone_id)

        now = datetime.now(tz=timezone.utc).isoformat()
        update_data = {**data, "updated_at": now}
        await self._zone_ref(client_id, zone_id).update(update_data)

        updated = (snap.to_dict() or {})
        updated.update(update_data)
        updated["zone_id"] = zone_id
        return updated

    async def delete_zone(self, client_id: str, zone_id: str) -> None:
        """
        Elimina una zona. Lanza NotFoundError si no existe.
        """
        snap = await self._zone_ref(client_id, zone_id).get()
        if not snap.exists:
            raise NotFoundError("Zone", zone_id)
        await self._zone_ref(client_id, zone_id).delete()
