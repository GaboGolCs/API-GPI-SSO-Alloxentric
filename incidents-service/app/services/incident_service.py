# Aqui manejamos la logica de negocio, reglas, validaciones, etc.
# Es el intermediario entre el router (que maneja las solicitudes) y
# el repositorio (que maneja la base de datos).
# Aqui podemos hcaer modificaciones a la solicitud por ejemplo.

from app.repositories.incident_repo import IncidentRepository
from app.schemas.incident import IncidentCreate


class IncidentService:
    def __init__(self):
        # El servicio instancia el repositorio que necesita
        self.repo = IncidentRepository()

    def get_all_incidents(self):
        # Aquí podríamos filtrar o transformar datos antes de devolverlos
        return self.repo.get_all()

    def create_incident(self, data: IncidentCreate, user_id: str):
        # Aquí podríamos agregar reglas de negocio, por ejemplo:
        # "Si risk_level es 'critical', enviar alerta al gerente" (lo haremos luego)
        return self.repo.create(data, user_id)
