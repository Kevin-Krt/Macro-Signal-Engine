from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_prefix="APP_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["dev", "prod", "test"] = "dev"
    database_url: PostgresDsn
    redis_url: RedisDsn
    jwt_secret: SecretStr
    fernet_key: SecretStr


@lru_cache
def get_settings() -> Settings:
    return Settings()
