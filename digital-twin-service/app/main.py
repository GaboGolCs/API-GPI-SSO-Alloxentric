from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import digital_twin
from app.exceptions import register_exception_handlers

load_dotenv()

app = FastAPI(
    title="Digital Twin Service - SSO Alloxentric",
    description="Microservicio para el Gemelo Digital de Planta y Zonas del sistema SSO",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción reemplazar por la URL del frontend
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(digital_twin.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "digital-twin-service"}
