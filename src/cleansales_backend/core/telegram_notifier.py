import datetime
import html
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

import pytz
import requests
from pydantic import AnyHttpUrl

from .config import settings
from .event_bus import Event, EventBus

logger = logging.getLogger(__name__)


@dataclass
class LineObject:
    format: Literal["title", "text", "bullet"]
    text: str


class TelegramInitEvent(Enum):
    INIT = "INIT"


class TelegramNotifier:
    """Telegram 通知處理器"""

    _event_bus: EventBus
    _post_url: AnyHttpUrl | None

    def __init__(self, event_bus: EventBus, register_events: list[Enum]) -> None:
        """初始化 Telegram 通知處理器

        Args:
            event_bus (EventBus): 事件總線實例
            register_events (list[Enum]): 要註冊的事件列表
        """
        self._event_bus = event_bus
        self._post_url = None

        # 註冊事件處理器，但根據功能是否啟用決定是否發送通知
        self._register_event_handlers(register_events + [TelegramInitEvent.INIT])

        if not settings.FEATURES_TELEGRAM:
            logger.warning("Telegram notification is disabled in feature flags.")
            return

        try:
            self._post_url = self._configure_post_url()
        except Exception as e:
            logger.error(f"Failed to configure Telegram URL: {str(e)}")
            return

        if not self._post_url:
            logger.warning("Telegram notification is configured but invalid.")
            return

        logger.info("Telegram notification configured successfully.")
        self.hello()

    def hello(self) -> None:
        """發送初始化通知"""
        logger.info("Hello from TelegramNotifier")
        current_time = datetime.datetime.now(tz=pytz.timezone(settings.TIMEZONE))
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        self._event_bus.publish(
            Event(
                event=TelegramInitEvent.INIT,
                message="Telegram notification initialized",
                content={
                    "telegram_message": [
                        LineObject(
                            format="title",
                            text=f"Telegram notification initialized at {formatted_time}",
                        ),
                    ],
                },
            )
        )

    def _configure_post_url(self) -> AnyHttpUrl | None:
        """配置 Telegram 通知 URL

        Returns:
            AnyHttpUrl | None: 配置的URL或None
        """
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            try:
                return AnyHttpUrl(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={settings.TELEGRAM_CHAT_ID}"
                )
            except Exception as e:
                logger.error(f"Invalid URL configuration: {e}")

        return None

    def _register_event_handlers(self, events: list[Enum]) -> None:
        """註冊事件處理器

        Args:
            events (list[Enum]): 要註冊的事件列表
        """
        for event in events:
            self._event_bus.register(event, self.notify)

    def _format_message(self, event: Event) -> str:
        """將事件格式化為消息文本

        Args:
            event (Event): 事件對象

        Returns:
            str: 格式化後的消息文本
        """
        if not isinstance(event.content.get("telegram_message"), list):
            logger.warning("Invalid telegram_message format")
            return ""

        message_objects: list[LineObject] = event.content["telegram_message"]
        message: list[str] = []

        for line in message_objects:
            # 確保所有文本都經過HTML轉義以防止注入
            escaped_text = html.escape(line.text)

            if line.format == "title":
                message.append(f"<b>{escaped_text}</b>")
            elif line.format == "text":
                message.append(f"{'  ' + escaped_text}")
            elif line.format == "bullet":
                message.append(f"{'    - ' + escaped_text}")

        return "\n".join(message)

    def _prepare_payload(self, event: Event) -> dict[str, Any]:
        """準備要發送的資料

        Args:
            event (Event): 事件對象

        Returns:
            Dict[str, Any]: 準備好的資料
        """
        return {
            "text": self._format_message(event),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

    def notify(self, event: Event) -> None:
        """發送 Telegram 通知

        Args:
            event (Event): 要發送的事件
        """
        # 如果Telegram功能被禁用或配置無效，直接返回
        if not settings.FEATURES_TELEGRAM or not self._post_url:
            return

        try:
            payload = self._prepare_payload(event)
            if not payload["text"]:
                logger.warning("Empty message, skipping notification")
                return

            response = self._send_notification(payload)
            self._handle_response(response)

        except requests.Timeout:
            logger.error("Telegram notification timed out")
        except requests.RequestException as e:
            logger.error(f"Telegram request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during Telegram notification: {str(e)}")

    def _send_notification(self, payload: dict[str, Any]) -> requests.Response:
        """發送通知請求，包含重試邏輯

        Args:
            payload (dict[str, Any]): 要發送的資料

        Returns:
            requests.Response: 請求響應
        """
        if not self._post_url:
            logger.error("Telegram notification is not configured.")
            return requests.Response()

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = requests.post(
                    url=self._post_url.unicode_string(),
                    json=payload,
                    timeout=10,
                )
                return response
            except requests.RequestException as e:
                retry_count += 1
                # 使用指數退避策略
                wait_time = 2**retry_count
                logger.warning(
                    f"Telegram request failed (attempt {retry_count}/{max_retries}): {str(e)}. \
                    Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)

        logger.error(
            f"Failed to send Telegram notification after {max_retries} retries."
        )
        return requests.Response()

    def _handle_response(self, response: requests.Response) -> None:
        """處理響應結果

        Args:
            response (requests.Response): 請求響應
        """
        try:
            if not response.ok:
                # 隱藏敏感信息
                response_text = response.text
                if response_text and len(response_text) > 100:
                    response_text = response_text[:100] + "..."

                logger.error(
                    f"Telegram notification failed: {response.status_code} - {response_text}"
                )
            else:
                logger.debug(
                    f"Telegram notification sent successfully: {response.status_code}"
                )
        finally:
            # 確保響應對象被正確關閉
            response.close()
