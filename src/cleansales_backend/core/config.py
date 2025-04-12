"""
################################################################################
# 核心配置模組
#
# 這個模組提供了核心功能的配置，包括：
# 1. 數據庫配置
# 2. 事件總線配置
# 3. 通知配置
#
# 主要功能：
# - 配置驗證
# - 環境變量處理
# - 默認值設置
################################################################################
"""

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, Literal, override

import pytz
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """應用程序設置模型"""

    # ENV_FILE: str = Field(default=ENV_FILE)

    TIMEZONE: str = Field(default="Asia/Taipei")
    NOW: str = Field(
        default_factory=lambda: datetime.now(tz=pytz.timezone("Asia/Taipei")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    BRANCH: str = Field(default="unset in env")
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    # 數據庫配置
    DB: Literal["sqlite", "supabase", "supabase_pooler"] = Field(default="sqlite")
    DB_ECHO: bool = Field(default=False)
    SQLITE_DB_PATH: Path = Field(default_factory=lambda: ROOT_DIR / "data" / "main.db")

    # supabase
    # FEATURES_SUPABASE: bool = Field(default=False)
    SUPABASE_DB_HOST: str = Field(default="")
    SUPABASE_DB_PASSWORD: str = Field(default="")
    SUPABASE_DB_USER: str = Field(default="")
    SUPABASE_DB_PORT: int = Field(default=5432)
    SUPABASE_DB_NAME: str = Field(default="")
    # supabase pooler
    SUPABASE_POOLER_TENANT_ID: str = Field(default="")

    # supabase production
    SUPABASE_PRODUCTION_URL: str = Field(default="")

    # supabase client
    SUPABASE_CLIENT_URL: str = Field(default="")
    SUPABASE_ANON_KEY: str = Field(default="")

    # 日誌配置
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 功能開關配置
    FEATURES_RAW_DATA_API: bool = Field(default=True)  # 是否啟用原始數據API

    # Telegram 通知配置
    FEATURES_TELEGRAM: bool = Field(default=False)
    TELEGRAM_BOT_TOKEN: str | None = Field(default=None)
    TELEGRAM_CHAT_ID: str | None = Field(default=None)

    # Todoist 配置
    TODOIST_API_TOKEN: str | None = Field(default=None)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @override
    def model_post_init(self, _: None) -> None:
        """模型初始化後的處理

        在這裡處理目錄創建和 Telegram 配置
        """
        # 確保必要的目錄存在
        self.SQLITE_DB_PATH.parent.mkdir(exist_ok=True)

    def to_dict_safety(self) -> dict[str, str | None | bool]:
        db_path = None
        if self.DB == "sqlite":
            db_path = str(self.SQLITE_DB_PATH)
        elif self.DB == "supabase":
            db_path = f"{self.SUPABASE_DB_USER}@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}"
        elif self.DB == "supabase_pooler":
            db_path = f"{self.SUPABASE_DB_USER}.{self.SUPABASE_POOLER_TENANT_ID}@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}"
        return {
            "BRANCH": self.BRANCH,
            "DB": self.DB,
            "DB_PATH": db_path,
            "LOG_LEVEL": self.LOG_LEVEL,
            "FEATURES_RAW_DATA_API": self.FEATURES_RAW_DATA_API,
            "FEATURES_TELEGRAM": self.FEATURES_TELEGRAM,
            "NOW": self.NOW,
        }


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()


if __name__ == "__main__":
    print(Settings().model_dump_json())
