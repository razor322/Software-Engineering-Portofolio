from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OfficeHub"
    environment: str = "development"  # development | staging | production
    api_v1_prefix: str = "/api/v1"
    # ponytail: dev default points at docker-compose Postgres on 5433
    # (5432 occupied by the local PostgreSQL service)
    database_url: str = "postgresql+asyncpg://officehub:officehub@localhost:5433/officehub"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
