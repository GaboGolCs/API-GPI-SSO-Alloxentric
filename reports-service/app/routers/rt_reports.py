from fastapi import APIRouter, Depends, status
from app.dep_reports import get_db, get_mock_user
from app.services.srv_reports import ReportService
from app.repositories.rep_reports import ReportRepository
from app.schemas.scm_reports import ReportCreate

router = APIRouter(prefix="/v1/reports")


# Enpoint para postear un nuevo reporte, se espera un objeto ReportCreate en el cuerpo de la solicitud.
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_report(
    report_in: ReportCreate,
    db=Depends(get_db),
    current_user=Depends(
        get_mock_user
    ),  # Simula Obtener el client_id del JWT [cite: 105, 136]
):
    # Inyección de dependencias manual o vía contenedor
    repository = ReportRepository(db)
    service = ReportService(repository)
    current_user = get_mock_user()
    # Simula Obtener el client_id del JWT [cite: 105, 136]

    print(
        "Usuario simulado para el reporte:", current_user
    )  # Debug: Verificar el usuario simulado
    report_id = await service.create_report(
        client_id=current_user["client_id"],
        report_in=report_in,
        user_id=current_user["user_id"],
    )

    return {"report_id": report_id}
