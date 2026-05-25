import ulid
from datetime import datetime
from app.repositories.rep_reports import ReportRepository
from app.schemas.scm_reports import ReportCreate
from app.services.cloudinary_service import upload_image  # Importación asíncrona existente

STATUS_LABELS = {
    "open":      "En Revisión",
    "reviewing": "En Revisión",
    "assigned":  "Acción Asignada",
    "closed":    "Cerrado",
}


class ReportService:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    # ─── REPORTS ──────────────────────────────────────────────────────────────

    async def create_report(self, client_id: str, report_in: ReportCreate, user_id: str, file_bytes: bytes) -> str:
        # 1. Generamos el ID único con el formato de tu negocio
        report_id = f"rep_{ulid.ULID()}"
        
        # 2. Subimos la imagen a Cloudinary si se enviaron bytes válidos
        image_url = None
        if file_bytes and len(file_bytes) > 0:
            image_url = await upload_image(file_bytes, report_id)

        # 3. Mapeamos los datos base del reporte desde el esquema Pydantic
        report_data = report_in.model_dump()
        
        # Generamos una estampa de tiempo en formato ISO String nativo compatible con JS `new Date()`
        current_time_iso = datetime.utcnow().isoformat()

        report_data.update({
            "report_id":   report_id,
            "client_id":   client_id,
            "reported_by": user_id,  # <-- El UID real extraído automáticamente desde el Token JWT
            "image_url":   image_url,
            "evidences":   [image_url] if image_url else [],  # <-- Duplicamos aquí para retrocompatibilidad móvil
            "created_at":  current_time_iso,  # Cadena limpia para evitar crasheos de fechas en el Command Center
            "status":      "open",
            "timeline": {
                "sent":    current_time_iso,
            },
        })

        # 4. Guardamos el diccionario estructurado a través del patrón repositorio
        await self.repository.save(client_id, report_id, report_data)

        # Notificación automática al crear reporte
        await self.repository.create_notification(client_id, user_id, {
            "type":      "actualizacion",
            "title":     "Reporte recibido",
            "body":      "Tu reporte fue enviado y está siendo revisado.",
            "report_id": report_id,
        })

        return report_id

    async def get_all(self, client_id: str, user_id: str) -> list:
        return await self.repository.get_all(client_id, user_id)

    async def get_by_id(self, client_id: str, report_id: str) -> dict | None:
        return await self.repository.get_by_id(client_id, report_id)

    async def update_status(
        self,
        client_id: str,
        report_id: str,
        status: str,
        feedback: str = "",
    ) -> bool:
        # 1. Obtener el reporte para saber a quién notificar
        report = await self.repository.get_by_id(client_id, report_id)
        if not report:
            return False

        # 2. Actualizar estado + timeline + feedback en Firestore
        ok = await self.repository.update_status(client_id, report_id, status, feedback)
        if not ok:
            return False

        # 3. Crear notificación para el trabajador
        user_id = report.get("reported_by", "")
        if user_id:
            label = STATUS_LABELS.get(status, status)
            body  = f"Tu reporte cambió a: {label}"
            if feedback:
                body += f"\n\nComentario del supervisor: {feedback}"

            await self.repository.create_notification(client_id, user_id, {
                "type":      "actualizacion",
                "title":     f"Reporte actualizado → {label}",
                "body":      body,
                "report_id": report_id,
            })

        return True

    # ─── WORKER STATS ─────────────────────────────────────────────────────────

    async def get_worker_stats(self, client_id: str, user_id: str, period: str = "month") -> dict:
        reports = await self.repository.get_all(client_id, user_id)
        total         = len(reports)
        
        # En lugar de buscar "open", contamos cuántos están "closed" y el resto son abiertos
        closed        = sum(1 for r in reports if r.get("status") == "closed")
        open_reports  = total - closed  # Esto sumará el reporte nuevo aunque tenga otro sub-estado
        
        iap           = sum(1 for r in reports if r.get("is_iap"))
        effectiveness = round((closed / total * 100), 1) if total > 0 else 0.0
        
        return {
            "period":              period,
            "total_reports":       total,
            "reports_this_period": open_reports,  # <-- Forzamos el número real de activos
            "closed_reports":      closed,
            "effectiveness_rate":  effectiveness,
            "iap_reports":         iap,
        }

    # ─── NOTIFICATIONS ────────────────────────────────────────────────────────

    async def get_notifications(self, client_id: str, user_id: str) -> dict:
        notifs = await self.repository.get_notifications(client_id, user_id)
        unread = sum(1 for n in notifs if not n.get("read", False))
        return {"data": notifs, "unread_count": unread}

    async def mark_notification_read(
        self, client_id: str, notification_id: str, user_id: str
    ) -> bool:
        return await self.repository.mark_notification_read(client_id, notification_id, user_id)