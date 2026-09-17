from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_prefix="APP_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["dev", "prod", "test"] = "dev"
    database_url: PostgresDsn
    test_database_url: PostgresDsn | None = None
    redis_url: RedisDsn
    jwt_secret: SecretStr
    fernet_key: SecretStr
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"
    log_sql: bool = False
    finnhub_api_key: SecretStr


@lru_cache
def get_settings() -> Settings:
    return Settings()
