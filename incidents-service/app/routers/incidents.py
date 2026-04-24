from fastapi import APIRouter, Depends  # Creador de rutas y inyector de dependecias
from typing import (
    List,
)  # Para definir que el endpoint devuelve una lista de incidentes no solo 1

from app.schemas.incident import Incident, IncidentCreate  # Importamos esquemas
from app.services.incident_service import (
    IncidentService,
)  # Importamos el servicio (logica de negocio o BD)

from app.dependencies import get_current_user, get_incident_service


# Crea un router específico para manejar todo lo relacionado con incidentes.
# prefix="/incidents": Define que todas las rutas de este archivo tendrán /incidents al principio.
# tags=["Incidents"]: Usa este texto para agrupar los métodos en la documentación automática de Swagger.
router = APIRouter(prefix="/incidents", tags=["Incidents"])


# response_model=List[Incident]: Indica que la respuesta de este endpoint será una lista de objetos del tipo Incident,
# lo que ayuda a FastAPI a validar y documentar correctamente la salida.
@router.get("/", response_model=List[Incident])
def get_incidents(service: IncidentService = Depends(get_incident_service)):
    return service.get_all_incidents()


@router.post("/", response_model=Incident, status_code=201)
# Dependencias: get_current_user para obtener info del usuario que hace la solicitud y
# get_incident_service para usar la logica de negocio
def create_incident(
    payload: IncidentCreate,
    current_user: dict = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
):
    return service.create_incident(payload, current_user["user_id"])
