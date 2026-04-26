from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


# 1. Definimos las opciones válidas para el tipo de reporte
class ReportType(str, Enum):
    incident = "incident"
    audit = "audit"
    inspection = "inspection"


# 2. Esquema Base: Lo que es común para crear y leer
class ReportBase(BaseModel):
    title: str = Field(..., description="Título descriptivo del reporte")
    type: ReportType = Field(..., description="Tipo de reporte")
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filtros usados para generar el reporte (ej. rango de fechas, planta)",
    )


# 3. Esquema para Crear: Lo que nos envía el frontend
class ReportCreate(ReportBase):
    # Nota: No pedimos 'generated_by' ni 'generated_at' porque esos los
    # pondrá el backend automáticamente por seguridad.
    pass


# 4. Esquema de Salida: Lo que le devolvemos al frontend (El documento completo)
class Report_Response(ReportBase):
    id: str
    generated_by: str = Field(..., description="ID del usuario que solicitó el reporte")
    generated_at: datetime
    file_url: Optional[str] = Field(
        None, description="URL de descarga en Google Cloud Storage"
    )

    class Config:
        from_attributes = True
