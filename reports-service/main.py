from fastapi import FastAPI
from app.routers import reports_router

app = FastAPI(title="SSO API - Microservicio de Reportes")

app.include_router(reports_router.router, prefix="/v1")


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "Service is running"}
