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

from functools import lru_cache
from pathlib import Path
from typing import ClassVar, override

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """應用程序設置模型"""
    
    BRANCH: str

    # 數據庫配置
    DB_PATH: Path = Field(default_factory=lambda: ROOT_DIR / "data" / "main.db")
    DB_ECHO: bool = Field(default=False)

    # API 服務配置
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_RELOAD: bool = Field(default=True)

    # 上傳文件配置
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB TODO: 取消
    ALLOWED_EXTENSIONS: set[str] = Field(default={".xlsx", ".xls"})  # TODO: 取消

    # 日誌配置
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Telegram 通知配置
    TELEGRAM_BOT_TOKEN: str | None = Field(default=None)
    TELEGRAM_CHAT_ID: str | None = Field(default=None)
    CUSTOM_TELEGRAM_WEBHOOK_URL: AnyHttpUrl | None = Field(default=None)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env-testing"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @override
    def model_post_init(self, __: None) -> None:
        """模型初始化後的處理

        在這裡處理目錄創建和 Telegram 配置
        """
        # 確保必要的目錄存在
        self.DB_PATH.parent.mkdir(exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """獲取設置實例（使用緩存）

    Returns:
        Settings: 設置實例
    """
    return Settings()


settings: Settings = get_settings()
