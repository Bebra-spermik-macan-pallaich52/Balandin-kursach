from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Пароль и адрес задаются через .env; пример предназначен только для локальной разработки.
    database_url: str = "postgresql+psycopg://coursework:coursework_local@localhost:5432/coursework"

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if make_url(value).drivername != "postgresql+psycopg":
            raise ValueError("Используйте PostgreSQL и драйвер psycopg: postgresql+psycopg://...")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
