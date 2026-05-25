import jwt
import os
import json
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import firestore
from google.oauth2 import service_account
from typing import Callable  # Quitamos List ya que ahora usamos argumentos posicionales (*args)
from app.schemas.user import CurrentUser
from app.config import settings

from dotenv import load_dotenv
load_dotenv()

_db_client = None
security_bearer = HTTPBearer()

# 1. Tu función original de Firebase (Intacta y Correcta)
def get_db() -> firestore.AsyncClient:
    global _db_client
    if _db_client is None:
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        project    = os.getenv("SSO_FIRESTORE_PROJECT", "prueba-sso-gestion-riesgos")
        if creds_json:
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            _db_client = firestore.AsyncClient(project=project, credentials=credentials)
        else:
            _db_client = firestore.AsyncClient(project=project)
    return _db_client


# 2. Dependencia para extraer y validar el usuario actual desde el JWT Token
# 2. Dependencia para extraer y validar el usuario actual desde el JWT Token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_bearer)) -> CurrentUser:
    token = credentials.credentials
    try:
        # Decodificamos el token JWT (Asegúrate de que la propiedad de tus settings coincida)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        # 🌟 Inicializamos el esquema STRICTAMENTE con los campos que posee
        user = CurrentUser(
            id=payload.get("sub"),
            role=payload.get("role"),
            client_id=payload.get("client_id")
        )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido o expirado."
        )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido o expirado."
        )


# 3. LA FUNCIÓN MODIFICADA: Ahora acepta múltiples strings separados por comas
def verify_role(*allowed_roles: str) -> Callable:
    """
    Verifica si el usuario autenticado tiene uno de los roles permitidos.
    El asterisco (*) permite recibir parámetros sueltos: Depends(verify_role("admin", "sso_manager"))
    """
    def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        # allowed_roles ahora se comporta internamente como una tupla: ('admin', 'sso_manager')
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los permisos necesarios (Rol insuficiente)."
            )
        return current_user
    return role_checker