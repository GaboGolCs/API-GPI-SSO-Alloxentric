from google.cloud.firestore import AsyncClient
from ulid import ULID
from datetime import datetime, timezone


class IncidentRepository:
    def __init__(self, db: AsyncClient):
        self.db = db

    async def create(self, client_id: str, incident_data: dict):
        """
        Guarda un incidente siguiendo el modelo de colecciones y convenciones.
        """
        # Convención 6.3: IDs generados por backend (prefijo + ULID)
        report_id = f"rep_{str(ULID())}"

        # Inyectamos campos automáticos del backend
        incident_data["report_id"] = report_id
        incident_data["client_id"] = client_id  # Aislamiento multi-tenant
        incident_data["created_at"] = datetime.now(timezone.utc)  # Firestore Timestamp

        # Ruta según especificación 6.2: Subcolección de clients
        doc_ref = (
            self.db.collection("clients")
            .document(client_id)
            .collection("reports")
            .document(report_id)
        )

        # Operación asíncrona para guardar en Firestore
        await doc_ref.set(incident_data)

        return incident_data
