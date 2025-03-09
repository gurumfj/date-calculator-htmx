from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """設定"""

    DB_PATH: str = Field(default="data/main.db")
    TELEGRAM_WEBHOOK_URL: str

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
