import os
import json
import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import firestore
from google.oauth2 import service_account
from app.conf_reports import settings

load_dotenv()

JWT_SECRET    = os.getenv("JWT_SECRET") or getattr(settings, "JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# ─── FIRESTORE ────────────────────────────────────────────────────────────────

_db_client = None

def _get_credentials():
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
    if creds_json:
        return service_account.Credentials.from_service_account_info(json.loads(creds_json))
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if cred_path:
        return service_account.Credentials.from_service_account_file(cred_path)
    raise RuntimeError("No se encontraron credenciales de Firebase")

async def get_db():
    global _db_client
    if _db_client is None:
        _db_client = firestore.AsyncClient(
            project=settings.firestore_project,
            credentials=_get_credentials(),
        )
    yield _db_client

# ─── AUTH ─────────────────────────────────────────────────────────────────────

security = HTTPBearer(auto_error=True)

def get_current_user(
    credentials_bearer: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    if not credentials_bearer:
        raise HTTPException(status_code=401, detail="Token requerido")
    try:
        payload = jwt.decode(
            credentials_bearer.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido: falta sub")
        return {
            "user_id":   user_id,
            "role":      payload.get("role", "worker"),
            "client_id": payload.get("client_id", "allox_01"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_mock_user() -> dict:
    """Solo para compatibilidad — los routers deben usar get_current_user()"""
    raise HTTPException(status_code=401, detail="Autenticación requerida")