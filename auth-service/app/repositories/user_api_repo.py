import httpx
from app.config import settings


class UserApiRepository:
    def __init__(self):
        self.base_url = settings.USERS_SERVICE_URL

    async def get_user_for_auth(self, client_id: str, email: str):
        # 1. Preparamos la cabecera con el secreto
        headers = {"X-Internal-Token": settings.INTERNAL_API_KEY}

        payload = {"client_id": client_id, "email": email}

        # 2. Enviamos los headers en la petición HTTP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/internal/users/by-email",
                json=payload,
                headers=headers,  # <--- LA LLAVE AQUÍ
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()
