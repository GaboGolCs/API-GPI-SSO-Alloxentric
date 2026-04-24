# Este archvo simula una coneccion con la base de datos, en este caso una coleccion de Firestore, pero en memoria.
# mas adelante implementaremos firestore

import uuid
from datetime import datetime
from app.schemas.incident import IncidentCreate

# Simulamos la colección de Firestore en memoria
_firestore_dummy_db = []


# Clase que maneja la interaccion con el dummy db
# get para traer todos los incidentes
# create para agregar un nuevo incidente en el arreglo
# con un id unico, el id del usuario que reporta, el estado inicial "reported" y la fecha de creacion.
#  Ademas de los datos del incidente.
class IncidentRepository:
    def get_all(self):
        return _firestore_dummy_db

    def create(self, incident_data: IncidentCreate, user_id: str) -> dict:
        new_incident = {
            "id": f"inc_{uuid.uuid4().hex[:6]}",
            "reporter_id": user_id,
            "status": "reported",
            "created_at": datetime.now(),
            **incident_data.model_dump(),
        }
        _firestore_dummy_db.append(new_incident)
        return new_incident
