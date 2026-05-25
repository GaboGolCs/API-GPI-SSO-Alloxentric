from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignora variables del .env que no estén aquí
    )

    # App
    sso_environment: str = "development"
    app_version: str = "1.0.0"
    log_level: str = "INFO"

    # GCP / Firestore
    sso_firestore_project: str
    firestore_database: str = "(default)"

    # Auth — JWT propio con HS256 (firmado por auth-service)
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    # Comunicación interna entre microservicios
    internal_api_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
