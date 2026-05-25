import httpx
import logging
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

# Configuración óptima de tiempos de espera (Mitiga Cold Starts de Render)
# 15 segundos para esperar datos, 5 segundos para establecer la conexión inicial
HTTP_TIMEOUT = httpx.Timeout(15.0, connect=5.0)

class UserApiRepository:
    def __init__(self):
        self.base_url = settings.USERS_SERVICE_URL

    async def get_user_for_auth(self, client_id: str, email: str):
        headers = {"X-Internal-Token": settings.INTERNAL_API_KEY}
        payload = {"client_id": client_id, "email": email}

        # Pasamos el timeout óptimo al instanciar el cliente
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/internal/users/by-email",
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 404:
                    return None

                # Si responde con 4xx o 5xx (que no sea 404), saltará al bloque HTTPStatusError
                response.raise_for_status()
                return response.json()

            except httpx.ReadTimeout:
                logger.error(f"Timeout leyendo del servicio de usuarios para el email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="El servicio de usuarios tardó demasiado en responder."
                )
            except httpx.ConnectTimeout:
                logger.error("No se pudo conectar con el servicio de usuarios (Servidor apagado o lento).")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="El servicio de usuarios no está disponible temporalmente."
                )
            except httpx.HTTPStatusError as exc:
                logger.error(f"Error devuelto por el servicio de usuarios: {exc.response.status_code} - {exc.response.text}")
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=f"Error en validación de credenciales internas."
                )
            except Exception as exc:
                logger.error(f"Error inesperado de red en UserApiRepository: {str(exc)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error interno de comunicación entre servicios."
                )