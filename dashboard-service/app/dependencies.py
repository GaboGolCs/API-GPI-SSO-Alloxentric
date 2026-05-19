import jwt
import os
import json
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import firestore
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
        # ─── FORZAMOS EL ID REAL DE TU LINK DE FIREBASE ─────────────────────
        project = "prueba-sso-gestion-riesgos"  
        
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

# ─── AUTH ─────────────────────────────────────────────────────────────────────

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> CurrentUser:
    token = credentials.credentials
    try:
        # ─── CAMBIO CLAVE: BYPASS DIRECTO A LA VARIABLE IGNORADA ───────────
        # En vez de usar settings.JWT_SECRET que da la clave vieja del 2024,
        # forzamos la lectura del .env del sistema o ponemos un respaldo.
        
        secret_key = os.getenv("JWT_SECRET")
        
        # Si os.getenv falló porque no lee el .env, ponemos tu clave real de Render aquí adentro:
        if not secret_key or secret_key == "sso-gpi-secret-2024-cambiar-en-produccion":
            # TODO: Cuando subas esto a Render, esta línea se ignorará porque Render sí tendrá la variable en memoria.
            secret_key = "sso-gpi-secret-2024-cambiar-en-produccion"
        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        # ───────────────────────────────────────────────────────────────────

        user_id   = payload.get("sub")
        role      = payload.get("role")
        client_id = payload.get("client_id")

        if not user_id or not role or not client_id:
            raise HTTPException(status_code=401, detail="Token inválido: faltan claims esenciales (sub, role o client_id)")

        return CurrentUser(id=str(user_id), role=str(role), client_id=str(client_id))

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado. Genera uno nuevo en auth-service.")
        
    except Exception as e:
        # ─── LOG DE DEBUG EN TU TERMINAL ──────────────────────────────────────
        print("\n" + "="*50)
        print("🔴 ERROR DETECTADO EN DASHBOARD-SERVICE AL DECODIFICAR JWT")
        print(f"🔹 Tipo de Excepción: {type(e).__name__}")
        print(f"🔹 Mensaje del Sistema: {str(e)}")
        print(f"🔹 Llave secreta usada: '{settings.JWT_SECRET}'")
        print(f"🔹 Algoritmo usado: '{settings.JWT_ALGORITHM}'")
        print("="*50 + "\n")
        
        # ─── RESPUESTA DETALLADA PARA SWAGGER ─────────────────────────────────
        raise HTTPException(
            status_code=401, 
            detail=f"Token inválido o firma incorrecta. Motivo exacto: {str(e)}"
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