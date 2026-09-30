from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OfficeHub"
    environment: str = "development"  # development | staging | production
    api_v1_prefix: str = "/api/v1"
    # dev runs against the machine's local PostgreSQL service (Docker compose is optional)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/officehub"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    session_ttl_hours: int = 8

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
