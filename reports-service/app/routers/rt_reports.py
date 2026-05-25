from fastapi import APIRouter, Depends, status, HTTPException, Security, Form, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.dep_reports import get_db, get_current_user
from app.services.srv_reports import ReportService
from app.repositories.rep_reports import ReportRepository
from app.schemas.scm_reports import ReportCreate

router  = APIRouter()
security = HTTPBearer(auto_error=False)


def get_service(db=Depends(get_db)) -> ReportService:
    return ReportService(ReportRepository(db))


class StatusUpdate(BaseModel):
    status:   str
    feedback: str = ""


# ─── REPORTS ──────────────────────────────────────────────────────────────────

# REMEDIO: Quitamos la barra "/" final para que responda directamente a "/v1/reports" sin redirecciones mutadas
@router.post("/v1/reports")  # <-- Forzamos la ruta limpia y directa sin barra final
async def create_report(
    description: str = Form(...),
    area_id: str = Form(...),
    type: str = Form(...),
    shift: str = Form(...),
    file: UploadFile = File(None),
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    current_user = get_current_user(credentials)
    
    # 1. Leemos los bytes del archivo cargado para Cloudinary
    file_bytes = b""
    if file and file.filename != "empty.jpg":
        file_bytes = await file.read()

    # 2. Mapeamos los datos del formulario al esquema ReportCreate que espera tu servicio
    report_in = ReportCreate(
        description=description,
        area_id=area_id,
        type=type,
        shift=shift,
        is_iap=False  
    )

    # 3. Invocar al servicio estructurado
    service = ReportService(ReportRepository(db))
    report_id = await service.create_report(
        client_id=current_user["client_id"],
        report_in=report_in,
        user_id=current_user["user_id"],
        file_bytes=file_bytes
    )

    return {"report_id": report_id}


@router.get("/v1/reports")  # <-- Forzado sin barra final
async def list_reports(
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    current_user = get_current_user(credentials)
    service      = ReportService(ReportRepository(db))
    return await service.get_all(
        client_id=current_user["client_id"],
        user_id=current_user["user_id"],
    )


@router.get("/{report_id}")  # Sincronizado sin slash intermedio duplicado
async def get_report(
    report_id: str,
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    current_user = get_current_user(credentials)
    service      = ReportService(ReportRepository(db))
    report = await service.get_by_id(
        client_id=current_user["client_id"],
        report_id=report_id,
    )
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return report


@router.patch("/v1/reports/{report_id}/status")  # 👈 Agrégale el "/v1/reports" antes
async def update_status(
    report_id: str,
    body: StatusUpdate,
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    current_user = get_current_user(credentials)
    service      = ReportService(ReportRepository(db))
    ok = await service.update_status(
        client_id=current_user["client_id"],
        report_id=report_id,
        status=body.status,
        feedback=body.feedback,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return {"ok": True}


# ─── WORKER STATS ─────────────────────────────────────────────────────────────

@router.get("/v1/workers/me/stats")
async def get_worker_stats(
    period: str = "month",
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    current_user = get_current_user(credentials)
    service      = ReportService(ReportRepository(db))
    return await service.get_worker_stats(
        client_id=current_user["client_id"],
        user_id=current_user["user_id"],
        period=period,
    )


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

@router.get("/v1/workers/me/notifications")
async def get_notifications(
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    current_user = get_current_user(credentials)
    service      = ReportService(ReportRepository(db))
    return await service.get_notifications(
        client_id=current_user["client_id"],
        user_id=current_user["user_id"],
    )


@router.patch("/v1/workers/me/notifications/{notification_id}")
async def mark_notification_read(
    notification_id: str,
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    current_user = get_current_user(credentials)
    service      = ReportService(ReportRepository(db))
    ok = await service.mark_notification_read(
        client_id=current_user["client_id"],
        notification_id=notification_id,
        user_id=current_user["user_id"],
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return {"ok": True}


# ─── ADMIN ────────────────────────────────────────────────────────────────────

@router.get("/v1/admin/reports")
async def list_all_reports(db=Depends(get_db)):
    col_ref = db.collection("clients").document("cliente_prueba_123").collection("reports")
    results = []
    async for doc in col_ref.stream():
        data = doc.to_dict()
        if data:
            results.append(data)
    return results