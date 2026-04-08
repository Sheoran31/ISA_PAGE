"""
Consolidation Tracker: Tracks consecutive days within narrow EMA range.
Determines when a consolidation period has begun for EMA breakout alerts.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
from storage.database import db
from utils.logger import logger


class ConsolidationTracker:
    """
    Tracks how many consecutive days a symbol has been in consolidation.

    A consolidation is when all 5 EMAs (20, 50, 100, 150, 200) are within
    a narrow range (e.g., 5% of each other) for 3+ consecutive days.
    """

    @staticmethod
    def get_consolidation_state(symbol: str) -> Optional[Dict]:
        """
        Get current consolidation state for a symbol.

        Returns:
            Dict with keys:
                - consecutive_days: How many days in consolidation
                - start_date: When consolidation started
                - range_high: Highest EMA in consolidation
                - range_low: Lowest EMA in consolidation
                - is_active: True if actively consolidated
        """
        try:
            query = '''
                SELECT consecutive_days, start_date, range_high, range_low, narrow_range_percent
                FROM consolidation_state
                WHERE symbol = ?
            '''
            rows = db.execute_query(query, (symbol,))

            if not rows:
                return {
                    'symbol': symbol,
                    'consecutive_days': 0,
                    'start_date': None,
                    'range_high': None,
                    'range_low': None,
                    'is_active': False
                }

            row = rows[0]
            return {
                'symbol': symbol,
                'consecutive_days': row[0],
                'start_date': row[1],
                'range_high': row[2],
                'range_low': row[3],
                'narrow_range_percent': row[4],
                'is_active': row[0] >= 3  # Active if 3+ days
            }
        except Exception as e:
            logger.error(f"Failed to get consolidation state: {e}")
            return None

    @staticmethod
    def update_consolidation(
        symbol: str,
        is_consolidated: bool,
        range_high: Optional[float] = None,
        range_low: Optional[float] = None,
        narrow_range_percent: float = 5.0
    ) -> bool:
        """
        Update consolidation state for a symbol.

        If is_consolidated is True:
            - Increment consecutive_days
            - Update range_high/low

        If is_consolidated is False:
            - Reset consecutive_days to 0
            - Reset range_high/low

        Args:
            symbol: Stock symbol
            is_consolidated: Is today in consolidation?
            range_high: Highest EMA value
            range_low: Lowest EMA value
            narrow_range_percent: Consolidation tolerance %

        Returns:
            True if updated
        """
        try:
            now = datetime.utcnow().isoformat()

            # Get current state
            current = ConsolidationTracker.get_consolidation_state(symbol)
            if not current:
                current = {'consecutive_days': 0, 'start_date': None}

            if is_consolidated:
                # Continue or start consolidation
                if current['consecutive_days'] > 0:
                    # Already consolidating, increment
                    new_days = current['consecutive_days'] + 1
                    start_date = current['start_date']
                else:
                    # Start new consolidation
                    new_days = 1
                    start_date = datetime.utcnow().strftime('%Y-%m-%d')
            else:
                # End consolidation
                new_days = 0
                start_date = None

            # Insert or update
            query = '''
                INSERT INTO consolidation_state
                (symbol, consecutive_days, start_date, range_high, range_low,
                 narrow_range_percent, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    consecutive_days=excluded.consecutive_days,
                    start_date=excluded.start_date,
                    range_high=excluded.range_high,
                    range_low=excluded.range_low,
                    narrow_range_percent=excluded.narrow_range_percent,
                    last_checked=excluded.last_checked
            '''
            params = (
                symbol,
                new_days,
                start_date,
                range_high,
                range_low,
                narrow_range_percent,
                now
            )

            db.execute_update(query, params)

            if is_consolidated:
                logger.debug(f"{symbol}: Consolidation day {new_days} (range: {range_low:.2f} - {range_high:.2f})")
            else:
                logger.debug(f"{symbol}: Consolidation ended")

            return True
        except Exception as e:
            logger.error(f"Failed to update consolidation: {e}")
            return False

    @staticmethod
    def is_consolidation_active(symbol: str, min_days: int = 3) -> bool:
        """
        Check if symbol is in active consolidation.

        Active = consecutive_days >= min_days

        Args:
            symbol: Stock symbol
            min_days: Minimum days required for active consolidation

        Returns:
            True if actively consolidated
        """
        state = ConsolidationTracker.get_consolidation_state(symbol)
        if not state:
            return False
        return state['consecutive_days'] >= min_days

    @staticmethod
    def get_consolidation_duration(symbol: str) -> int:
        """
        Get number of consecutive consolidation days.

        Returns:
            Number of days (0 if not consolidating)
        """
        state = ConsolidationTracker.get_consolidation_state(symbol)
        if not state:
            return 0
        return state['consecutive_days']

    @staticmethod
    def reset_consolidation(symbol: str) -> bool:
        """
        Reset consolidation state (used after breakout alert).

        Args:
            symbol: Stock symbol

        Returns:
            True if reset
        """
        try:
            query = '''
                UPDATE consolidation_state
                SET consecutive_days = 0, start_date = NULL,
                    range_high = NULL, range_low = NULL
                WHERE symbol = ?
            '''
            db.execute_update(query, (symbol,))
            logger.info(f"{symbol}: Consolidation reset after breakout")
            return True
        except Exception as e:
            logger.error(f"Failed to reset consolidation: {e}")
            return False

    @staticmethod
    def get_all_consolidating_symbols(min_days: int = 3) -> List[str]:
        """
        Get all symbols currently in consolidation.

        Args:
            min_days: Minimum days to be considered consolidating

        Returns:
            List of symbols
        """
        try:
            query = '''
                SELECT symbol FROM consolidation_state
                WHERE consecutive_days >= ?
                ORDER BY consecutive_days DESC
            '''
            rows = db.execute_query(query, (min_days,))
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Failed to get consolidating symbols: {e}")
            return []

    @staticmethod
    def get_consolidation_summary() -> Dict[str, Dict]:
        """
        Get consolidation status for all symbols.

        Returns:
            Dict mapping symbol -> consolidation info
        """
        try:
            query = '''
                SELECT symbol, consecutive_days, start_date, range_high, range_low
                FROM consolidation_state
                WHERE consecutive_days > 0
                ORDER BY consecutive_days DESC
            '''
            rows = db.execute_query(query)

            summary = {}
            for row in rows:
                summary[row[0]] = {
                    'days': row[1],
                    'start_date': row[2],
                    'range_high': row[3],
                    'range_low': row[4]
                }

            return summary
        except Exception as e:
            logger.error(f"Failed to get consolidation summary: {e}")
            return {}
