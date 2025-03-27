import logging
from enum import Enum

import requests
from pydantic import AnyHttpUrl

from .config import settings
from .event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram 通知處理器"""

    _event_bus: EventBus | None = None
    post_url: AnyHttpUrl | None = None

    def __init__(self, event_bus: EventBus, register_events: list[Enum]) -> None:
        """初始化 Telegram 通知處理器

        Args:
            event_bus (EventBus): 事件總線實例
            register_events (list[Enum]): 要註冊的事件列表
        """

        self._event_bus = event_bus

        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            self.post_url = AnyHttpUrl(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={settings.TELEGRAM_CHAT_ID}"
            )
        if not self.post_url and settings.CUSTOM_TELEGRAM_WEBHOOK_URL:
            self.post_url = AnyHttpUrl(settings.CUSTOM_TELEGRAM_WEBHOOK_URL)

        # 只有在配置了 Telegram 時才註冊事件處理器
        if self.post_url:
            for event in register_events:
                self._event_bus.register(event, self.notify)
            logger.info("Telegram notification is configured.")
        else:
            logger.warning("Telegram notification is not configured.")

    def notify(self, event: Event) -> None:
        """發送 Telegram 通知

        Args:
            event (Event): 要發送的事件
        """
        try:
            if not self.post_url:
                return

            # 將事件內容轉換為格式化的文字訊息
            message = f"事件: {event.event.value}\n"
            message += f"\n訊息: {event.message}\n"
            message += "\n內容:\n"
            for key, value in event.content.items():
                message += f"- {key}: {value}\n"
            # message += f"\n時間: {event.content['timestamp']}"

            # 準備 Telegram API 所需的資料
            payload = {
                "text": message,
                "parse_mode": "HTML",  # 支援基本 HTML 格式
                "disable_web_page_preview": True,  # 避免預覽可能的連結
            }

            # 如果是自訂 webhook，直接發送原始內容
            if settings.CUSTOM_TELEGRAM_WEBHOOK_URL:
                payload = event.content

            response = requests.post(
                url=self.post_url.unicode_string(),
                json=payload,
                timeout=10,  # 添加超時設定
            )

            if not response.ok:
                logger.error(
                    f"Telegram 通知發送失敗: {response.status_code} - {response.text}"
                )
            else:
                logger.debug(f"Telegram 通知發送成功: {response.status_code}")

        except requests.Timeout:
            logger.error("Telegram 通知發送超時")
        except requests.RequestException as e:
            logger.error(f"Telegram 通知發送請求錯誤: {str(e)}")
        except Exception as e:
            logger.error(f"Telegram 通知發送時發生未預期的錯誤: {str(e)}")
