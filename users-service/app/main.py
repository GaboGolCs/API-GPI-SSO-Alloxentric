from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users
from dotenv import load_dotenv

load_dotenv()  # Esto busca un archivo .env y lo carga en la memoria

app = FastAPI(
    title="Users Service - SSO Alloxentric",
    description="Microservicio para la gestión de usuarios y roles Multi-tenant",
    version="1.0.0",
)
# Middleware estándar para permitir peticiones desde el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se cambia por la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registramos nuestros endpoints
app.include_router(users.router)


# Endpoint básico de salud (Health Check) para Cloud Run
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "users-service"}
