from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "auth-service"
    JWT_SECRET: str = "super-secret-key-cambiar-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    INTERNAL_API_KEY: str = "clave-por-defecto"

    # URL interna del users-service (ej: http://localhost:8001 o la URL de Cloud Run)
    USERS_SERVICE_URL: str = "http://localhost:8001"

    class Config:
        env_file = (".env",)
        extra = "ignore"


settings = Settings()
