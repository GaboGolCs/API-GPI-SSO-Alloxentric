from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.repositories.user_api_repo import UserApiRepository
from app.services.auth_service import AuthService

# 1. Usamos HTTPBearer en lugar de OAuth2PasswordBearer
security = HTTPBearer()


def get_auth_service() -> AuthService:
    repo = UserApiRepository()
    return AuthService(repo)


# 2. Actualizamos la dependencia para leer el token del Header de autorización
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    token = credentials.credentials
    try:
        # Usamos el servicio para validar que el token no haya expirado o sea falso
        payload = service.verify_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
