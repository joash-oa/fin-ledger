from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    debug: bool = False
    cookie_secure: bool = True
    session_idle_timeout_seconds: int
    session_max_lifetime_seconds: int

    model_config = SettingsConfigDict(
        env_file=(".env", Path(__file__).resolve().parents[2] / ".env")
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
