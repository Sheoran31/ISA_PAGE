"""
Cooldown Manager: Prevent alert spam by tracking last-fired times.
Ensures same alert doesn't fire too frequently.
"""

from datetime import datetime, timedelta
from typing import Dict
import json
from pathlib import Path

from storage.database import db
from utils.logger import logger


class CooldownManager:
    """
    Manages alert cooldowns to prevent spam.

    Each alert has a cooldown period (e.g., 30 minutes).
    Same alert won't trigger again within its cooldown window.
    """

    def __init__(self):
        """Initialize cooldown manager."""
        self._memory_cache: Dict[str, datetime] = {}
        self._load_from_db()
        logger.info("CooldownManager initialized")

    def _load_from_db(self) -> None:
        """Load cooldown state from database on startup."""
        try:
            query = 'SELECT alert_id, last_fired_at FROM cooldown_state'
            rows = db.execute_query(query)

            for row in rows:
                alert_id = row[0]
                last_fired_str = row[1]
                try:
                    last_fired = datetime.fromisoformat(last_fired_str)
                    self._memory_cache[alert_id] = last_fired
                except ValueError:
                    logger.warning(f"Invalid cooldown timestamp for {alert_id}")

            logger.info(f"Loaded {len(self._memory_cache)} cooldown states")
        except Exception as e:
            logger.warning(f"Failed to load cooldown state: {e}")

    def is_in_cooldown(self, alert_id: str, cooldown_minutes: int = 30) -> bool:
        """
        Check if alert is currently in cooldown.

        Args:
            alert_id: Alert ID
            cooldown_minutes: Cooldown duration in minutes

        Returns:
            True if still in cooldown, False if can fire
        """
        if alert_id not in self._memory_cache:
            return False

        last_fired = self._memory_cache[alert_id]
        cooldown_expires = last_fired + timedelta(minutes=cooldown_minutes)
        now = datetime.utcnow()

        if now < cooldown_expires:
            remaining = (cooldown_expires - now).total_seconds() / 60
            logger.debug(f"{alert_id}: In cooldown ({remaining:.1f} min remaining)")
            return True

        return False

    def set_cooldown(self, alert_id: str, cooldown_minutes: int = 30) -> None:
        """
        Set cooldown for an alert after it fires.

        Args:
            alert_id: Alert ID
            cooldown_minutes: Cooldown duration
        """
        now = datetime.utcnow()
        self._memory_cache[alert_id] = now

        # Also save to database
        try:
            query = '''
                INSERT INTO cooldown_state (alert_id, last_fired_at)
                VALUES (?, ?)
                ON CONFLICT(alert_id) DO UPDATE SET last_fired_at=excluded.last_fired_at
            '''
            db.execute_update(query, (alert_id, now.isoformat()))
            logger.debug(f"{alert_id}: Cooldown set for {cooldown_minutes} minutes")
        except Exception as e:
            logger.error(f"Failed to save cooldown: {e}")

    def reset_cooldown(self, alert_id: str) -> None:
        """
        Reset cooldown for an alert (allow it to fire again immediately).

        Args:
            alert_id: Alert ID
        """
        if alert_id in self._memory_cache:
            del self._memory_cache[alert_id]

        try:
            query = 'DELETE FROM cooldown_state WHERE alert_id = ?'
            db.execute_update(query, (alert_id,))
            logger.info(f"{alert_id}: Cooldown reset")
        except Exception as e:
            logger.error(f"Failed to reset cooldown: {e}")

    def get_remaining_cooldown(self, alert_id: str, cooldown_minutes: int = 30) -> int:
        """
        Get remaining cooldown time in minutes.

        Returns:
            Remaining minutes (0 if no cooldown)
        """
        if alert_id not in self._memory_cache:
            return 0

        last_fired = self._memory_cache[alert_id]
        cooldown_expires = last_fired + timedelta(minutes=cooldown_minutes)
        now = datetime.utcnow()

        if now < cooldown_expires:
            remaining = int((cooldown_expires - now).total_seconds() / 60)
            return max(remaining, 0)

        return 0

    def clear_expired_cooldowns(self) -> int:
        """
        Clear expired cooldowns from cache.

        Returns:
            Number of cleared entries
        """
        now = datetime.utcnow()
        expired = []

        for alert_id, last_fired in self._memory_cache.items():
            # Assume default 30 minute cooldown
            if now > last_fired + timedelta(minutes=30):
                expired.append(alert_id)

        for alert_id in expired:
            del self._memory_cache[alert_id]

        logger.debug(f"Cleared {len(expired)} expired cooldowns")
        return len(expired)

    def summary(self) -> str:
        """Get cooldown summary."""
        if not self._memory_cache:
            return "No active cooldowns"

        lines = [f"Active cooldowns: {len(self._memory_cache)}"]
        for alert_id, last_fired in list(self._memory_cache.items())[:5]:
            ago = (datetime.utcnow() - last_fired).total_seconds() / 60
            lines.append(f"  {alert_id}: {ago:.1f} min ago")

        if len(self._memory_cache) > 5:
            lines.append(f"  ... and {len(self._memory_cache) - 5} more")

        return "\n".join(lines)
