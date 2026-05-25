from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "dashboard-service"
    SSO_FIRESTORE_PROJECT: str = "prueba-sso-gestion-riesgos"
    SSO_ENVIRONMENT: str = "development"
    JWT_SECRET: str = "sso-gpi-secret-2024-cambiar-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    GOOGLE_CREDENTIALS_JSON: str | None = None # Contenido del service-account.json en Render

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
