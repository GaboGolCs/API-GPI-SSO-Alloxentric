"""Repository — acceso a Firestore para el workers-service.

Estructura de colecciones utilizada:
─────────────────────────────────────────────────────────────────────────────
clients/{client_id}                          ← documento raíz del cliente
    └── users/{user_id}                      ← el worker ES un usuario
            ├── assigned_areas: []           ← áreas asignadas al worker
            ├── role: "worker"
            └── notifications/{notif_id}    ← subcolección creada por este servicio
                    ├── notification_id
                    ├── type               : "alert"|"assignment"|"comment"|"status_change"|"reminder"
                    ├── title
                    ├── body
                    ├── status             : "unread" | "read"
                    ├── related_report_id  : opcional
                    ├── related_alert_id   : opcional
                    ├── created_at         : Firestore Timestamp
                    └── read_at            : Firestore Timestamp | null

clients/{client_id}/reports/{report_id}      ← reportes (solo lectura para stats)
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime, timezone

from google.cloud import firestore

from app.exceptions import NotFoundError


class WorkersRepository:

    def __init__(self, db: firestore.AsyncClient) -> None:
        self._db = db

    # ─── Helpers de rutas ─────────────────────────────────────────────────

    def _user_ref(self, client_id: str, user_id: str) -> firestore.AsyncDocumentReference:
        """Referencia al documento del usuario dentro de la subcolección users."""
        return (
            self._db
            .collection("clients")
            .document(client_id)
            .collection("users")
            .document(user_id)
        )

    def _notifications_col(
        self, client_id: str, user_id: str
    ) -> firestore.AsyncCollectionReference:
        """Subcolección notifications dentro del usuario."""
        return self._user_ref(client_id, user_id).collection("notifications")

    def _notification_ref(
        self, client_id: str, user_id: str, notification_id: str
    ) -> firestore.AsyncDocumentReference:
        return self._notifications_col(client_id, user_id).document(notification_id)

    def _reports_col(self, client_id: str) -> firestore.AsyncCollectionReference:
        """Subcolección reports del cliente (solo lectura para stats)."""
        return (
            self._db
            .collection("clients")
            .document(client_id)
            .collection("reports")
        )

    # ─── Stats — usuarios ─────────────────────────────────────────────────

    async def get_user_document(self, client_id: str, user_id: str) -> dict:
        """
        Retorna el documento del usuario desde:
            clients/{client_id}/users/{user_id}

        Lanza NotFoundError si no existe.
        """
        snap = await self._user_ref(client_id, user_id).get()
        if not snap.exists:
            raise NotFoundError("User", user_id)
        return snap.to_dict() or {}

    # ─── Stats — reportes ─────────────────────────────────────────────────

    async def get_reports_for_worker(
        self,
        client_id: str,
        user_id: str,
        since: datetime,
    ) -> list[dict]:
        """
        Retorna todos los reportes creados por este usuario en el período.

        Query sobre:
            clients/{client_id}/reports
        Filtros:
            reported_by == user_id
            created_at  >= since
        """
        query = (
            self._reports_col(client_id)
            .where("reported_by", "==", user_id)
            .where("created_at", ">=", since)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
        )

        results: list[dict] = []
        async for doc in query.stream():
            data = doc.to_dict() or {}
            data["report_id"] = doc.id
            results.append(data)
        return results

    # ─── Notificaciones ───────────────────────────────────────────────────

    async def create_notification(
        self,
        client_id: str,
        user_id: str,
        notification_id: str,
        data: dict,
    ) -> dict:
        """
        Crea un documento en:
            clients/{client_id}/users/{user_id}/notifications/{notification_id}

        El campo `created_at` se setea automáticamente como Firestore Timestamp.
        """
        now = datetime.now(tz=timezone.utc)
        payload = {
            **data,
            "notification_id": notification_id,
            "status": "unread",
            "created_at": now,
            "read_at": None,
        }
        await self._notification_ref(client_id, user_id, notification_id).set(payload)
        return payload

    async def list_notifications(
        self,
        client_id: str,
        user_id: str,
        *,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[dict]:
        """
        Lista las notificaciones del usuario ordenadas de más nueva a más antigua.

        Ruta: clients/{client_id}/users/{user_id}/notifications
        """
        col = self._notifications_col(client_id, user_id)

        if status_filter:
            query = (
                col
                .where("status", "==", status_filter)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
        else:
            query = col.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)

        results: list[dict] = []
        async for doc in query.stream():
            data = doc.to_dict() or {}
            data["notification_id"] = doc.id
            results.append(data)
        return results

    async def count_unread_notifications(self, client_id: str, user_id: str) -> int:
        """
        Cuenta las notificaciones con status='unread' usando agregación de Firestore.
        No descarga los documentos completos — solo el conteo.
        """
        col = self._notifications_col(client_id, user_id)
        query = col.where("status", "==", "unread")
        agg = await query.count().get()
        return int(agg[0][0].value) if agg else 0

    async def get_notification(
        self, client_id: str, user_id: str, notification_id: str
    ) -> dict:
        """
        Retorna un documento de notificación específico.
        Lanza NotFoundError si no existe.
        """
        snap = await self._notification_ref(client_id, user_id, notification_id).get()
        if not snap.exists:
            raise NotFoundError("Notification", notification_id)
        data = snap.to_dict() or {}
        data["notification_id"] = snap.id
        return data

    async def mark_notification_read(
        self, client_id: str, user_id: str, notification_id: str
    ) -> dict:
        """
        Marca una notificación como leída. Es idempotente — si ya estaba
        en 'read', solo actualiza el read_at sin lanzar error.

        Actualiza en Firestore:
            status  → "read"
            read_at → timestamp actual
        """
        ref = self._notification_ref(client_id, user_id, notification_id)

        snap = await ref.get()
        if not snap.exists:
            raise NotFoundError("Notification", notification_id)

        now = datetime.now(tz=timezone.utc)
        await ref.update({"status": "read", "read_at": now})

        data = snap.to_dict() or {}
        data.update({
            "notification_id": notification_id,
            "status": "read",
            "read_at": now,
        })
        return data
