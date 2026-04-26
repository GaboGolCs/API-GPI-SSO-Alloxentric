from fastapi import APIRouter, Depends  # Creador de rutas y inyector de dependecias
from typing import List
from app.schemas.reports_schema import (
    Report_Response,
)  # Esquema de datos para la respuesta del reporte

from app.services.reports_service import (
    ReportsService,
)  # Importamos el servicio (logica de negocio o BD)


router = APIRouter(prefix="/reports", tags=["Reports"])


# Response_model=List[Report_Response]:
# Indica que la respuesta de este endpoint será una lista de objetos del tipo Report
# Creada con pydantic, lo que ayuda a FastAPI a validar y documentar correctamente la salida.
@router.get("/", response_model=List[Report_Response])
async def read_reports(service: ReportsService = Depends(ReportsService)):
    # Creamos el objeto de la clase ReportsService usando Depends.
    return await service.get_reports()
