from fastapi import APIRouter, Depends, status
from google.cloud.firestore import AsyncClient
from typing import List

from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.repositories.user_repo import UserRepository
from app.dependencies import get_db, CurrentUser, verify_role

# PREFIJO ACTUALIZADO PARA COINCIDIR CON LA TABLA DE FRONTEND
router = APIRouter(prefix="/v1/admin/users", tags=["Users Admin"])


def get_user_service(db: AsyncClient = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("/", response_model=List[UserResponse])
async def list_users(
    service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(verify_role("admin", "sso_manager")),
):
    return await service.get_all_users(client_id=current_user.client_id)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(verify_role("admin", "sso_manager")),
):
    return await service.create_user(client_id=current_user.client_id, user_in=user_in)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(verify_role("admin", "sso_manager")),
):
    return await service.update_user(
        client_id=current_user.client_id, user_id=user_id, user_in=user_in
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(verify_role("admin", "sso_manager")),
):
    await service.delete_user(client_id=current_user.client_id, user_id=user_id)
