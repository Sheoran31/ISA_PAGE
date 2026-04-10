"""
Metrics Repository: Records per-cycle metrics for dashboard and analytics.
Tracks alerts fired, symbols checked, performance metrics, etc.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from storage.database import db
from utils.logger import logger
from utils.exceptions import DatabaseError


class MetricsRepository:
    """Manages metrics collection and retrieval for system monitoring."""

    @staticmethod
    def record_cycle(cycle_result: Dict) -> None:
        """
        Record one check cycle's metrics.

        Args:
            cycle_result: Result dict from AlertEngine/AgentOrchestrator with keys:
                - success: bool
                - alerts_fired: int
                - symbols_checked: int
                - elapsed_seconds: float
                - error (optional): str
                - timestamp: str (ISO format)
        """
        try:
            success = 1 if cycle_result.get('success', False) else 0
            cycle_at = cycle_result.get('timestamp', datetime.utcnow().isoformat())
            alerts_fired = cycle_result.get('alerts_fired', 0)
            symbols_checked = cycle_result.get('symbols_checked', 0)
            elapsed_seconds = cycle_result.get('elapsed_seconds', 0)
            error_details = cycle_result.get('error', None)

            query = '''
                INSERT INTO metrics (cycle_at, alerts_fired, symbols_checked, elapsed_seconds, success, error_details)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            db.execute_update(query, (cycle_at, alerts_fired, symbols_checked, elapsed_seconds, success, error_details))
            logger.debug(f"Metrics recorded: {alerts_fired} alerts, {symbols_checked} symbols checked")
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")

    @staticmethod
    def get_daily_summary(days: int = 7) -> List[Dict]:
        """
        Get aggregated daily metrics for the last N days.

        Args:
            days: Number of days to summarize (default 7)

        Returns:
            List of dicts with daily aggregates:
            {
                'date': YYYY-MM-DD,
                'total_cycles': int,
                'total_alerts': int,
                'avg_symbols': float,
                'avg_elapsed_seconds': float,
                'success_count': int,
                'failure_count': int
            }
        """
        try:
            query = '''
                SELECT
                    DATE(cycle_at) as date,
                    COUNT(*) as total_cycles,
                    SUM(alerts_fired) as total_alerts,
                    AVG(symbols_checked) as avg_symbols,
                    AVG(elapsed_seconds) as avg_elapsed_seconds,
                    SUM(success) as success_count,
                    SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failure_count
                FROM metrics
                WHERE cycle_at >= datetime('now', '-' || ? || ' days')
                GROUP BY DATE(cycle_at)
                ORDER BY date DESC
            '''
            rows = db.execute_query(query, (days,))

            summary = []
            for row in rows:
                summary.append({
                    'date': row[0],
                    'total_cycles': row[1],
                    'total_alerts': row[2] or 0,
                    'avg_symbols': round(row[3] or 0, 1),
                    'avg_elapsed_seconds': round(row[4] or 0, 2),
                    'success_count': row[5] or 0,
                    'failure_count': row[6] or 0
                })
            logger.debug(f"Daily summary retrieved: {len(summary)} days")
            return summary
        except Exception as e:
            logger.error(f"Failed to get daily summary: {e}")
            return []

    @staticmethod
    def get_cycle_count_today() -> int:
        """Get number of check cycles that ran today."""
        try:
            query = '''
                SELECT COUNT(*) FROM metrics
                WHERE DATE(cycle_at) = DATE('now')
            '''
            rows = db.execute_query(query)
            return rows[0][0] if rows else 0
        except Exception as e:
            logger.error(f"Failed to get cycle count: {e}")
            return 0

    @staticmethod
    def get_alerts_today() -> int:
        """Get total alerts fired today."""
        try:
            query = '''
                SELECT COALESCE(SUM(alerts_fired), 0) FROM metrics
                WHERE DATE(cycle_at) = DATE('now') AND success = 1
            '''
            rows = db.execute_query(query)
            return rows[0][0] if rows else 0
        except Exception as e:
            logger.error(f"Failed to get alerts today: {e}")
            return 0

    @staticmethod
    def get_component_error_rates() -> Dict[str, Any]:
        """
        Get error statistics (failures, success rate, etc.).

        Returns:
            Dict with:
            {
                'total_cycles': int,
                'success_cycles': int,
                'failed_cycles': int,
                'success_rate': float (0-100)
            }
        """
        try:
            query = '''
                SELECT
                    COUNT(*) as total,
                    SUM(success) as success_count,
                    SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failure_count
                FROM metrics
            '''
            rows = db.execute_query(query)
            if rows:
                total = rows[0][0] or 0
                success = rows[0][1] or 0
                failed = rows[0][2] or 0
                success_rate = (success / total * 100) if total > 0 else 0
                return {
                    'total_cycles': total,
                    'success_cycles': success,
                    'failed_cycles': failed,
                    'success_rate': round(success_rate, 2)
                }
            return {
                'total_cycles': 0,
                'success_cycles': 0,
                'failed_cycles': 0,
                'success_rate': 0.0
            }
        except Exception as e:
            logger.error(f"Failed to get error rates: {e}")
            return {}

    @staticmethod
    def get_recent_metrics(limit: int = 20) -> List[Dict]:
        """Get the N most recent cycle metrics."""
        try:
            query = '''
                SELECT
                    cycle_at,
                    alerts_fired,
                    symbols_checked,
                    elapsed_seconds,
                    success,
                    error_details
                FROM metrics
                ORDER BY cycle_at DESC
                LIMIT ?
            '''
            rows = db.execute_query(query, (limit,))

            metrics = []
            for row in rows:
                metrics.append({
                    'cycle_at': row[0],
                    'alerts_fired': row[1],
                    'symbols_checked': row[2],
                    'elapsed_seconds': round(row[3], 2),
                    'success': bool(row[4]),
                    'error': row[5]
                })
            return metrics
        except Exception as e:
            logger.error(f"Failed to get recent metrics: {e}")
            return []

    @staticmethod
    def cleanup_old_metrics(days_to_keep: int = 90) -> int:
        """Delete metrics older than N days. Returns count deleted."""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
            query = 'DELETE FROM metrics WHERE cycle_at < ?'
            rowcount = db.execute_update(query, (cutoff_date,))
            logger.info(f"Cleaned up {rowcount} old metrics")
            return rowcount
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return 0
