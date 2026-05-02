from fastapi import FastAPI
from app.routers import rt_incidents

app = FastAPI(title="SSO API - Microservicio de Incidentes")

app.include_router(rt_incidents.router, prefix="/v1")
