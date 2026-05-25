from google.cloud import firestore
from datetime import datetime, timezone
import ulid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(data: dict) -> dict:
    for k, v in data.items():
        if hasattr(v, 'isoformat'):
            data[k] = v.isoformat()
        elif hasattr(v, 'ToDatetime'):
            data[k] = v.ToDatetime(tzinfo=timezone.utc).isoformat()
        elif hasattr(v, 'seconds'):
            data[k] = datetime.fromtimestamp(v.seconds, tz=timezone.utc).isoformat()
    return data


class AlertRepository:
    def __init__(self, db: firestore.AsyncClient):
        self.db = db

    def _alerts_ref(self, client_id: str):
        return self.db.collection("clients").document(client_id).collection("alerts")

    def _notifs_ref(self, client_id: str, user_id: str):
        return (
            self.db.collection("clients")
            .document(client_id)
            .collection("users")
            .document(user_id)
            .collection("notifications")
        )

    async def list_alerts(
        self,
        client_id: str,
        status: str = "active",
        alert_type: str | None = None,
        zone_id: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list, int]:
        ref = self._alerts_ref(client_id)
        query = ref.where("status", "==", status)
        if alert_type:
            query = query.where("type", "==", alert_type)
        if zone_id:
            query = query.where("zone_id", "==", zone_id)

        results = []
        async for doc in query.stream():
            data = doc.to_dict()
            if data:
                data = _normalize(data)
                results.append(data)

        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        return results[start:start + page_size], total

    async def get_stats(self, client_id: str) -> dict:
        ref = self._alerts_ref(client_id)
        today = datetime.now(timezone.utc).date().isoformat()

        active = 0
        resolved_today = 0
        auto_today = 0

        async for doc in ref.stream():
            data = doc.to_dict() or {}
            if data.get("status") == "active":
                active += 1
            resolved_at = data.get("resolved_at", "")
            if resolved_at and resolved_at[:10] == today:
                resolved_today += 1
            created_at = data.get("created_at", "")
            if (
                data.get("type") in ("iap", "sla", "auto")
                and created_at[:10] == today
            ):
                auto_today += 1

        return {
            "active_alerts":   active,
            "pending_review":  active,
            "resolved_today":  resolved_today,
            "auto_sent_today": auto_today,
        }

    async def resolve_alert(
        self, client_id: str, alert_id: str, resolution_note: str = ""
    ) -> dict | None:
        doc_ref = self._alerts_ref(client_id).document(alert_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return None
        now = _now()
        await doc_ref.update({
            "status":          "resolved",
            "resolved_at":     now,
            "resolution_note": resolution_note,
        })
        data = doc.to_dict() or {}
        data.update({"status": "resolved", "resolved_at": now, "resolution_note": resolution_note})
        return _normalize(data)

    async def create_manual_alert(
        self,
        client_id: str,
        title: str,
        body: str,
        severity: str,
        zone_id: str | None,
        recipient_ids: list[str] | None,
    ) -> dict:
        alert_id = f"alt_{ulid.ULID()}"
        now = _now()
        alert_data = {
            "id":          alert_id,
            "type":        "manual",
            "title":       title,
            "body":        body,
            "severity":    severity,
            "zone_id":     zone_id,
            "zone_name":   zone_id,
            "status":      "active",
            "client_id":   client_id,
            "created_at":  now,
        }
        await self._alerts_ref(client_id).document(alert_id).set(alert_data)

        # Enviar notificación a cada recipient
        recipients = recipient_ids or []
        for user_id in recipients:
            notif_id = f"notif_{ulid.ULID()}"
            await self._notifs_ref(client_id, user_id).document(notif_id).set({
                "id":         notif_id,
                "user_id":    user_id,
                "type":       "alert",
                "title":      title,
                "body":       body,
                "read":       False,
                "alert_id":   alert_id,
                "created_at": now,
            })

        return {**alert_data, "recipients_count": len(recipients)}

    async def create_iap_alert(
        self, client_id: str, report_id: str, area_id: str, user_id: str
    ) -> str:
        """Llamado automáticamente cuando se crea un reporte IAP."""
        alert_id = f"alt_{ulid.ULID()}"
        now = _now()
        await self._alerts_ref(client_id).document(alert_id).set({
            "id":          alert_id,
            "type":        "iap",
            "title":       f"Nuevo IAP — {area_id}",
            "body":        f"Se reportó un Incidente de Alto Potencial en {area_id}.",
            "zone_id":     area_id,
            "zone_name":   area_id,
            "incident_id": report_id,
            "severity":    "high",
            "status":      "active",
            "client_id":   client_id,
            "created_at":  now,
        })
        return alert_id
