"""
Load and manage conditions from conditions.json file.
Supports hot-reloading (detects file changes).
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from utils.logger import logger


class ConditionsLoader:
    """
    Load conditions from JSON file with caching and file monitoring.
    """

    CONDITIONS_FILE = Path(__file__).parent / 'conditions.json'

    def __init__(self):
        """Initialize loader."""
        self._last_modified = None
        self._cached_conditions = None
        self._load()

    def _load(self) -> None:
        """Load conditions from file."""
        try:
            if not self.CONDITIONS_FILE.exists():
                logger.warning(f"Conditions file not found: {self.CONDITIONS_FILE}")
                self._cached_conditions = []
                return

            # Check if file has changed
            current_mtime = os.path.getmtime(self.CONDITIONS_FILE)
            if self._last_modified == current_mtime and self._cached_conditions is not None:
                logger.debug("Conditions cache valid (no file change)")
                return

            # Load from file
            with open(self.CONDITIONS_FILE, 'r') as f:
                data = json.load(f)

            alerts = data.get('alerts', [])

            # Filter enabled alerts
            enabled_alerts = [a for a in alerts if a.get('enabled', True)]

            # Validate each alert
            validated = []
            for alert in enabled_alerts:
                try:
                    if self._validate_alert(alert):
                        validated.append(alert)
                    else:
                        logger.warning(f"Invalid alert: {alert.get('id')}")
                except Exception as e:
                    logger.error(f"Error validating alert {alert.get('id')}: {e}")

            self._cached_conditions = validated
            self._last_modified = current_mtime

            logger.info(f"Loaded {len(validated)} enabled conditions from {self.CONDITIONS_FILE}")

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in conditions.json: {e}")
            self._cached_conditions = []
        except Exception as e:
            logger.error(f"Failed to load conditions: {e}")
            self._cached_conditions = []

    def _validate_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Validate alert structure.

        Args:
            alert: Alert dict from JSON

        Returns:
            True if valid
        """
        required_fields = ['id', 'name', 'symbol', 'type', 'parameters']

        for field in required_fields:
            if field not in alert:
                logger.error(f"Missing required field '{field}' in alert")
                return False

        if not isinstance(alert['parameters'], dict):
            logger.error("'parameters' must be a dict")
            return False

        return True

    def get_conditions(self) -> List[Dict[str, Any]]:
        """
        Get all enabled conditions.

        Automatically reloads if file has changed.

        Returns:
            List of condition dicts
        """
        self._load()  # Check for changes
        return self._cached_conditions or []

    def get_conditions_for_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get conditions for a specific symbol.

        Args:
            symbol: Stock symbol

        Returns:
            List of condition dicts for that symbol
        """
        return [c for c in self.get_conditions() if c.get('symbol') == symbol]

    def get_conditions_by_type(self, condition_type: str) -> List[Dict[str, Any]]:
        """
        Get conditions of a specific type.

        Args:
            condition_type: Type string (price_above, ema_consolidation, etc.)

        Returns:
            List of matching conditions
        """
        return [c for c in self.get_conditions() if c.get('type') == condition_type]


# Global loader instance
_loader = ConditionsLoader()


def load_conditions() -> List[Dict[str, Any]]:
    """Get all enabled conditions."""
    return _loader.get_conditions()


def reload_conditions() -> None:
    """Force reload from file."""
    _loader._load()


def get_condition_count() -> int:
    """Get count of active conditions."""
    return len(_loader.get_conditions())
