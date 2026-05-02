from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    firestore_project: str

    # Le decimos que lea del archivo .env y busque el prefijo SSO_
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="SSO_", extra="ignore"
    )


# Instanciamos las configuraciones para usarlas en el resto de la app
settings = Settings()  # type: ignore
