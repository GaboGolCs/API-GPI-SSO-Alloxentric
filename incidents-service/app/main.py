from fastapi import FastAPI
from app.routers import incidents

app = FastAPI(title="SSO API - Microservicio de Incidentes")

app.include_router(incidents.router, prefix="/v1")


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "Service is running"}
