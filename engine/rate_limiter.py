"""
Rate Limiter: Prevents alert spam by limiting alerts per cycle and per symbol per day.
Enforces MAX_ALERTS_PER_CYCLE and MAX_ALERTS_PER_SYMBOL_PER_DAY settings.
"""

from datetime import datetime
from typing import Dict

from utils.logger import logger


class RateLimiter:
    """
    Rate limiter for alerts.

    Two limits:
    1. Per cycle: max N alerts per check cycle
    2. Per symbol per day: max M alerts per symbol per calendar day
    """

    def __init__(self, max_per_cycle: int = 10, max_per_symbol_per_day: int = 5):
        """
        Initialize rate limiter.

        Args:
            max_per_cycle: Maximum alerts allowed in one check cycle
            max_per_symbol_per_day: Maximum alerts per symbol per calendar day
        """
        self.max_per_cycle = max_per_cycle
        self.max_per_symbol_per_day = max_per_symbol_per_day

        self._cycle_count: int = 0
        self._symbol_daily: Dict[str, int] = {}
        self._day_key: str = ""

        logger.info(f"RateLimiter initialized: max {max_per_cycle}/cycle, {max_per_symbol_per_day}/symbol/day")

    def can_fire(self, symbol: str) -> bool:
        """
        Check if an alert is allowed under rate limits.

        Args:
            symbol: Stock symbol

        Returns:
            True if alert can fire, False if blocked by rate limit
        """
        self._maybe_reset_daily()

        # Check cycle limit
        if self._cycle_count >= self.max_per_cycle:
            logger.debug(f"Rate limit: cycle limit reached ({self._cycle_count}/{self.max_per_cycle})")
            return False

        # Check symbol daily limit
        symbol_count = self._symbol_daily.get(symbol, 0)
        if symbol_count >= self.max_per_symbol_per_day:
            logger.debug(f"Rate limit: {symbol} daily limit reached ({symbol_count}/{self.max_per_symbol_per_day})")
            return False

        return True

    def record_fire(self, symbol: str) -> None:
        """
        Record that an alert fired (increment counters).

        Args:
            symbol: Stock symbol that triggered an alert
        """
        self._cycle_count += 1
        self._symbol_daily[symbol] = self._symbol_daily.get(symbol, 0) + 1
        logger.debug(f"Alert recorded for {symbol}: {self._cycle_count} in cycle, {self._symbol_daily[symbol]} for day")

    def reset_cycle(self) -> None:
        """Reset cycle counter at the start of each check cycle."""
        self._cycle_count = 0
        logger.debug("Cycle counter reset")

    def _maybe_reset_daily(self) -> None:
        """
        Check if day has changed and reset daily counter if needed.
        Called before each can_fire() check.
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        if today != self._day_key:
            self._day_key = today
            self._symbol_daily = {}
            logger.info(f"Daily counter reset for {today}")

    def get_status(self) -> Dict:
        """Get current limiter status."""
        self._maybe_reset_daily()
        return {
            'cycle_count': self._cycle_count,
            'max_per_cycle': self.max_per_cycle,
            'symbols_with_alerts_today': len(self._symbol_daily),
            'current_date': self._day_key,
            'symbol_alert_counts': dict(self._symbol_daily)
        }
