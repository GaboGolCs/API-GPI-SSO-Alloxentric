import jwt
import os
import logging
from dotenv import load_dotenv
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import firestore
from app.config import settings


logger = logging.getLogger(__name__)

# En get_current_user, en el except:

load_dotenv()

_db_client = None


def get_db() -> firestore.AsyncClient:
    global _db_client
    if _db_client is None:
        _db_client = firestore.AsyncClient(project=settings.FIRESTORE_PROJECT)
    return _db_client


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    if credentials is None:
        return {"user_id": "usr_admin", "role": "sso_manager", "client_id": "cliente_prueba_123"}
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return {
            "user_id":   payload.get("sub"),
            "role":      payload.get("role", "sso_manager"),
            "client_id": payload.get("client_id", "cliente_prueba_123"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.PyJWTError as e:
        logger.error(f"JWT error: {e}")
    raise HTTPException(status_code=401, detail=f"Token inválido: {e}")
