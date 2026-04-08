"""
Repository for managing bot-added conditions.
Handles all database operations for conditions table.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from storage.database import db
from utils.logger import logger
from utils.exceptions import DatabaseError


class ConditionRepository:
    """Manages bot-added conditions stored in database."""

    @staticmethod
    def add_condition(
        name: str,
        symbol: str,
        condition_type: str,
        parameters: Dict,
        cooldown_minutes: int = 30,
        enabled: bool = True
    ) -> str:
        """
        Add a new condition to the database.

        Args:
            name: Human-readable name for the alert
            symbol: Stock symbol (e.g., 'NSE:TCS')
            condition_type: Type (price_above, price_below, etc.)
            parameters: Dict of condition parameters
            cooldown_minutes: Cooldown before re-triggering
            enabled: Whether condition is active

        Returns:
            alert_id of the newly created condition
        """
        try:
            alert_id = str(uuid.uuid4())[:8]  # Short UUID
            now = datetime.utcnow().isoformat()

            query = '''
                INSERT INTO conditions
                (alert_id, name, symbol, condition_type, parameters,
                 cooldown_minutes, enabled, created_by, created_at, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                alert_id,
                name,
                symbol,
                condition_type,
                json.dumps(parameters),
                cooldown_minutes,
                1 if enabled else 0,
                'bot',
                now,
                now
            )

            db.execute_update(query, params)
            logger.info(f"Condition added: {alert_id} - {name}")
            return alert_id
        except Exception as e:
            logger.error(f"Failed to add condition: {e}")
            raise DatabaseError(f"Insert failed: {e}")

    @staticmethod
    def list_conditions(enabled_only: bool = True) -> List[Dict]:
        """
        List all bot-added conditions.

        Args:
            enabled_only: If True, only return enabled conditions

        Returns:
            List of condition dictionaries
        """
        try:
            if enabled_only:
                query = 'SELECT * FROM conditions WHERE enabled = 1 ORDER BY created_at DESC'
                rows = db.execute_query(query)
            else:
                query = 'SELECT * FROM conditions ORDER BY created_at DESC'
                rows = db.execute_query(query)

            conditions = []
            for row in rows:
                conditions.append({
                    'id': row[0],
                    'alert_id': row[1],
                    'name': row[2],
                    'symbol': row[3],
                    'condition_type': row[4],
                    'parameters': json.loads(row[5]),
                    'cooldown_minutes': row[6],
                    'enabled': bool(row[7]),
                    'created_by': row[8],
                    'created_at': row[9],
                    'last_modified': row[10]
                })

            return conditions
        except Exception as e:
            logger.error(f"Failed to list conditions: {e}")
            raise DatabaseError(f"Query failed: {e}")

    @staticmethod
    def get_condition_by_id(alert_id: str) -> Optional[Dict]:
        """Get a single condition by its alert_id."""
        try:
            query = 'SELECT * FROM conditions WHERE alert_id = ?'
            rows = db.execute_query(query, (alert_id,))

            if not rows:
                return None

            row = rows[0]
            return {
                'id': row[0],
                'alert_id': row[1],
                'name': row[2],
                'symbol': row[3],
                'condition_type': row[4],
                'parameters': json.loads(row[5]),
                'cooldown_minutes': row[6],
                'enabled': bool(row[7]),
                'created_by': row[8],
                'created_at': row[9],
                'last_modified': row[10]
            }
        except Exception as e:
            logger.error(f"Failed to get condition: {e}")
            raise DatabaseError(f"Query failed: {e}")

    @staticmethod
    def delete_condition(alert_id: str) -> bool:
        """
        Delete a condition by alert_id.

        Args:
            alert_id: ID of condition to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            query = 'DELETE FROM conditions WHERE alert_id = ?'
            rows_affected = db.execute_update(query, (alert_id,))

            if rows_affected > 0:
                logger.info(f"Condition deleted: {alert_id}")
                return True
            else:
                logger.warning(f"Condition not found: {alert_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete condition: {e}")
            raise DatabaseError(f"Delete failed: {e}")

    @staticmethod
    def update_condition_enabled(alert_id: str, enabled: bool) -> bool:
        """
        Enable or disable a condition.

        Args:
            alert_id: ID of condition
            enabled: True to enable, False to disable

        Returns:
            True if updated, False if not found
        """
        try:
            now = datetime.utcnow().isoformat()
            query = '''
                UPDATE conditions
                SET enabled = ?, last_modified = ?
                WHERE alert_id = ?
            '''
            params = (1 if enabled else 0, now, alert_id)
            rows_affected = db.execute_update(query, params)

            if rows_affected > 0:
                status = "enabled" if enabled else "disabled"
                logger.info(f"Condition {status}: {alert_id}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to update condition: {e}")
            raise DatabaseError(f"Update failed: {e}")

    @staticmethod
    def get_conditions_by_symbol(symbol: str, enabled_only: bool = True) -> List[Dict]:
        """
        Get all conditions for a specific symbol.

        Args:
            symbol: Stock symbol to filter by
            enabled_only: Only return enabled conditions

        Returns:
            List of condition dictionaries
        """
        try:
            if enabled_only:
                query = 'SELECT * FROM conditions WHERE symbol = ? AND enabled = 1'
            else:
                query = 'SELECT * FROM conditions WHERE symbol = ?'

            rows = db.execute_query(query, (symbol,))

            conditions = []
            for row in rows:
                conditions.append({
                    'id': row[0],
                    'alert_id': row[1],
                    'name': row[2],
                    'symbol': row[3],
                    'condition_type': row[4],
                    'parameters': json.loads(row[5]),
                    'cooldown_minutes': row[6],
                    'enabled': bool(row[7]),
                    'created_by': row[8],
                    'created_at': row[9],
                    'last_modified': row[10]
                })

            return conditions
        except Exception as e:
            logger.error(f"Failed to fetch conditions by symbol: {e}")
            raise DatabaseError(f"Query failed: {e}")

    @staticmethod
    def count_conditions(enabled_only: bool = True) -> int:
        """Count total conditions."""
        try:
            if enabled_only:
                query = 'SELECT COUNT(*) FROM conditions WHERE enabled = 1'
            else:
                query = 'SELECT COUNT(*) FROM conditions'

            rows = db.execute_query(query)
            return rows[0][0] if rows else 0
        except Exception as e:
            logger.error(f"Failed to count conditions: {e}")
            return 0
