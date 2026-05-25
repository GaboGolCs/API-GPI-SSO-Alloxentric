import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    JWT_SECRET:          str = os.getenv("JWT_SECRET", "clave-por-defecto")
    JWT_ALGORITHM:       str = "HS256"
    FIRESTORE_PROJECT:   str = os.getenv("SSO_FIRESTORE_PROJECT", "prueba-sso-gestion-riesgos")
    GOOGLE_CREDENTIALS:  str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")

settings = Settings()
