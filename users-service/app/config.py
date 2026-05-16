from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Definimos las variables que queremos leer y sus valores por defecto
    JWT_SECRET: str = "clave-por-defecto-si-no-hay-env"
    JWT_ALGORITHM: str = "HS256"
    INTERNAL_API_KEY: str = "clave-por-defecto"

    # Le indicamos a Pydantic dónde buscar el archivo y que ignore variables extra de Firebase
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
