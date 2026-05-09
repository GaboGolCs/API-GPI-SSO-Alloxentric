import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import firestore
from typing import Callable
from app.schemas.user import CurrentUser

SECRET_KEY = "tu_super_clave_secreta_temporal_para_desarrollo"  # Esto luego va en .env
ALGORITHM = "HS256"


_db_client = None


def get_db() -> firestore.AsyncClient:
    global _db_client
    if _db_client is None:
        _db_client = firestore.AsyncClient()
    return _db_client


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> CurrentUser:
    token = credentials.credentials
    try:
        # Decodificamos nuestro propio JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 1. Extraemos los valores en variables
        user_id = payload.get("sub")
        role = payload.get("role")
        client_id = payload.get("client_id")

        # 2. Validamos que ninguno sea None
        if not user_id or not role or not client_id:
            raise HTTPException(
                status_code=401,
                detail="Token inválido: Faltan claims requeridos (sub, role o client_id)",
            )

        # 3. Los convertimos explícitamente a string (str) para satisfacer el tipado
        return CurrentUser(id=str(user_id), role=str(role), client_id=str(client_id))

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        # MOCK TEMPORAL: Para que puedas seguir probando en Swagger sin el auth-service aún
        if token == "test-token-admin":
            return CurrentUser(id="usr_test", role="admin", client_id="client_test")
        raise HTTPException(status_code=401, detail="Token inválido")


def verify_role(*allowed_roles: str) -> Callable:
    def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"No permitido. Roles requeridos: {allowed_roles}",
            )
        return current_user

    return role_checker
