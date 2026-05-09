from fastapi import FastAPI
from app.routers import rt_reports

from fastapi.middleware.cors import CORSMiddleware

# Middleware estándar para permitir peticiones desde el Frontend
app = FastAPI(title="SSO Reports Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se cambia por la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos las rutas de reportes
app.include_router(rt_reports.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "reports-service"}
