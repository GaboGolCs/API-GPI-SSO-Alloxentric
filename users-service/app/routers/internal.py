from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr
from google.cloud.firestore import AsyncClient

from app.services.user_service import UserService
from app.repositories.user_repo import UserRepository
from app.dependencies import get_db
from app.config import settings  # Importamos los settings


# 1. Creamos la función del "candado"
async def verify_internal_token(x_internal_token: str = Header(...)):
    if x_internal_token != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=403, detail="Prohibido: Token interno inválido o ausente"
        )


# 2. Le ponemos el candado a TODO el router interno
router = APIRouter(
    prefix="/v1/internal",
    tags=["Internal"],
    dependencies=[Depends(verify_internal_token)],  # <--- EL CANDADO AQUÍ
)


class InternalAuthRequest(BaseModel):
    client_id: str
    email: EmailStr


def get_user_service(db: AsyncClient = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.post("/users/by-email")
async def get_user_for_auth(
    payload: InternalAuthRequest, service: UserService = Depends(get_user_service)
):
    user = await service.get_user_for_auth_internal(
        client_id=payload.client_id, email=payload.email
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
