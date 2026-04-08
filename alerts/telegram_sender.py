"""
Telegram Sender: Send formatted alerts to Telegram chat.
Handles retries, rate limiting, and error handling.
"""

from typing import List, Optional
import time
import requests

from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_EXTRA_CHAT_IDS
from utils.logger import logger
from utils.exceptions import TelegramSendError


class TelegramSender:
    """
    Send alerts to Telegram using Telegram Bot API.
    """

    # Telegram API
    TELEGRAM_API_URL = "https://api.telegram.org/bot"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(self):
        """Initialize Telegram bot."""
        if not TELEGRAM_BOT_TOKEN:
            raise TelegramSendError("TELEGRAM_BOT_TOKEN not configured in .env")

        if not TELEGRAM_CHAT_ID:
            raise TelegramSendError("TELEGRAM_CHAT_ID not configured in .env")

        self.token = TELEGRAM_BOT_TOKEN
        self.primary_chat_id = int(TELEGRAM_CHAT_ID)

        # Parse extra chat IDs
        self.extra_chat_ids = []
        if TELEGRAM_EXTRA_CHAT_IDS:
            try:
                self.extra_chat_ids = [int(cid.strip()) for cid in TELEGRAM_EXTRA_CHAT_IDS.split(',')]
            except ValueError:
                logger.warning("Invalid TELEGRAM_EXTRA_CHAT_IDS format")

        logger.info(f"TelegramSender initialized (primary: {self.primary_chat_id})")

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
            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
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
                        if attempt < self.MAX_RETRIES:
                            logger.warning(f"Telegram send failed (attempt {attempt}/{self.MAX_RETRIES}): {error_msg}")
                            time.sleep(self.RETRY_DELAY)
                        else:
                            raise Exception(f"Telegram API error: {error_msg}")

                except requests.exceptions.Timeout:
                    if attempt < self.MAX_RETRIES:
                        logger.warning(f"Telegram timeout (attempt {attempt}/{self.MAX_RETRIES})")
                        time.sleep(self.RETRY_DELAY)
                    else:
                        raise

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

        Note: Full connection test requires async context.
        Here we just verify the bot token is set.

        Returns:
            True if bot is configured
        """
        try:
            if not self.bot.token:
                logger.error("Telegram bot token is not configured")
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
