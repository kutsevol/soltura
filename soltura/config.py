from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class DatabaseSettings(BaseConfig):
    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5433/soltura",
        description="Async SQLAlchemy URL of the Postgres database",
    )


class LLMSettings(BaseConfig):
    model_config = SettingsConfigDict(env_prefix="LLM_")

    model: str = Field(
        default="claude-sonnet-5-5",
        description="Claude model used for text generation, glosses and answer judging",
    )
    # The SDK's own variable name. pydantic-settings reads .env into these models
    # without exporting it to the process environment, so the key is passed to the
    # client explicitly rather than left for the SDK to find.
    api_key: SecretStr | None = Field(
        default=None,
        validation_alias="ANTHROPIC_API_KEY",
        description="Anthropic API key; unset means LLM features are unavailable",
    )


class SrsSettings(BaseConfig):
    model_config = SettingsConfigDict(env_prefix="SRS_")

    desired_retention: float = Field(
        default=0.9,
        gt=0,
        lt=1,
        description="Target probability of recall that FSRS schedules reviews for",
    )


class AuthSettings(BaseConfig):
    model_config = SettingsConfigDict(env_prefix="AUTH_")

    dev_telegram_user_id: int | None = Field(
        default=None,
        description="Telegram user id to act as when no Telegram login is present; unset disables dev login",
    )


class LoggingSettings(BaseConfig):
    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Level of the application's own loggers",
    )


class Settings(BaseConfig):
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="Database connection settings",
    )
    llm: LLMSettings = Field(
        default_factory=LLMSettings,
        description="LLM provider settings",
    )
    srs: SrsSettings = Field(
        default_factory=SrsSettings,
        description="Spaced repetition settings",
    )
    auth: AuthSettings = Field(
        default_factory=AuthSettings,
        description="Learner login settings",
    )
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description="Logging settings",
    )


settings = Settings()
