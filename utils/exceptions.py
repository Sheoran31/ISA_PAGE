"""
Custom exceptions for the stock alert system.
Each exception is specific, making error handling cleaner.
"""


class StockAlertError(Exception):
    """Base exception for all stock alert system errors."""
    pass


class KiteAPIError(StockAlertError):
    """Raised when Zerodha Kite API calls fail."""
    pass


class SymbolNotFoundError(StockAlertError):
    """Raised when a stock symbol doesn't exist in NSE/BSE."""
    pass


class SymbolValidationError(StockAlertError):
    """Raised when symbol validation fails."""
    pass


class TelegramSendError(StockAlertError):
    """Raised when Telegram message fails to send."""
    pass


class InvalidConditionError(StockAlertError):
    """Raised when condition JSON is malformed or invalid."""
    pass


class MarketClosedError(StockAlertError):
    """Raised when attempting to fetch prices outside market hours."""
    pass


class DatabaseError(StockAlertError):
    """Raised when database operations fail."""
    pass


class ConfigError(StockAlertError):
    """Raised when required configuration is missing or invalid."""
    pass


class AccessTokenError(StockAlertError):
    """Raised when Kite access token is missing or expired."""
    pass
