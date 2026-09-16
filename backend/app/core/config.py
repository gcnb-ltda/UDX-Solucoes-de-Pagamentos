from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_name: str = "UDX Solucoes de Pagamentos"
    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str = "dev-only-change-me-with-at-least-32-random-characters"
    bootstrap_token: str = "dev-bootstrap-change-me"
    database_url: str = "postgresql+psycopg://udx:udx@localhost:5432/udx_payments"
    redis_url: str = "redis://localhost:6379/0"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "udx-payments"
    jwt_audience: str = "udx-payments-api"
    jwt_access_minutes: int = 15
    jwt_refresh_days: int = 7
    jwt_mfa_challenge_minutes: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
