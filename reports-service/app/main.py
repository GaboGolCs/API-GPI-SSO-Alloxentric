from fastapi import FastAPI
from app.routers import rt_reports

app = FastAPI(title="SSO Reports Service")

# Incluimos las rutas de reportes
app.include_router(rt_reports.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "reports-service"}
