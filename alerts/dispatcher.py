"""
Alert Dispatcher: Send alerts to multiple channels (Telegram, Zerodha, etc.)
Supports both traditional alerts and order-based alerts.
"""

from typing import Dict, Any, Optional
from config.settings import ZERODHA_ENABLED
from alerts.telegram_sender import get_telegram_sender
from utils.logger import logger

# Import Zerodha sender only if available
try:
    from alerts.zerodha_sender import get_zerodha_sender
    ZERODHA_AVAILABLE = True
except ImportError:
    ZERODHA_AVAILABLE = False


class AlertDispatcher:
    """Dispatch alerts to multiple channels (Telegram, Zerodha, etc.)"""

    def __init__(self):
        """Initialize alert dispatcher"""
        self.telegram_sender = get_telegram_sender()
        self.zerodha_sender = None
        self.zerodha_enabled = ZERODHA_ENABLED and ZERODHA_AVAILABLE

        if self.zerodha_enabled:
            try:
                self.zerodha_sender = get_zerodha_sender()
                logger.info("✅ Zerodha alerts enabled")
            except Exception as e:
                logger.warning(f"⚠️ Zerodha initialization failed: {e} - Telegram-only mode")
                self.zerodha_enabled = False
        else:
            logger.info("ℹ️ Zerodha alerts disabled (ZERODHA_ENABLED=false)")

    def send_alert(self, message: str) -> bool:
        """
        Send alert to all enabled channels

        Args:
            message: Alert message to send

        Returns:
            True if at least Telegram was successful
        """
        try:
            # Always send to Telegram (primary channel)
            telegram_ok = self.telegram_sender.send_alert(message)

            if not telegram_ok:
                logger.error("❌ Failed to send Telegram alert")
                return False

            # Optionally send to Zerodha
            if self.zerodha_enabled and self.zerodha_sender:
                try:
                    logger.info("📲 Attempting to send to Zerodha...")
                    # Note: Zerodha alerts are order-based, not message-based
                    # This is a placeholder for future integration
                    logger.info("✓ Zerodha notification logged")
                except Exception as e:
                    logger.warning(f"⚠️ Zerodha send failed: {e}")
                    # Don't fail the whole alert if Zerodha fails

            return True

        except Exception as e:
            logger.error(f"Alert dispatch failed: {e}")
            return False

    def send_breakout_alert(self, symbol: str, price: float, ema_high: float,
                           ema_low: float, spread_pct: float) -> Dict[str, Any]:
        """
        Send breakout alert to Zerodha (if enabled)

        Args:
            symbol: Stock symbol
            price: Current price
            ema_high: Highest EMA
            ema_low: Lowest EMA
            spread_pct: EMA spread percentage

        Returns:
            Alert result with order_id for confirmation
        """
        if not self.zerodha_enabled or not self.zerodha_sender:
            return {
                'status': 'skipped',
                'reason': 'Zerodha alerts not enabled'
            }

        try:
            return self.zerodha_sender.send_breakout_alert(
                symbol=symbol,
                price=price,
                ema_high=ema_high,
                ema_low=ema_low,
                spread_pct=spread_pct
            )
        except Exception as e:
            logger.error(f"Failed to send Zerodha breakout alert: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def send_breakdown_alert(self, symbol: str, price: float, ema_high: float,
                            ema_low: float, spread_pct: float) -> Dict[str, Any]:
        """
        Send breakdown alert to Zerodha (if enabled)

        Args:
            symbol: Stock symbol
            price: Current price
            ema_high: Highest EMA
            ema_low: Lowest EMA
            spread_pct: EMA spread percentage

        Returns:
            Alert result with order_id for confirmation
        """
        if not self.zerodha_enabled or not self.zerodha_sender:
            return {
                'status': 'skipped',
                'reason': 'Zerodha alerts not enabled'
            }

        try:
            return self.zerodha_sender.send_breakdown_alert(
                symbol=symbol,
                price=price,
                ema_high=ema_high,
                ema_low=ema_low,
                spread_pct=spread_pct
            )
        except Exception as e:
            logger.error(f"Failed to send Zerodha breakdown alert: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def get_pending_orders(self) -> Dict:
        """Get all pending Zerodha orders"""
        if not self.zerodha_enabled or not self.zerodha_sender:
            return {}
        return self.zerodha_sender.get_pending_orders()

    def confirm_order(self, order_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Confirm and execute a pending Zerodha order"""
        if not self.zerodha_enabled or not self.zerodha_sender:
            return {'status': 'failed', 'error': 'Zerodha not enabled'}
        return self.zerodha_sender.confirm_and_execute(order_id, quantity)

    def reject_order(self, order_id: str) -> Dict[str, Any]:
        """Reject a pending Zerodha order"""
        if not self.zerodha_enabled or not self.zerodha_sender:
            return {'status': 'failed', 'error': 'Zerodha not enabled'}
        return self.zerodha_sender.reject_order(order_id)


# Global instance
_dispatcher_instance = None


def get_alert_dispatcher() -> AlertDispatcher:
    """Get or create global AlertDispatcher instance"""
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = AlertDispatcher()
    return _dispatcher_instance
