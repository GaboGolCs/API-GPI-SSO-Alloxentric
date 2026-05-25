import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    JWT_SECRET: str = os.getenv("JWT_SECRET", "clave-por-defecto")
    JWT_ALGORITHM: str = "HS256"
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "clave-por-defecto")

settings = Settings()