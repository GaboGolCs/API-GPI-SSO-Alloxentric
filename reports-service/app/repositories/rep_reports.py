from google.cloud import firestore
import ulid as ulid_lib
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_timestamps(data: dict) -> dict:
    """Convierte DatetimeWithNanoseconds de Firestore a ISO string."""
    for key, value in data.items():
        if hasattr(value, 'isoformat'):
            data[key] = value.isoformat()
        elif isinstance(value, dict):
            data[key] = _normalize_timestamps(value)
    return data


class ReportRepository:
    def __init__(self, db: firestore.AsyncClient):
        self.db = db

    def _reports_ref(self, client_id: str):
        return self.db.collection("clients").document(client_id).collection("reports")

    def _notifs_ref(self, client_id: str, user_id: str):
        """
        Ruta profesional: notificaciones por worker
        clients/{client_id}/users/{user_id}/notifications/
        """
        return (
            self.db.collection("clients")
            .document(client_id)
            .collection("users")
            .document(user_id)
            .collection("notifications")
        )

    # ─── REPORTS ──────────────────────────────────────────────────────────────

    async def save(self, client_id: str, report_id: str, data: dict):
        doc_ref = self._reports_ref(client_id).document(report_id)
        await doc_ref.set(data)

    async def get_all(self, client_id: str, user_id: str) -> list:
        query = self._reports_ref(client_id).where("reported_by", "==", user_id)
        results = []
        async for doc in query.stream():
            data = doc.to_dict()
            if data:
                data = _normalize_timestamps(data)
                results.append(data)
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    async def get_by_id(self, client_id: str, report_id: str) -> dict | None:
        doc_ref = self._reports_ref(client_id).document(report_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        return _normalize_timestamps(data) if data else None

    async def update_status(
        self,
        client_id: str,
        report_id: str,
        status: str,
        feedback: str = "",
    ) -> bool:
        doc_ref = self._reports_ref(client_id).document(report_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return False

        now = _now_iso()
        timeline_field_map = {
            "open":      "sent",
            "reviewing": "reviewing",
            "assigned":  "assigned",
            "closed":    "closed",
        }
        timeline_key = timeline_field_map.get(status)
        update_data: dict = {"status": status}
        if timeline_key:
            update_data[f"timeline.{timeline_key}"] = now
        if feedback:
            update_data["feedback"] = feedback

        await doc_ref.update(update_data)
        return True

    # ─── NOTIFICATIONS (por worker) ───────────────────────────────────────────

    async def get_notifications(self, client_id: str, user_id: str) -> list:
        query = (
            self._notifs_ref(client_id, user_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(50)
        )
        results = []
        async for doc in query.stream():
            data = doc.to_dict()
            if data:
                data["id"] = doc.id
                data = _normalize_timestamps(data)
                results.append(data)
        return results

    async def mark_notification_read(
        self, client_id: str, notification_id: str, user_id: str
    ) -> bool:
        if notification_id == "all":
            query = self._notifs_ref(client_id, user_id).where("read", "==", False)
            async for doc in query.stream():
                await doc.reference.update({"read": True, "read_at": _now_iso()})
            return True

        doc_ref = self._notifs_ref(client_id, user_id).document(notification_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return False
        await doc_ref.update({"read": True, "read_at": _now_iso()})
        return True

    async def create_notification(
        self, client_id: str, user_id: str, notif_data: dict
    ) -> str:
        notif_id = f"notif_{ulid_lib.ULID()}"
        doc_ref = self._notifs_ref(client_id, user_id).document(notif_id)
        notif_data.update({
            "id":         notif_id,
            "user_id":    user_id,
            "read":       False,
            "created_at": _now_iso(),
        })
        await doc_ref.set(notif_data)
        return notif_id