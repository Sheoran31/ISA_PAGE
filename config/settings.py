"""
Configuration settings loaded from .env file.
This is the single source of truth for all app configuration.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

from utils.exceptions import ConfigError
from utils.logger import logger

# Load .env file from project root
ENV_FILE = Path(__file__).parent.parent / '.env'
load_dotenv(ENV_FILE)

logger.info(f"Loading configuration from {ENV_FILE}")


def get_required(key: str) -> str:
    """Get required environment variable, fail fast if missing."""
    value = os.getenv(key)
    if not value:
        error_msg = f"Required environment variable '{key}' is not set. Check .env file."
        logger.error(error_msg)
        raise ConfigError(error_msg)
    return value


def get_optional(key: str, default: str = None) -> str:
    """Get optional environment variable with default."""
    return os.getenv(key, default)


# ========== DATA PROVIDER (YAHOO FINANCE) ==========
# YFinance doesn't require any authentication
logger.info("Using Yahoo Finance for market data (no authentication required)")

# ========== TELEGRAM BOT ==========
try:
    TELEGRAM_BOT_TOKEN = get_required('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = get_required('TELEGRAM_CHAT_ID')
except ConfigError:
    TELEGRAM_BOT_TOKEN = None
    TELEGRAM_CHAT_ID = None
    logger.warning("Telegram credentials not yet configured.")

TELEGRAM_EXTRA_CHAT_IDS = get_optional('TELEGRAM_EXTRA_CHAT_IDS', '')

# ========== ZERODHA API (OPTIONAL) ==========
ZERODHA_ENABLED = get_optional('ZERODHA_ENABLED', 'false').lower() == 'true'
ZERODHA_API_KEY = get_optional('ZERODHA_API_KEY')
ZERODHA_ACCESS_TOKEN = get_optional('ZERODHA_ACCESS_TOKEN')
ZERODHA_USER_ID = get_optional('ZERODHA_USER_ID')

# ========== SCHEDULER SETTINGS ==========
CHECK_INTERVAL_MINUTES = int(get_optional('CHECK_INTERVAL_MINUTES', '2'))
MARKET_HOURS_ONLY = get_optional('MARKET_HOURS_ONLY', 'true').lower() == 'true'

# ========== ALERT BEHAVIOR ==========
DEFAULT_COOLDOWN_MINUTES = int(get_optional('DEFAULT_COOLDOWN_MINUTES', '30'))
MAX_ALERTS_PER_CYCLE = int(get_optional('MAX_ALERTS_PER_CYCLE', '10'))
MAX_ALERTS_PER_SYMBOL_PER_DAY = int(get_optional('MAX_ALERTS_PER_SYMBOL_PER_DAY', '5'))

# ========== REAL-TIME TRIGGER SETTINGS ==========
REALTIME_INTERVAL_SECONDS = int(get_optional('REALTIME_INTERVAL_SECONDS', '30'))
REALTIME_CONDITION_TYPES = get_optional('REALTIME_CONDITION_TYPES',
                                         'price_above,price_below,percent_change,volume_spike').split(',')

# ========== STORAGE ==========
DATABASE_PATH = get_optional('DATABASE_PATH', 'data/alerts.db')

# ========== LOGGING ==========
LOG_LEVEL = get_optional('LOG_LEVEL', 'INFO').upper()
LOG_FILE = get_optional('LOG_FILE', 'logs/app.log')
LOG_MAX_SIZE_MB = int(get_optional('LOG_MAX_SIZE_MB', '10'))

# ========== DISPLAY SETTINGS ==========
TIMEZONE = 'Asia/Kolkata'  # IST

logger.info("Configuration loaded successfully")
logger.debug(f"Check interval: {CHECK_INTERVAL_MINUTES} minutes")
logger.debug(f"Market hours only: {MARKET_HOURS_ONLY}")
logger.debug(f"Default cooldown: {DEFAULT_COOLDOWN_MINUTES} minutes")
