from datetime import timedelta
from fastapi import APIRouter, Depends
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.services.auth_service import AuthService
from app.dependencies import (
    get_auth_service,
    get_current_user,
)  # Importamos de dependencies.py

router = APIRouter(prefix="/v1/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, service: AuthService = Depends(get_auth_service)
):
    return await service.login(payload)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest, service: AuthService = Depends(get_auth_service)
):
    payload_data = service.verify_token(payload.refresh_token, check_refresh=True)
    access_payload = {
        "sub": payload_data["sub"],
        "client_id": payload_data.get("client_id", ""),
        "role": payload_data.get("role", "worker"),
    }
    new_access = service.generate_jwt(access_payload, timedelta(minutes=30))

    return TokenResponse(
        access_token=new_access,
        refresh_token=payload.refresh_token,
        user_id=payload_data["sub"],
        role=payload_data.get("role", "worker"),
    )


# Ya que estamos aquí, podemos agregar el GET /me que pidió tu jefe
@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # Simplemente devolvemos lo que decodificamos del token
    return {
        "user_id": current_user.get("sub"),
        "client_id": current_user.get("client_id"),
        "role": current_user.get("role"),
    }
