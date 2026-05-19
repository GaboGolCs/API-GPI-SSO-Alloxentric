from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import dashboard

load_dotenv()

app = FastAPI(
    title="Dashboard Service - SSO Alloxentric",
    description="Microservicio de Dashboard y Heat Map para la plataforma SSO",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción reemplazar por la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "dashboard-service"}
