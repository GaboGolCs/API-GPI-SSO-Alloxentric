# Definicion de los esquemas de datos para los incidentes, definimos las claves y sus tipos,
# Tenemos validaciones basicas como longitud minima para la descripcion,
# y ejemplos para facilitar la documentacion automatica de FastAPI.

from pydantic import BaseModel, Field
from datetime import datetime


# Usamos una clase para definir los campos necesarios para un incidente
class IncidentCreate(BaseModel):
    area_id: str = Field(..., example="area_001")  # En Field definimos reglas
    description: str = Field(..., min_length=10)  # ... = campo obligatorio
    risk_level: str = Field(..., example="high")
    is_iap: bool = False


# Util para aniadir info extra cuando el incidente ya esta creado.
class Incident(IncidentCreate):
    id: str
    status: str
    reporter_id: str
    created_at: datetime

    class Config:
        from_attributes = True  # Permite crear un Incident a partir de un
        # objeto con atributos similares en este caso un BD
