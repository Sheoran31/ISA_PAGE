"""
Engine State Repository: Persists engine state for crash recovery.
Saves/loads engine snapshots to track last check time, alerts fired, etc.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from storage.database import db
from utils.logger import logger
from utils.exceptions import DatabaseError


class EngineStateRepository:
    """Manages persistence of engine state for recovery after crashes."""

    @staticmethod
    def save(key: str, value: Any) -> None:
        """
        Save a single state value.

        Args:
            key: State key (e.g., 'last_check_time', 'alerts_fired_today')
            value: Value to save (will be JSON serialized)
        """
        try:
            value_json = json.dumps(value)
            now = datetime.utcnow().isoformat()
            query = '''
                INSERT INTO engine_state (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            '''
            db.execute_update(query, (key, value_json, now))
            logger.debug(f"Engine state saved: {key}")
        except Exception as e:
            logger.error(f"Failed to save engine state '{key}': {e}")

    @staticmethod
    def load(key: str, default: Any = None) -> Any:
        """
        Load a single state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            Deserialized value or default
        """
        try:
            query = 'SELECT value FROM engine_state WHERE key = ?'
            rows = db.execute_query(query, (key,))
            if rows:
                value_json = rows[0][0]
                return json.loads(value_json)
            return default
        except Exception as e:
            logger.warning(f"Failed to load engine state '{key}': {e}")
            return default

    @staticmethod
    def save_snapshot(state: Dict) -> None:
        """
        Save a complete engine state snapshot.

        Args:
            state: Dictionary with engine state (last_check_time, alerts_fired_today, etc.)
        """
        try:
            for key, value in state.items():
                EngineStateRepository.save(key, value)
            logger.debug(f"Engine snapshot saved: {len(state)} items")
        except Exception as e:
            logger.error(f"Failed to save engine snapshot: {e}")

    @staticmethod
    def load_snapshot() -> Dict:
        """
        Load the last saved engine state snapshot.

        Returns:
            Dictionary with saved state or empty dict if none exists
        """
        try:
            query = 'SELECT key, value FROM engine_state'
            rows = db.execute_query(query)

            snapshot = {}
            for row in rows:
                key = row[0]
                value_json = row[1]
                try:
                    snapshot[key] = json.loads(value_json)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to deserialize state key '{key}'")

            logger.info(f"Engine snapshot loaded: {len(snapshot)} items")
            return snapshot
        except Exception as e:
            logger.warning(f"Failed to load engine snapshot: {e}")
            return {}

    @staticmethod
    def delete(key: str) -> None:
        """Delete a state key."""
        try:
            query = 'DELETE FROM engine_state WHERE key = ?'
            db.execute_update(query, (key,))
            logger.debug(f"Engine state deleted: {key}")
        except Exception as e:
            logger.error(f"Failed to delete engine state '{key}': {e}")

    @staticmethod
    def clear_all() -> None:
        """Clear all engine state (for testing)."""
        try:
            query = 'DELETE FROM engine_state'
            db.execute_update(query)
            logger.info("All engine state cleared")
        except Exception as e:
            logger.error(f"Failed to clear engine state: {e}")
