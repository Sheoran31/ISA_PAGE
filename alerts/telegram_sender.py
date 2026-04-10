"""
Telegram Sender: Send formatted alerts to Telegram chat.
Handles retries, rate limiting, and error handling.
"""

from typing import List, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging

from utils.logger import logger
from utils.exceptions import TelegramSendError
import os
from dotenv import load_dotenv
from pathlib import Path


class TelegramSender:
    """
    Send alerts to Telegram using Telegram Bot API.
    """

    # Telegram API
    TELEGRAM_API_URL = "https://api.telegram.org/bot"

    def __init__(self):
        """Initialize Telegram bot."""
        # Load fresh from .env file
        env_file = Path(__file__).parent.parent / '.env'
        load_dotenv(env_file, override=True)

        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not token:
            raise TelegramSendError("TELEGRAM_BOT_TOKEN not configured in .env")

        if not chat_id:
            raise TelegramSendError("TELEGRAM_CHAT_ID not configured in .env")

        self.token = token
        self.primary_chat_id = int(chat_id)

        # Parse extra chat IDs
        self.extra_chat_ids = []
        extra_ids = os.getenv('TELEGRAM_EXTRA_CHAT_IDS', '')
        if extra_ids:
            try:
                self.extra_chat_ids = [int(cid.strip()) for cid in extra_ids.split(',')]
            except ValueError:
                logger.warning("Invalid TELEGRAM_EXTRA_CHAT_IDS format")

        logger.info(f"TelegramSender initialized (primary: {self.primary_chat_id})")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=False
    )
    def _send_to_chat(self, message: str, chat_id: int) -> bool:
        """
        Internal method to send message to a chat (with retry logic).

        Args:
            message: Message text
            chat_id: Telegram chat ID

        Returns:
            True if sent successfully
        """
        url = f"{self.TELEGRAM_API_URL}{self.token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info(f"Alert sent to Telegram (chat_id: {chat_id})")
            return True
        else:
            error_msg = response.text
            raise Exception(f"Telegram API error: {error_msg}")

    def send_alert(self, message: str, chat_id: Optional[int] = None) -> bool:
        """
        Send alert message to Telegram chat.

        Args:
            message: Alert message text
            chat_id: Override default chat ID (optional)

        Returns:
            True if sent successfully
        """
        chat_id = chat_id or self.primary_chat_id

        try:
            return self._send_to_chat(message, chat_id)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def send_to_all_chats(self, message: str) -> int:
        """
        Send message to all configured chat IDs.

        Args:
            message: Alert message

        Returns:
            Number of successful sends
        """
        sent_count = 0

        # Send to primary chat
        if self.send_alert(message, self.primary_chat_id):
            sent_count += 1

        # Send to extra chats
        for chat_id in self.extra_chat_ids:
            if self.send_alert(message, chat_id):
                sent_count += 1

        return sent_count

    def send_status(self, message: str) -> bool:
        """
        Send status message (like /status response).

        Args:
            message: Status message

        Returns:
            True if sent
        """
        return self.send_alert(message)

    def test_connection(self) -> bool:
        """
        Test if bot is configured properly.

        Returns:
            True if bot is configured
        """
        try:
            if not self.token or not self.primary_chat_id:
                logger.error("Telegram credentials not configured")
                return False
            logger.info("✓ Telegram bot configured")
            return True
        except Exception as e:
            logger.error(f"Failed to configure Telegram: {e}")
            return False

    def send_startup_message(self) -> bool:
        """
        Send startup notification.

        Returns:
            True if sent
        """
        message = (
            "✅ Stock Alert System Started\n\n"
            "🚀 EMA Consolidation Breakout Alerts\n"
            "📊 Real-time Price Monitoring\n"
            "⏰ Running 9:15 AM - 3:30 PM IST (Weekdays)\n\n"
            "Available Commands:\n"
            "/status - System status\n"
            "/add_alert - Add new alert\n"
            "/list_alerts - Show all alerts\n"
            "/delete_alert - Remove alert"
        )
        return self.send_alert(message)

    def send_error_message(self, error_title: str, error_details: str) -> bool:
        """
        Send error notification.

        Args:
            error_title: Title of error
            error_details: Error description

        Returns:
            True if sent
        """
        message = (
            f"⚠️ Error: {error_title}\n\n"
            f"{error_details}\n\n"
            f"Time: {logger._get_timestamp()}"
        )
        return self.send_alert(message)

    def is_ready(self) -> bool:
        """Check if Telegram sender is ready."""
        return self.test_connection()


# Global instance
_telegram_sender_instance = None


def get_telegram_sender() -> TelegramSender:
    """Get or create global TelegramSender instance."""
    global _telegram_sender_instance
    if _telegram_sender_instance is None:
        _telegram_sender_instance = TelegramSender()
    return _telegram_sender_instance
