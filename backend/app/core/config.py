import json
from functools import lru_cache

from pydantic import model_validator
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

    secret_provider: str = "env"
    aws_secret_name: str | None = None
    aws_region: str = "us-east-1"
    data_encryption_key: str | None = None

    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "udx-payments"
    jwt_audience: str = "udx-payments-api"
    jwt_access_minutes: int = 15
    jwt_refresh_days: int = 7
    jwt_mfa_challenge_minutes: int = 5
    jwt_active_kid: str = "v1"
    jwt_keys_json: str = (
        '{"v1":"dev-only-change-me-with-at-least-32-random-characters"}'
    )

    auth_login_rate_limit: int = 10
    auth_login_rate_window_seconds: int = 60
    auth_mfa_rate_limit: int = 8
    auth_mfa_rate_window_seconds: int = 300
    auth_lock_threshold: int = 5
    auth_lock_max_minutes: int = 60
    mfa_recovery_code_count: int = 10
    allow_manual_settlement: bool = False

    payment_provider: str = "disabled"
    payment_provider_webhook_secret: str | None = None
    payment_provider_timeout_seconds: int = 10
    webhook_replay_window_seconds: int = 300

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        environment = self.app_env.lower()
        if environment != "production":
            return self
        if len(self.app_secret_key) < 32 or self.app_secret_key.startswith("dev-"):
            raise ValueError("APP_SECRET_KEY must be a strong production secret")
        if len(self.bootstrap_token) < 24 or self.bootstrap_token.startswith("dev-"):
            raise ValueError("BOOTSTRAP_TOKEN must be a strong production secret")
        if self.allow_manual_settlement:
            raise ValueError("Manual settlement must be disabled in production")
        if self.payment_provider == "mock":
            raise ValueError("Mock payment provider is forbidden in production")
        if self.payment_provider != "disabled":
            if not self.payment_provider_webhook_secret:
                raise ValueError("PAYMENT_PROVIDER_WEBHOOK_SECRET is required")
            if len(self.payment_provider_webhook_secret) < 32:
                raise ValueError("PAYMENT_PROVIDER_WEBHOOK_SECRET is too short")
        if self.secret_provider == "aws" and not self.aws_secret_name:
            raise ValueError("AWS_SECRET_NAME is required for production AWS secrets")
        if self.secret_provider == "env":
            if not self.data_encryption_key or len(self.data_encryption_key) < 32:
                raise ValueError("DATA_ENCRYPTION_KEY must be set in production")
            key_ring = json.loads(self.jwt_keys_json)
            if (
                not isinstance(key_ring, dict)
                or self.jwt_active_kid not in key_ring
                or any(len(str(value)) < 32 for value in key_ring.values())
            ):
                raise ValueError("JWT_KEYS_JSON must contain strong production keys")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
