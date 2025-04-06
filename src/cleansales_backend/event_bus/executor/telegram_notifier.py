import html
import logging
import time
from typing import Protocol

import requests
from pydantic import AnyHttpUrl
from rich.console import Console
from rich.logging import RichHandler

from cleansales_backend.event_bus import EventBus
from cleansales_backend.event_bus.events import (
    BroadcastEvent,
    BroadcastEventPayload,
    Head,
    LineObject,
)

logger = logging.getLogger(__name__)
console = Console()

# 使用 rich 的 RichHandler 來美化日誌輸出
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)


class TelegramSettings(Protocol):
    FEATURES_TELEGRAM: bool
    TELEGRAM_BOT_TOKEN: str | None
    TELEGRAM_CHAT_ID: str | None
    TIMEZONE: str


class TelegramNotifier:
    """Telegram 通知處理器"""

    _event_bus: EventBus
    _post_url: AnyHttpUrl
    _settings: TelegramSettings

    def __init__(
        self,
        event_bus: EventBus,
        settings: TelegramSettings,
    ) -> None:
        """初始化 Telegram 通知處理器

        Args:
            event_bus (EventBus): 事件總線實例
            register_events (list[Enum]): 要註冊的事件列表
        """
        self._event_bus = event_bus
        self._settings = settings

        if not settings.FEATURES_TELEGRAM:
            logger.warning("Telegram notification is disabled in feature flags.")
            return

        # 配置 Telegram URL
        if not self._settings.TELEGRAM_BOT_TOKEN or not self._settings.TELEGRAM_CHAT_ID:
            logger.warning("Telegram notification is configured but invalid.")
            return

        self._post_url = self._configure_post_url(
            token=self._settings.TELEGRAM_BOT_TOKEN,
            chat_id=self._settings.TELEGRAM_CHAT_ID,
        )
        # 註冊事件處理器
        self._register_event_handlers()

        logger.info("Telegram notification configured successfully.")

    def _configure_post_url(self, token: str, chat_id: str) -> AnyHttpUrl:
        """配置 Telegram 通知 URL

        Args:
            token (str): 通知 token
            chat_id (str): 通知 chat_id

        Returns:
            AnyHttpUrl: 配置的URL
        """
        if token.strip() == "" or chat_id.strip() == "":
            raise ValueError("Telegram token and chat ID are required.")
        return AnyHttpUrl(
            f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}"
        )

    def _register_event_handlers(self) -> None:
        """註冊事件處理器

        Args:
            events (list[Enum]): 要註冊的事件列表
        """
        self._event_bus.register(BroadcastEvent.SEND_MESSAGE, self.send_message)
        # self._event_bus.register(TelegramEvent.SEND_DOCUMENT, self.send_document)

    def _format_message(self, msg: list[LineObject]) -> str:
        """將事件格式化為消息文本

        Args:
            msg (list[LineObject]): 消息對象

        Returns:
            str: 格式化後的消息文本
        """
        message: list[str] = []

        for line in msg:
            # 確保所有文本都經過HTML轉義以防止注入
            escaped_text = html.escape(line.text)

            if line.head == Head.TITLE:
                message.append(f"<b>{escaped_text}</b>")
            elif line.head == Head.TEXT:
                message.append(f"{'  ' + escaped_text}")
            elif line.head == Head.BULLET:
                message.append(f"{'    - ' + escaped_text}")

        return "\n".join(message)

    def _prepare_payload(self, msg: list[LineObject]) -> dict[str, str | bool]:
        """準備要發送的資料

        Args:
            msg (list[LineObject]): 消息對象

        Returns:
            Dict[str, str|bool]: 準備好的資料
        """
        return {
            "text": self._format_message(msg),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

    def send_message(self, payload: BroadcastEventPayload) -> None:
        """發送 Telegram 通知

        Args:
            payload (BroadcastEventPayload): 要發送的消息
        """
        # 如果Telegram功能被禁用或配置無效，直接返回
        if not self._settings.FEATURES_TELEGRAM or not self._post_url:
            return

        try:
            body = self._prepare_payload(payload.content)
            if not body["text"]:
                logger.warning("Empty message, skipping notification")
                return

            response = self._send_notification(body)
            self._handle_response(response)

        except requests.Timeout:
            logger.error("Telegram notification timed out")
        except requests.RequestException as e:
            logger.error(f"Telegram request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during Telegram notification: {str(e)}")

    def _send_notification(self, payload: dict[str, str | bool]) -> requests.Response:
        """發送通知請求，包含重試邏輯

        Args:
            payload (dict[str, str|bool]): 要發送的資料

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


if __name__ == "__main__":
    from cleansales_backend.core.config import get_settings
    from cleansales_backend.event_bus import get_event_bus

    telegram_notifier = TelegramNotifier(
        event_bus=get_event_bus(),
        settings=get_settings(),
    )
    msg = [
        LineObject(Head.TITLE, text="Telegram notification initialized"),
    ]
    msg.extend(
        [
            LineObject(Head.BULLET, text=f"{k}: {v}")
            for k, v in get_settings().to_dict_safety().items()
        ]
    )

    get_event_bus().publish(
        payload=BroadcastEventPayload(
            event=BroadcastEvent.SEND_MESSAGE,
            content=msg,
        ),
    )
