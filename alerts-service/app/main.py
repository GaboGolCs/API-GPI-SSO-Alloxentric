from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import alerts
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Alerts Service - SSO Alloxentric",
    description="Microservicio para el Centro de Alertas del sistema SSO",
    version="1.0.0",
)

# 1. Definimos explícitamente los orígenes permitidos
# Al quitar el "*", solucionamos el conflicto con allow_credentials=True
origins = [
    "https://gpi-websso.vercel.app",  # Tu frontend en Vercel
    "http://localhost:5173",          # Tu entorno local con Vite/React
    "http://localhost:3000",          # Por si usas otro puerto local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # ← Pasamos la lista explícita aquí
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "alerts-service"}