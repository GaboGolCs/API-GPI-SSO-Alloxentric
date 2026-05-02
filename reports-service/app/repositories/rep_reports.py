from google.cloud import firestore


class ReportRepository:
    def __init__(self, db: firestore.AsyncClient):
        self.db = db

    # Método para guardar un reporte en Firestore
    async def save(self, client_id: str, report_id: str, data: dict):
        # Implementa el aislamiento multi-tenant definido en el documento [cite: 26, 116]
        doc_ref = (
            self.db.collection("clients")
            .document(client_id)
            .collection("reports")
            .document(report_id)
        )
        await doc_ref.set(data)
