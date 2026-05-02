import ulid
from google.cloud import firestore
from app.repositories.rep_reports import ReportRepository
from app.schemas.scm_reports import ReportCreate


class ReportService:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def create_report(
        self, client_id: str, report_in: ReportCreate, user_id: str
    ):
        # Generación de ID según convención: rep_ + ULID
        report_id = (
            f"rep_{ulid.ULID()}"  # ULID genera un ID único y ordenable [cite: 118]
        )

        # Transformación y preparación de datos
        report_data = report_in.model_dump()
        report_data.update(
            {
                "report_id": report_id,
                "client_id": client_id,  # Campo obligatorio en todos los documentos
                "reported_by": user_id,
                "created_at": firestore.SERVER_TIMESTAMP,  # Timestamp nativo [cite: 119]
                "status": "open",  # Estado inicial definido en el esquema
            }
        )

        await self.repository.save(client_id, report_id, report_data)
        return report_id
