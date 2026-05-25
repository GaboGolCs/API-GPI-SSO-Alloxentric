import jwt
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.srv_incidents import IncidentService

load_dotenv()

JWT_SECRET    = os.getenv("JWT_SECRET", "clave-por-defecto")
JWT_ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    # Si no hay token, devolvemos mock para pruebas en Swagger
    if credentials is None:
        return {"user_id": "usr_abc123", "role": "worker", "client_id": "cliente_prueba_123"}
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "user_id":   payload.get("sub"),
            "role":      payload.get("role", "worker"),
            "client_id": payload.get("client_id", "cliente_prueba_123"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


def get_incident_service() -> IncidentService:
    return IncidentService()