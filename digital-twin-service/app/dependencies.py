import jwt
import os
import json
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import firestore, storage
from google.oauth2 import service_account
from typing import Callable
from pydantic import BaseModel
from app.config import settings

from dotenv import load_dotenv
load_dotenv()

# ─── CURRENT USER MODEL ───────────────────────────────────────────────────────

class CurrentUser(BaseModel):
    id:        str
    role:      str
    client_id: str

# ─── FIRESTORE ────────────────────────────────────────────────────────────────

_db_client = None

def get_db() -> firestore.AsyncClient:
    global _db_client
    if _db_client is None:
        project   = settings.SSO_FIRESTORE_PROJECT
        creds_json = settings.GOOGLE_CREDENTIALS_JSON

        if creds_json:
            # Render: credenciales como variable de entorno JSON
            creds_dict  = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            _db_client  = firestore.AsyncClient(project=project, credentials=credentials)
        else:
            # Local: usa GOOGLE_APPLICATION_CREDENTIALS (archivo)
            _db_client = firestore.AsyncClient(project=project)
    return _db_client

# ─── CLOUD STORAGE ────────────────────────────────────────────────────────────

_storage_client = None

def get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        creds_json = settings.GOOGLE_CREDENTIALS_JSON
        if creds_json:
            creds_dict  = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            _storage_client = storage.Client(
                project=settings.SSO_FIRESTORE_PROJECT,
                credentials=credentials,
            )
        else:
            _storage_client = storage.Client()
    return _storage_client

# ─── AUTH ─────────────────────────────────────────────────────────────────────

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> CurrentUser:
    token = credentials.credentials
    try:
        secret_key = os.getenv("JWT_SECRET", settings.JWT_SECRET)

        payload = jwt.decode(token, secret_key, algorithms=["HS256"])

        user_id   = payload.get("sub")
        role      = payload.get("role")
        client_id = payload.get("client_id")

        if not user_id or not role or not client_id:
            raise HTTPException(
                status_code=401,
                detail="Token inválido: faltan claims esenciales (sub, role o client_id)",
            )

        return CurrentUser(id=str(user_id), role=str(role), client_id=str(client_id))

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado.")

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token inválido o firma incorrecta. Motivo: {str(e)}",
        )


def verify_role(*allowed_roles: str) -> Callable:
    """Fábrica de dependencias para verificar roles."""
    def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"No permitido. Tu rol es '{current_user.role}'. Roles requeridos: {list(allowed_roles)}",
            )
        return current_user
    return role_checker
