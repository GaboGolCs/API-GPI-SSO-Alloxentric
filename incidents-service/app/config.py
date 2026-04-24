from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Variables base que Pydantic buscará en el entorno
    environment: str = "development"
    project_name: str = "SSO Incidents Service"
    version: str = "1.0.0"

    # Simulamos variables de Keycloak que pide tu documentación
    keycloak_url: str = "https://auth.sso.alloxentric.com"
    keycloak_realm: str = "sso-realm"

    # Configuración para que lea automáticamente un archivo .env si existe
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SSO_")


# Creamos una instancia global (Singleton) para usarla en todo el proyecto
settings = Settings()
