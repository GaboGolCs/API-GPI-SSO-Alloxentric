import os
from dotenv import load_dotenv
from google.cloud import firestore
from google.oauth2 import service_account
from app.conf_reports import settings

# 1. Forzamos la carga de las variables del .env al sistema operativo
load_dotenv()

# 2. Rescatamos la ruta absoluta que pusiste en tu .env
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# 3. Creamos las credenciales explícitamente
credentials = service_account.Credentials.from_service_account_file(cred_path)


async def get_db():
    """
    Devuelve el cliente AsyncClient de Firestore con las credenciales forzadas.
    """
    # 4. Le pasamos las credenciales directamente al cliente de Google
    db = firestore.AsyncClient(
        project=settings.firestore_project, credentials=credentials
    )

    try:
        yield db
    finally:
        pass


# Simulamos keycloak con un usuario fijo para pruebas
def get_mock_user():
    # Simula un trabajador autenticado
    return {"user_id": "worker_99", "role": "worker", "client_id": "allox_01"}
