from fastapi import FastAPI
from app.routers import rt_incidents
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SSO API - Microservicio de Incidentes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se cambia por la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rt_incidents.router, prefix="/v1")
