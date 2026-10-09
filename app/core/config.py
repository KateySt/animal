from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import SSLConnection


class AppConfig(BaseSettings):
    APP_NAME: str = "animal-shelter"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class DBConfig(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_ECHO: bool = False
    DB_SSL: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @computed_field
    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def connect_args(self) -> dict[str, str]:
        return {"ssl": "require"} if self.DB_SSL else {}


class AuthConfig(BaseSettings):
    ACCESS_TOKEN_SECRET: str
    ACCESS_TOKEN_TIME_MINUTES: int
    REFRESH_TOKEN_TIME_DAYS: int
    JWT_ALGORITHM: str

    ADMIN_SECRET: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    COOKIE_SECURE: bool = True
    COOKIE_DOMAIN: str | None = None

    CORS_ORIGINS: list[str]

    FRONTEND_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class RedisConfig(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_USER: str
    REDIS_PASSWORD: str
    REDIS_SSL: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def pool_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "username": self.REDIS_USER or None,
            "password": self.REDIS_PASSWORD,
        }
        if self.REDIS_SSL:
            kwargs["connection_class"] = SSLConnection
        return kwargs


class StripeConfig(BaseSettings):
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AnthropicConfig(BaseSettings):
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str
    ANTHROPIC_MAX_TOKEN: int

    ANTHROPIC_TITLE_MAX_TOKEN: int
    ANTHROPIC_SUMMERY_MAX_TOKEN: int

    SUMMARY_EVERY_N: int = 10
    RECENT_WINDOW: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class BlobConfig(BaseSettings):
    BLOB_READ_WRITE_TOKEN: SecretStr
    BLOB_DOCUMENTS_READ_WRITE_TOKEN: SecretStr

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class TestConfig(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int

    model_config = SettingsConfigDict(env_file=".env.test", env_file_encoding="utf-8", extra="ignore")

    @computed_field
    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class ImageConfig(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_IMAGE_MODEL: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class LiveKitConfig(BaseSettings):
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    LIVEKIT_AGENT_NAME: str = "animal-chat-agent"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class BookRagConfig(BaseSettings):
    BOOK_RAG_BASE_URL: str
    INTERNAL_SERVICE_TOKEN: str
    BOOK_RAG_MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024
    BOOK_RAG_MAX_DOCUMENTS_PER_SESSION: int = 5
    BOOK_RAG_REQUEST_TIMEOUT_SECONDS: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AgentConfig(BaseSettings):
    AGENT_SERVICE_TOKEN: str = Field(min_length=32)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_image_config() -> ImageConfig:
    return ImageConfig()


@lru_cache
def get_livekit_config() -> LiveKitConfig:
    return LiveKitConfig()


@lru_cache
def get_blob_config() -> BlobConfig:
    return BlobConfig()


@lru_cache
def get_anthropic_config() -> AnthropicConfig:
    return AnthropicConfig()


@lru_cache
def get_db_config() -> DBConfig:
    return DBConfig()


@lru_cache
def get_test_config() -> TestConfig:
    return TestConfig()


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


@lru_cache
def get_book_rag_config() -> BookRagConfig:
    return BookRagConfig()


@lru_cache
def get_agent_config() -> AgentConfig:
    return AgentConfig()
