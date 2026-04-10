"""
SQLite database initialization and connection management.
Creates all required tables on first run.
"""

import sqlite3
import os
from pathlib import Path
from threading import RLock

from config.settings import DATABASE_PATH
from utils.logger import logger
from utils.exceptions import DatabaseError


class Database:
    """SQLite database connection manager."""

    _instance = None
    _lock = RLock()

    def __new__(cls):
        """Singleton pattern to ensure only one DB instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize database connection and create tables."""
        if self._initialized:
            return

        self.db_path = DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30
            )
            self.connection.row_factory = sqlite3.Row
            # Enable WAL mode for concurrent multi-thread writes
            self.connection.execute("PRAGMA journal_mode=WAL")
            logger.info(f"Database connected: {self.db_path}")

            self._create_tables()
            self._initialized = True
        except sqlite3.Error as e:
            error_msg = f"Failed to initialize database: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def _create_tables(self):
        """Create all necessary tables if they don't exist."""
        cursor = self.connection.cursor()

        try:
            # TABLE: alert_history
            # Stores every alert that was triggered
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT NOT NULL,
                    alert_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    condition_type TEXT NOT NULL,
                    condition_params TEXT NOT NULL,
                    triggered_price REAL NOT NULL,
                    triggered_at TEXT NOT NULL,
                    message_sent TEXT NOT NULL,
                    telegram_status TEXT NOT NULL DEFAULT 'sent'
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_history_symbol ON alert_history(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_history_triggered_at ON alert_history(triggered_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_history_alert_id ON alert_history(alert_id)')

            # TABLE: conditions
            # Stores bot-added conditions (separate from conditions.json file)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conditions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    condition_type TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    cooldown_minutes INTEGER NOT NULL DEFAULT 30,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_by TEXT NOT NULL DEFAULT 'bot',
                    created_at TEXT NOT NULL,
                    last_modified TEXT NOT NULL
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conditions_symbol ON conditions(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conditions_enabled ON conditions(enabled)')

            # TABLE: price_cache
            # Stores last known price for each symbol (for rolling averages, etc.)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_cache (
                    symbol TEXT PRIMARY KEY,
                    last_price REAL,
                    day_open REAL,
                    day_high REAL,
                    day_low REAL,
                    volume INTEGER,
                    fetched_at TEXT NOT NULL
                )
            ''')

            # TABLE: cooldown_state
            # Persists cooldown timers across restarts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cooldown_state (
                    alert_id TEXT PRIMARY KEY,
                    last_fired_at TEXT NOT NULL
                )
            ''')

            # TABLE: daily_price_history
            # Stores 200+ days of OHLC data for EMA calculations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    ema_20 REAL,
                    ema_50 REAL,
                    ema_100 REAL,
                    ema_150 REAL,
                    ema_200 REAL,
                    is_consolidated INTEGER DEFAULT 0,
                    consolidation_days INTEGER DEFAULT 0,
                    fetched_at TEXT NOT NULL,
                    UNIQUE(symbol, date)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_price_symbol_date ON daily_price_history(symbol, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_price_symbol ON daily_price_history(symbol)')

            # TABLE: consolidation_state
            # Tracks current consolidation period per symbol (for EMA alerts)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consolidation_state (
                    symbol TEXT PRIMARY KEY,
                    consecutive_days INTEGER DEFAULT 0,
                    start_date TEXT,
                    range_high REAL,
                    range_low REAL,
                    narrow_range_percent REAL DEFAULT 5.0,
                    last_checked TEXT NOT NULL
                )
            ''')

            # TABLE: engine_state
            # Persists engine state for crash recovery (last check time, alerts fired today, etc.)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS engine_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')

            # TABLE: metrics
            # Records per-cycle metrics for dashboard and reporting
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_at TEXT NOT NULL,
                    alerts_fired INTEGER NOT NULL DEFAULT 0,
                    symbols_checked INTEGER NOT NULL DEFAULT 0,
                    elapsed_seconds REAL NOT NULL DEFAULT 0,
                    success INTEGER NOT NULL DEFAULT 1,
                    error_details TEXT
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_cycle_at ON metrics(cycle_at)')

            self.connection.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            error_msg = f"Failed to create tables: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_connection(self):
        """Get database connection."""
        if not self.connection:
            raise DatabaseError("Database not initialized")
        return self.connection

    def execute_query(self, query: str, params: tuple = ()):
        """Execute a query that returns results."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            error_msg = f"Query execution failed: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def execute_update(self, query: str, params: tuple = ()):
        """Execute a query that modifies data."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            self.connection.rollback()
            error_msg = f"Update failed: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


# Create singleton instance
db = Database()
