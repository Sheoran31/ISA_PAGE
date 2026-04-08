"""
Repository for managing daily price history records.
Stores 200+ days of OHLC data and calculated EMAs.
"""

import json
from datetime import datetime
from typing import List, Dict, Optional

from storage.database import db
from utils.logger import logger
from utils.exceptions import DatabaseError


class PriceHistoryRepository:
    """Manages historical OHLC data and EMA calculations."""

    @staticmethod
    def insert_or_update_ohlc(symbol: str, ohlc_data: List[Dict]) -> int:
        """
        Insert or update OHLC data for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'NSE:TCS')
            ohlc_data: List of dicts with 'date', 'open', 'high', 'low', 'close', 'volume'

        Returns:
            Number of records inserted/updated
        """
        try:
            now = datetime.utcnow().isoformat()
            count = 0

            for candle in ohlc_data:
                query = '''
                    INSERT INTO daily_price_history
                    (symbol, date, open, high, low, close, volume, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(symbol, date) DO UPDATE SET
                        open=excluded.open,
                        high=excluded.high,
                        low=excluded.low,
                        close=excluded.close,
                        volume=excluded.volume,
                        fetched_at=excluded.fetched_at
                '''
                params = (
                    symbol,
                    candle['date'],
                    candle.get('open'),
                    candle.get('high'),
                    candle.get('low'),
                    candle.get('close'),
                    candle.get('volume'),
                    now
                )

                db.execute_update(query, params)
                count += 1

            logger.info(f"Inserted/updated {count} OHLC records for {symbol}")
            return count
        except Exception as e:
            logger.error(f"Failed to insert OHLC data: {e}")
            raise DatabaseError(f"Insert OHLC failed: {e}")

    @staticmethod
    def get_last_n_candles(symbol: str, n: int = 200) -> List[Dict]:
        """
        Get last N candles for a symbol.

        Args:
            symbol: Stock symbol
            n: Number of candles to retrieve

        Returns:
            List of OHLC dicts (oldest to newest)
        """
        try:
            query = '''
                SELECT symbol, date, open, high, low, close, volume,
                       ema_20, ema_50, ema_100, ema_150, ema_200,
                       is_consolidated, consolidation_days
                FROM daily_price_history
                WHERE symbol = ?
                ORDER BY date DESC
                LIMIT ?
            '''
            rows = db.execute_query(query, (symbol, n))

            candles = []
            for row in reversed(rows):  # Reverse to get oldest to newest
                candles.append({
                    'symbol': row[0],
                    'date': row[1],
                    'open': row[2],
                    'high': row[3],
                    'low': row[4],
                    'close': row[5],
                    'volume': row[6],
                    'ema_20': row[7],
                    'ema_50': row[8],
                    'ema_100': row[9],
                    'ema_150': row[10],
                    'ema_200': row[11],
                    'is_consolidated': row[12],
                    'consolidation_days': row[13]
                })

            return candles
        except Exception as e:
            logger.error(f"Failed to get candles: {e}")
            raise DatabaseError(f"Query failed: {e}")

    @staticmethod
    def update_emas_for_candle(symbol: str, date: str, ema_values: Dict[int, float]) -> bool:
        """
        Update calculated EMA values for a specific candle.

        Args:
            symbol: Stock symbol
            date: Date (YYYY-MM-DD)
            ema_values: Dict of period -> value (e.g., {20: 3505.2, 50: 3498.0, ...})

        Returns:
            True if updated
        """
        try:
            query = '''
                UPDATE daily_price_history
                SET ema_20 = ?, ema_50 = ?, ema_100 = ?, ema_150 = ?, ema_200 = ?
                WHERE symbol = ? AND date = ?
            '''
            params = (
                ema_values.get(20),
                ema_values.get(50),
                ema_values.get(100),
                ema_values.get(150),
                ema_values.get(200),
                symbol,
                date
            )

            rows_affected = db.execute_update(query, params)
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Failed to update EMAs: {e}")
            raise DatabaseError(f"Update failed: {e}")

    @staticmethod
    def mark_consolidated(symbol: str, date: str, is_consolidated: bool, days: int) -> bool:
        """
        Mark a candle as consolidated or not.

        Args:
            symbol: Stock symbol
            date: Date (YYYY-MM-DD)
            is_consolidated: True if in narrow range
            days: Number of consecutive days in range

        Returns:
            True if updated
        """
        try:
            query = '''
                UPDATE daily_price_history
                SET is_consolidated = ?, consolidation_days = ?
                WHERE symbol = ? AND date = ?
            '''
            params = (1 if is_consolidated else 0, days, symbol, date)

            rows_affected = db.execute_update(query, params)
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Failed to mark consolidated: {e}")
            raise DatabaseError(f"Update failed: {e}")

    @staticmethod
    def get_consolidation_info(symbol: str) -> Optional[Dict]:
        """
        Get consolidation status for a symbol.

        Returns last 10 candles to analyze consolidation.
        """
        try:
            query = '''
                SELECT date, close, ema_20, ema_50, ema_100, ema_150, ema_200,
                       is_consolidated, consolidation_days
                FROM daily_price_history
                WHERE symbol = ?
                ORDER BY date DESC
                LIMIT 10
            '''
            rows = db.execute_query(query, (symbol,))

            if not rows:
                return None

            candles = []
            for row in reversed(rows):  # Oldest to newest
                candles.append({
                    'date': row[0],
                    'close': row[1],
                    'ema_20': row[2],
                    'ema_50': row[3],
                    'ema_100': row[4],
                    'ema_150': row[5],
                    'ema_200': row[6],
                    'is_consolidated': bool(row[7]),
                    'consolidation_days': row[8]
                })

            return {
                'symbol': symbol,
                'candles': candles,
                'latest_date': candles[-1]['date'] if candles else None,
                'latest_consolidation_days': candles[-1]['consolidation_days'] if candles else 0
            }
        except Exception as e:
            logger.error(f"Failed to get consolidation info: {e}")
            return None

    @staticmethod
    def count_candles(symbol: str) -> int:
        """Count total candles stored for a symbol."""
        try:
            query = 'SELECT COUNT(*) FROM daily_price_history WHERE symbol = ?'
            rows = db.execute_query(query, (symbol,))
            return rows[0][0] if rows else 0
        except Exception as e:
            logger.error(f"Failed to count candles: {e}")
            return 0

    @staticmethod
    def get_oldest_candle(symbol: str) -> Optional[Dict]:
        """Get oldest stored candle for a symbol."""
        try:
            query = '''
                SELECT date, close FROM daily_price_history
                WHERE symbol = ?
                ORDER BY date ASC
                LIMIT 1
            '''
            rows = db.execute_query(query, (symbol,))

            if not rows:
                return None

            return {'date': rows[0][0], 'close': rows[0][1]}
        except Exception as e:
            logger.error(f"Failed to get oldest candle: {e}")
            return None

    @staticmethod
    def delete_old_candles(symbol: str, keep_days: int = 250) -> int:
        """
        Delete candles older than keep_days to save space.

        Args:
            symbol: Stock symbol
            keep_days: Keep last N days

        Returns:
            Number of rows deleted
        """
        try:
            query = '''
                DELETE FROM daily_price_history
                WHERE symbol = ?
                AND date < (
                    SELECT date FROM daily_price_history
                    WHERE symbol = ?
                    ORDER BY date DESC
                    LIMIT 1 OFFSET ?
                )
            '''
            rows_affected = db.execute_update(query, (symbol, symbol, keep_days - 1))
            logger.info(f"Deleted {rows_affected} old candles for {symbol}")
            return rows_affected
        except Exception as e:
            logger.error(f"Failed to delete old candles: {e}")
            return 0
