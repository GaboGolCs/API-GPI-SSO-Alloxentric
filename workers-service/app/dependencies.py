from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.cloud import firestore, storage
from jose import JWTError, jwt

from app.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=True)


# ─── CurrentUser ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CurrentUser:
    id: str         # user_id del payload JWT
    role: str       # "worker" | "supervisor" | "admin"
    client_id: str  # ID de la organización
    email: str


# ─── Firestore client ──────────────────────────────────────────────────────


def get_db(
    settings: Annotated[Settings, Depends(get_settings)],
) -> firestore.AsyncClient:
    import os
    import json
    from google.oauth2 import service_account

    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
    project    = settings.sso_firestore_project

    if creds_json:
        # Render: credenciales como variable de entorno
        creds_dict  = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.AsyncClient(project=project, credentials=credentials)
    else:
        # Local: usa GOOGLE_APPLICATION_CREDENTIALS (archivo)
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        return firestore.AsyncClient(project=project, credentials=credentials)


# ─── Cloud Storage client ──────────────────────────────────────────────────


def get_storage_client() -> storage.Client:
    return storage.Client()


# ─── Auth — verifica JWT firmado por auth-service con HS256 ───────────────


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    """
    Valida el JWT que emite el auth-service.

    El token debe incluir estos campos en el payload:
        {
            "sub":       "user_id",
            "role":      "worker" | "supervisor" | "admin",
            "client_id": "client_abc",
            "email":     "usuario@dominio.com"
        }

    Header de la request:
        Authorization: Bearer <token>
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        user_id: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        client_id: str | None = payload.get("client_id")

        if not user_id or not role or not client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El token no contiene los campos requeridos: sub, role, client_id.",
            )

        return CurrentUser(
            id=user_id,
            role=role,
            client_id=client_id,
            email=payload.get("email", ""),
        )

    except JWTError:
        raise credentials_exception


# ─── Role verification ────────────────────────────────────────────────────


def verify_role(*allowed_roles: str):
    """Dependency factory — lanza 403 si el rol del usuario no está permitido."""

    async def _check(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El rol '{current_user.role}' no tiene acceso a este recurso.",
            )
        return current_user

    return _check
