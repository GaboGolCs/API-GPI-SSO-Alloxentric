# Aqui manejamos la logica de negocio, reglas, validaciones, etc.
# Es el intermediario entre el router (que maneja las solicitudes) y
# el repositorio (que maneja la base de datos).
# Aqui podemos hcaer modificaciones a la solicitud por ejemplo.

from app.repositories.incident_repo import IncidentRepository
from app.schemas.scm_incidents import IncidentCreate


class IncidentService:
    def __init__(self):
        # El servicio instancia el repositorio que necesita
        self.repo = IncidentRepository()

    def get_all_incidents(self):
        # Aquí podríamos filtrar o transformar datos antes de devolverlos
        return self.repo.get_all()

    def get_incident_by_id(self, client_id: str):
        print(
            f"Buscando incidente con ID de cliente: {client_id}"
        )  # Imprime el ID para verificar que se recibe correctamente.
        # Aquí podríamos agregar lógica para manejar casos especiales, como si el incidente no existe
        bd_response = self.repo.get_by_id(client_id)
        if bd_response is None:
            print(f"No se encontró ningún incidente con ID de cliente: {client_id}")
            return {"error": "Incident not found"}

        return bd_response

    def create_incident(self, data: IncidentCreate, user_id: str):
        # Aquí podríamos agregar reglas de negocio, por ejemplo:
        # "Si risk_level es 'critical', enviar alerta al gerente" (lo haremos luego)
        return self.repo.create(data, user_id)
