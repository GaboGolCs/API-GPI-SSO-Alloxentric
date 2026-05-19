from google.cloud import firestore
from datetime import datetime


class DashboardRepository:
    """Abstrae todas las operaciones de Firestore para el dashboard."""

    def __init__(self, db: firestore.AsyncClient):
        self.db = db

    async def get_all_reports(self, client_id: str) -> list:
        """Trae todos los reportes del cliente."""
        col_ref = (
            self.db.collection("clients")
            .document(client_id)
            .collection("reports")
        )
        results = []
        async for doc in col_ref.stream():
            data = doc.to_dict()
            if data:
                data["_doc_id"] = doc.id
                results.append(data)
        return results

    async def get_reports_by_date_range(
        self, client_id: str, date_from: datetime, date_to: datetime
    ) -> list:
        """Trae reportes dentro de un rango de fechas."""
        col_ref = (
            self.db.collection("clients")
            .document(client_id)
            .collection("reports")
        )
        results = []
        async for doc in col_ref.stream():
            data = doc.to_dict()
            if not data:
                continue
            created = data.get("created_at")
            if created:
                try:
                    if hasattr(created, "replace"):
                        dt = created.replace(tzinfo=None)
                    else:
                        dt = datetime.fromisoformat(
                            str(created).replace("Z", "").split(".")[0]
                        )
                    if date_from <= dt <= date_to:
                        results.append(data)
                except Exception:
                    pass
        return results
