from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

    FRONTEND_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class RedisConfig(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_USER: str
    REDIS_PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


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


class MinioConfig(BaseSettings):
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str
    MINIO_HOST: str
    MINIO_REGION: str
    MINIO_SECURE: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @computed_field
    @property
    def bucket_url(self) -> str:
        scheme = "https" if self.MINIO_SECURE else "http"
        return f"{scheme}://{self.MINIO_HOST}/{self.MINIO_BUCKET_NAME}/"


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


class SpeechConfig(BaseSettings):
    DEEPGRAM_API_KEY: str
    DEEPGRAM_MODEL: str = "nova-2"
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str
    ELEVENLABS_MODEL: str = "eleven_multilingual_v2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


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


class ExaConfig(BaseSettings):
    EXA_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_exa_config() -> ExaConfig:
    return ExaConfig()


@lru_cache
def get_image_config() -> ImageConfig:
    return ImageConfig()


@lru_cache
def get_livekit_config() -> LiveKitConfig:
    return LiveKitConfig()


@lru_cache
def get_speech_config() -> SpeechConfig:
    return SpeechConfig()


@lru_cache
def get_minio_config() -> MinioConfig:
    return MinioConfig()


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
