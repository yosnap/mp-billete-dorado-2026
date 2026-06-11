from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "MP Billete Dorado 2026"
    app_env: str = "development"
    debug: bool = False

    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Redis
    redis_url: str
    redis_password: str

    # Celery
    celery_broker_url: str
    celery_result_backend: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Admin — obligatorio, sin default para forzar configuración explícita en .env
    admin_token: str

    # Encriptación de email con pgcrypto — cambiar en producción
    pgcrypto_key: str = "dev-pgcrypto-key-change-in-prod"

    # CORS
    allowed_origins: list[str] = ["http://localhost:4321"]

    # SendGrid — requerido para envío de emails en producción
    sendgrid_api_key: str = ""

    # Remitente por defecto para todos los emails de la campaña
    email_from: str = "noreply@mainpaper.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
