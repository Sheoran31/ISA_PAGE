"""
Message Formatter: Format alerts into readable Telegram messages.
Handles different alert types with rich formatting.
"""

from typing import Dict, Any
from datetime import datetime

from utils.logger import logger


class MessageFormatter:
    """
    Format alert conditions into readable Telegram messages.
    """

    @staticmethod
    def format_alert(
        alert_id: str,
        alert_name: str,
        condition_type: str,
        symbol: str,
        price_data: Dict[str, Any]
    ) -> str:
        """
        Format alert based on condition type.

        Args:
            alert_id: Alert ID
            alert_name: Alert name
            condition_type: Type of condition (price_above, ema_consolidation, etc.)
            symbol: Stock symbol
            price_data: Current price data dict

        Returns:
            Formatted Telegram message
        """
        try:
            if condition_type == 'price_above':
                return MessageFormatter._format_price_above(alert_name, symbol, price_data)
            elif condition_type == 'price_below':
                return MessageFormatter._format_price_below(alert_name, symbol, price_data)
            elif condition_type == 'ema_consolidation':
                return MessageFormatter._format_ema_breakout(alert_name, symbol, price_data)
            elif condition_type == 'ema_breakdown':
                return MessageFormatter._format_ema_breakdown(alert_name, symbol, price_data)
            elif condition_type == 'ema_smart_breakout':
                return MessageFormatter._format_ema_smart(alert_name, symbol, price_data)
            elif condition_type == 'percent_change':
                return MessageFormatter._format_percent_change(alert_name, symbol, price_data)
            elif condition_type == 'volume_spike':
                return MessageFormatter._format_volume_spike(alert_name, symbol, price_data)
            else:
                return MessageFormatter._format_generic(alert_name, symbol, price_data)
        except Exception as e:
            logger.error(f"Failed to format message: {e}")
            return f"⚠️ {alert_name}\nAlert triggered for {symbol}"

    @staticmethod
    def _format_price_above(name: str, symbol: str, data: Dict) -> str:
        """Format price_above alert."""
        current = data.get('ltp') or data.get('close', 0)
        return (
            f"📈 {name}\n"
            f"\n{symbol}\n"
            f"Current: ₹{current:.2f}\n"
            f"Time: {datetime.now().strftime('%H:%M IST')}"
        )

    @staticmethod
    def _format_price_below(name: str, symbol: str, data: Dict) -> str:
        """Format price_below alert."""
        current = data.get('ltp') or data.get('close', 0)
        return (
            f"📉 {name}\n"
            f"\n{symbol}\n"
            f"Current: ₹{current:.2f}\n"
            f"Time: {datetime.now().strftime('%H:%M IST')}"
        )

    @staticmethod
    def _format_ema_breakout(name: str, symbol: str, data: Dict) -> str:
        """Format EMA consolidation breakout alert."""
        try:
            current_close = data.get('ltp') or data.get('close', 0)
            ema_info = data.get('ema_breakout', {})

            if not ema_info:
                return f"📊 {name}\n{symbol}\nClose: ₹{current_close:.2f}"

            crossed_emas = ema_info.get('crossed_emas', [])
            today_emas = ema_info.get('today_emas', {})
            consolidation_days = ema_info.get('consolidation_days', 0)
            range_high, range_low = ema_info.get('consolidation_range', (None, None))

            # Build message
            msg = f"🚀 {name}\n\n"
            msg += f"Stock: {symbol}\n"
            msg += f"Close: ₹{current_close:.2f}\n"
            msg += f"Time: {datetime.now().strftime('%H:%M IST')}\n"

            # Breakout info
            if crossed_emas:
                msg += f"\n🎯 Breakout Details:\n"
                crossed_text = ", ".join([f"EMA{e}" for e in sorted(crossed_emas)])
                msg += f"Crossed: {crossed_text}\n"

            # Consolidation info
            if consolidation_days > 0:
                msg += f"\n📈 Consolidation:\n"
                msg += f"Duration: {consolidation_days} days\n"
                if range_high and range_low:
                    msg += f"Range: ₹{range_low:.2f} - ₹{range_high:.2f}\n"
                    range_pct = ((range_high - range_low) / range_low) * 100
                    msg += f"Tight: {range_pct:.2f}%\n"

            # EMA values
            if today_emas:
                msg += f"\n📊 EMA Values:\n"
                for period in sorted(today_emas.keys()):
                    ema_val = today_emas[period]
                    if ema_val:
                        diff = current_close - ema_val
                        diff_pct = (diff / ema_val) * 100
                        status = "✓" if period in crossed_emas else "✗"
                        msg += f"EMA{period}: ₹{ema_val:.2f} {status} ({diff_pct:+.2f}%)\n"

            return msg
        except Exception as e:
            logger.error(f"Error formatting EMA message: {e}")
            return f"📊 {name}\n{symbol}"

    @staticmethod
    def _format_percent_change(name: str, symbol: str, data: Dict) -> str:
        """Format percent_change alert."""
        current = data.get('ltp') or data.get('close', 0)
        open_price = data.get('open', 0)

        if open_price:
            pct = ((current - open_price) / open_price) * 100
            emoji = "📈" if pct >= 0 else "📉"
            return (
                f"{emoji} {name}\n\n"
                f"{symbol}\n"
                f"Change: {pct:+.2f}%\n"
                f"Current: ₹{current:.2f}\n"
                f"Open: ₹{open_price:.2f}\n"
                f"Time: {datetime.now().strftime('%H:%M IST')}"
            )
        else:
            return f"{name}\n{symbol}\nCurrent: ₹{current:.2f}"

    @staticmethod
    def _format_volume_spike(name: str, symbol: str, data: Dict) -> str:
        """Format volume_spike alert."""
        current = data.get('ltp') or data.get('close', 0)
        volume = data.get('volume', 0)
        return (
            f"📊 {name}\n\n"
            f"{symbol}\n"
            f"Volume: {volume:,.0f}\n"
            f"Price: ₹{current:.2f}\n"
            f"Time: {datetime.now().strftime('%H:%M IST')}"
        )

    @staticmethod
    def _format_ema_breakdown(name: str, symbol: str, data: Dict) -> str:
        """Format EMA breakdown alert."""
        try:
            current_close = data.get('ltp') or data.get('close', 0)
            ema_info = data.get('ema_breakdown', {})

            if not ema_info:
                return f"📊 {name}\n{symbol}\nClose: ₹{current_close:.2f}"

            lowest_ema = ema_info.get('lowest_ema', 0)
            today_emas = ema_info.get('today_emas', {})
            consolidation_days = ema_info.get('consolidation_days', 0)
            range_high, range_low = ema_info.get('consolidation_range', (None, None))

            # Build message
            msg = f"🔴 BREAKDOWN! {name}\n\n"
            msg += f"Stock: {symbol}\n"
            msg += f"Close: ₹{current_close:.2f}\n"
            msg += f"Time: {datetime.now().strftime('%H:%M IST')}\n"

            # Breakdown info
            msg += f"\n⚠️ SELL Signal:\n"
            msg += f"Price CLOSED BELOW all EMAs\n"
            msg += f"Lowest EMA: ₹{lowest_ema:.2f}\n"

            # Consolidation info
            if consolidation_days > 0:
                msg += f"\n📈 Prior Consolidation:\n"
                msg += f"Duration: {consolidation_days} days\n"
                if range_high and range_low:
                    msg += f"Range: ₹{range_low:.2f} - ₹{range_high:.2f}\n"

            # EMA values
            if today_emas:
                msg += f"\n📊 EMA Values:\n"
                for period in sorted(today_emas.keys()):
                    ema_val = today_emas[period]
                    if ema_val:
                        diff = current_close - ema_val
                        diff_pct = (diff / ema_val) * 100
                        msg += f"EMA{period}: ₹{ema_val:.2f} ({diff_pct:+.2f}%)\n"

            return msg
        except Exception as e:
            logger.error(f"Error formatting breakdown message: {e}")
            return f"🔴 {name}\n{symbol}"

    @staticmethod
    def _format_ema_smart(name: str, symbol: str, data: Dict) -> str:
        """Format Smart EMA breakout/breakdown alert."""
        try:
            current_close = data.get('ltp') or data.get('close', 0)
            signal_info = data.get('ema_signal', {})

            if not signal_info:
                return f"📊 {name}\n{symbol}\nClose: ₹{current_close:.2f}"

            signal_type = signal_info.get('signal_type', 'SIGNAL')
            is_breakout = signal_info.get('is_breakout', False)
            is_breakdown = signal_info.get('is_breakdown', False)
            ema_spread_percent = signal_info.get('ema_spread_percent', 0)
            ema_high = signal_info.get('ema_high', 0)
            ema_low = signal_info.get('ema_low', 0)
            today_emas = signal_info.get('today_emas', {})

            # Choose emoji and action based on signal type
            if is_breakout:
                emoji = "🟢"
                action = "BUY ⬆️"
            else:
                emoji = "🔴"
                action = "SELL ⬇️"

            # Build message
            msg = f"{emoji} {signal_type}\n\n"
            msg += f"Stock: {symbol}\n"
            msg += f"Action: {action}\n"
            msg += f"Close: ₹{current_close:.2f}\n"
            msg += f"Time: {datetime.now().strftime('%H:%M IST')}\n"

            # EMA consolidation info
            msg += f"\n📊 EMA Status:\n"
            msg += f"Spread: {ema_spread_percent:.2f}% (TIGHT)\n"
            msg += f"Range: ₹{ema_low:.2f} - ₹{ema_high:.2f}\n"

            # EMA values
            if today_emas:
                msg += f"\n📈 EMA Values:\n"
                for period in sorted(today_emas.keys()):
                    ema_val = today_emas[period]
                    if ema_val:
                        diff = current_close - ema_val
                        diff_pct = (diff / ema_val) * 100
                        msg += f"EMA{period}: ₹{ema_val:.2f} ({diff_pct:+.2f}%)\n"

            return msg
        except Exception as e:
            logger.error(f"Error formatting smart signal message: {e}")
            return f"📊 {name}\n{symbol}"

    @staticmethod
    def _format_generic(name: str, symbol: str, data: Dict) -> str:
        """Format generic alert."""
        current = data.get('ltp') or data.get('close', 0)
        return (
            f"🔔 {name}\n\n"
            f"{symbol}\n"
            f"Price: ₹{current:.2f}\n"
            f"Time: {datetime.now().strftime('%H:%M IST')}"
        )

    @staticmethod
    def format_status_message(stats: Dict[str, Any]) -> str:
        """
        Format system status message for /status command.

        Args:
            stats: Stats dict with engine info

        Returns:
            Formatted status message
        """
        msg = "📊 System Status\n"
        msg += "━" * 30 + "\n\n"

        msg += f"Engine: {stats.get('engine_status', 'Unknown')}\n"
        msg += f"Last Check: {stats.get('last_check_time', 'Never')}\n"
        msg += f"Next Check: {stats.get('next_check_time', 'Unknown')}\n"
        msg += f"Market: {stats.get('market_status', 'Unknown')}\n\n"

        msg += f"Today's Stats:\n"
        msg += f"Alerts Fired: {stats.get('alerts_fired_today', 0)}\n"
        msg += f"Symbols Watched: {stats.get('symbols_watched', 0)}\n"
        msg += f"Conditions Active: {stats.get('conditions_active', 0)}\n\n"

        msg += f"Connections:\n"
        msg += f"Zerodha: {stats.get('zerodha_status', 'Unknown')}\n"
        msg += f"Telegram: {stats.get('telegram_status', 'Unknown')}\n"

        return msg
