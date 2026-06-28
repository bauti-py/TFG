from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NOMBRE: str = "Plataforma de Gestión de Equipos Inteligente"
    APP_ENV: str = "development"
    API_PREFIJO: str = "/api"

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gestion_equipos"

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "gestion_equipos"

    JWT_SECRET: str = "cambiar-por-una-clave-larga-y-aleatoria"
    JWT_ALGORITMO: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    MAX_INTENTOS_LOGIN: int = 5
    BLOQUEO_MINUTOS: int = 15

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    # Pool de modelos a rotar (separados por coma). Si está vacío, usa GEMINI_MODEL.
    GEMINI_MODELOS: str = ""
    # Minutos que un modelo queda "tmp_out" tras fallar (ej. cuota 429) antes de reusarlo.
    GEMINI_TMP_OUT_MINUTOS: int = 10
    LLM_TIMEOUT_SEGUNDOS: int = 30
    LLM_MAX_REINTENTOS: int = 3

    BOOTSTRAP_ADMIN_EMAIL: str = "lider@demo.com"
    BOOTSTRAP_ADMIN_PASSWORD: str = "Lider123!"
    BOOTSTRAP_ADMIN_NOMBRE: str = "Líder Técnico"

    @property
    def gemini_modelos(self) -> list[str]:
        modelos = [m.strip() for m in self.GEMINI_MODELOS.split(",") if m.strip()]
        return modelos or [self.GEMINI_MODEL]

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()


config = obtener_configuracion()
