from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ReportCreate(BaseModel):
    # Basado en tu formulario e interfaz
    area_id: str = Field(..., example="area_01")
    type: str = Field(..., example="Acto Inseguro")  # Acto o Condición
    is_iap: bool = Field(default=False)  # Interrupción de Alto Potencial
    description: str
    shift: str = Field(..., example="Turno A")
    # En NoSQL guardamos las URLs de las fotos [cite: 26, 112]
    evidences: Optional[List[str]] = []


# Hereda de la clase ReportCreate
class ReportResponse(ReportCreate):
    report_id: str
    status: str = "open"
    reported_by: str
    created_at: datetime
