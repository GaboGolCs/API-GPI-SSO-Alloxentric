from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

class UserBase(BaseModel):
    name: str = Field(..., description="Nombre completo del usuario")
    email: EmailStr = Field(..., description="Correo electrónico")
    role: str = Field(..., description="worker, analyst, sso_manager, admin")
    assigned_areas: List[str] = Field(
        default_factory=list, description="IDs de las áreas asignadas"
    )
    # 🌟 Opcional con valor por defecto en la base para que no reclame en la entrada
    client_id: Optional[str] = Field(None, description="ID del cliente corporativo")


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=6, description="Contraseña en texto plano (será encriptada)"
    )


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    assigned_areas: Optional[List[str]] = None
    status: Optional[str] = Field(None, description="active, inactive")
    password: Optional[str] = Field(
        None, min_length=6, description="Nueva contraseña si desea cambiarla"
    )


class UserResponse(UserBase):
    user_id: str
    status: str
    # 🌟 Lo dejamos igual que en la base o permitimos que sea un string dinámico
    client_id: Optional[str] = Field(None, description="ID del cliente asociado")

    class Config:
        from_attributes = True


class CurrentUser(BaseModel):
    id: str
    role: str
    client_id: str