from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users
from app.routers import internal
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Users Service - SSO Alloxentric",
    description="Microservicio para la gestión de usuarios y roles Multi-tenant",
    version="1.0.0",
)

# 🌟 Definimos los orígenes explícitos para que funcione con allow_credentials=True
origins = [
    "http://localhost:5173",          # Tu entorno local con Vite
    "http://127.0.0.1:5173",
    "https://gpi-websso.vercel.app"   # Tu app desplegada en Vercel
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # 🌟 Usamos la lista explícita aquí
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(internal.router)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "users-service"}