"""
Repository for managing alert history records.
Handles all database operations for alert_history table.
"""

import json
from datetime import datetime
from typing import List, Dict, Optional

from storage.database import db
from utils.logger import logger
from utils.exceptions import DatabaseError


class AlertRepository:
    """Manages alert history records."""

    @staticmethod
    def insert_alert_history(
        alert_id: str,
        alert_name: str,
        symbol: str,
        condition_type: str,
        condition_params: Dict,
        triggered_price: float,
        triggered_at: str,
        message_sent: str,
        telegram_status: str = 'sent'
    ) -> int:
        """
        Insert a new alert history record.

        Args:
            alert_id: ID of the alert that fired
            alert_name: Human-readable alert name
            symbol: Stock symbol (e.g., 'NSE:TCS')
            condition_type: Type of condition (e.g., 'price_above')
            condition_params: Dict of condition parameters
            triggered_price: Price at which alert triggered
            triggered_at: ISO 8601 timestamp when it triggered
            message_sent: The message text sent to Telegram
            telegram_status: Status of message delivery

        Returns:
            Row ID of inserted record
        """
        try:
            query = '''
                INSERT INTO alert_history
                (alert_id, alert_name, symbol, condition_type, condition_params,
                 triggered_price, triggered_at, message_sent, telegram_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                alert_id,
                alert_name,
                symbol,
                condition_type,
                json.dumps(condition_params),
                triggered_price,
                triggered_at,
                message_sent,
                telegram_status
            )

            cursor = db.connection.cursor()
            cursor.execute(query, params)
            db.connection.commit()

            row_id = cursor.lastrowid
            logger.info(f"Alert history recorded: {alert_id} at {triggered_price}")
            return row_id
        except Exception as e:
            logger.error(f"Failed to insert alert history: {e}")
            raise DatabaseError(f"Insert failed: {e}")

    @staticmethod
    def get_recent_alerts(limit: int = 10, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get recent alert history records.

        Args:
            limit: Number of recent alerts to return
            symbol: Optional filter by symbol

        Returns:
            List of alert dictionaries
        """
        try:
            if symbol:
                query = '''
                    SELECT * FROM alert_history
                    WHERE symbol = ?
                    ORDER BY triggered_at DESC
                    LIMIT ?
                '''
                rows = db.execute_query(query, (symbol, limit))
            else:
                query = '''
                    SELECT * FROM alert_history
                    ORDER BY triggered_at DESC
                    LIMIT ?
                '''
                rows = db.execute_query(query, (limit,))

            alerts = []
            for row in rows:
                alerts.append({
                    'id': row[0],
                    'alert_id': row[1],
                    'alert_name': row[2],
                    'symbol': row[3],
                    'condition_type': row[4],
                    'condition_params': json.loads(row[5]),
                    'triggered_price': row[6],
                    'triggered_at': row[7],
                    'message_sent': row[8],
                    'telegram_status': row[9]
                })

            return alerts
        except Exception as e:
            logger.error(f"Failed to fetch recent alerts: {e}")
            raise DatabaseError(f"Query failed: {e}")

    @staticmethod
    def get_alerts_by_symbol(symbol: str, days: int = 7) -> List[Dict]:
        """
        Get all alerts for a specific symbol within N days.

        Args:
            symbol: Stock symbol to filter by
            days: Number of past days to look at

        Returns:
            List of alert dictionaries
        """
        try:
            query = '''
                SELECT * FROM alert_history
                WHERE symbol = ?
                AND datetime(triggered_at) > datetime('now', '-' || ? || ' days')
                ORDER BY triggered_at DESC
            '''
            rows = db.execute_query(query, (symbol, days))

            alerts = []
            for row in rows:
                alerts.append({
                    'id': row[0],
                    'alert_id': row[1],
                    'alert_name': row[2],
                    'symbol': row[3],
                    'condition_type': row[4],
                    'condition_params': json.loads(row[5]),
                    'triggered_price': row[6],
                    'triggered_at': row[7],
                    'message_sent': row[8],
                    'telegram_status': row[9]
                })

            return alerts
        except Exception as e:
            logger.error(f"Failed to fetch alerts by symbol: {e}")
            raise DatabaseError(f"Query failed: {e}")

    @staticmethod
    def get_alert_count_today() -> int:
        """Get count of alerts fired today."""
        try:
            query = '''
                SELECT COUNT(*) FROM alert_history
                WHERE DATE(triggered_at) = DATE('now')
            '''
            rows = db.execute_query(query)
            return rows[0][0] if rows else 0
        except Exception as e:
            logger.error(f"Failed to get alert count: {e}")
            return 0

    @staticmethod
    def get_failed_alerts(limit: int = 20) -> List[Dict]:
        """Get alerts that failed to send via Telegram."""
        try:
            query = '''
                SELECT * FROM alert_history
                WHERE telegram_status IN ('failed', 'rate_limited')
                ORDER BY triggered_at DESC
                LIMIT ?
            '''
            rows = db.execute_query(query, (limit,))

            alerts = []
            for row in rows:
                alerts.append({
                    'id': row[0],
                    'alert_id': row[1],
                    'alert_name': row[2],
                    'symbol': row[3],
                    'triggered_at': row[7],
                    'telegram_status': row[9]
                })

            return alerts
        except Exception as e:
            logger.error(f"Failed to fetch failed alerts: {e}")
            return []
