from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    APP_NAME: str = "animal-shelter"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class DBConfig(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_ECHO: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @computed_field
    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class AuthConfig(BaseSettings):
    ACCESS_TOKEN_SECRET: str
    ACCESS_TOKEN_TIME_MINUTES: int
    REFRESH_TOKEN_TIME_DAYS: int
    JWT_ALGORITHM: str

    ADMIN_SECRET: str

    SUPERUSER_EMAIL: str
    SUPERUSER_PASSWORD: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    COOKIE_SECURE: bool = True
    COOKIE_DOMAIN: str | None = None

    CORS_ORIGINS: list[str]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class RedisConfig(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_USER: str
    REDIS_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class StripeConfig(BaseSettings):
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_db_config() -> DBConfig:
    return DBConfig()


@lru_cache
def get_app_config() -> AppConfig:
    return AppConfig()


@lru_cache
def get_auth_config() -> AuthConfig:
    return AuthConfig()


@lru_cache
def get_redis_config() -> RedisConfig:
    return RedisConfig()


@lru_cache
def get_stripe_config() -> StripeConfig:
    return StripeConfig()
