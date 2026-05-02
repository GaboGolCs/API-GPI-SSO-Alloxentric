# Definicion de los esquemas de datos para los incidentes, definimos las claves y sus tipos,
# Tenemos validaciones basicas como longitud minima para la descripcion,
# y ejemplos para facilitar la documentacion automatica de FastAPI.

from pydantic import BaseModel, Field
from datetime import datetime


# Usamos una clase para definir los campos necesarios para un incidente
class IncidentCreate(BaseModel):
    id_client: int = Field(..., example="area_001")  # En Field definimos reglas
    title: str = Field(..., example="Example incident title")
    description: str = Field(..., example="high")


# Util para aniadir info extra cuando el incidente ya esta creado.
class Incident(IncidentCreate):
    id_incident: int = Field(..., min_length=10)  # ... = campo obligatorio
    status: str = Field(..., example="reported")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True  # Permite crear un Incident a partir de un
        # objeto con atributos similares en este caso un BD
