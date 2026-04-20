from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    development = "development"
    testing = "testing"
    production = "production"


class AuthMode(StrEnum):
    jwt = "jwt"
    api_key = "api_key"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: AppEnv = AppEnv.development
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = Field(
        default="mysql+asyncmy://credit_app:credit_app@localhost:3306/credit_analytics",
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False

    auth_mode: AuthMode = AuthMode.jwt
    jwt_secret_key: SecretStr = SecretStr("change-me")
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl_minutes: int = 60
    api_key: SecretStr = SecretStr("change-me")

    bootstrap_admin_login: str = "admin"
    bootstrap_admin_password: SecretStr = SecretStr("admin")

    seed_on_startup: bool = False
    seed_data_dir: Path = Path("./data")

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        if "+" not in value:
            raise ValueError("database_url must specify async driver, e.g. mysql+asyncmy://...")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
