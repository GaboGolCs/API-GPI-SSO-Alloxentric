from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import rt_reports

app = FastAPI(title="SSO Reports Service")

# Permite que el frontend pueda llamar al backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # El asterisco permite TODO
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rt_reports.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "reports-service"}