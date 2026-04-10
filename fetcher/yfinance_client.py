"""
Yahoo Finance Client
Handles price fetching using yfinance (no authentication needed).
"""

import yfinance as yf
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.logger import logger
from utils.exceptions import KiteAPIError


class YFinanceClient:
    """
    Wrapper around yfinance for consistent API.

    Responsibilities:
    - Fetch real-time prices
    - Fetch historical data
    - Handle symbol normalization
    """

    def __init__(self):
        """Initialize YFinance client."""
        self._initialized = True
        logger.info("YFinanceClient initialized")

    def authenticate(self) -> bool:
        """
        YFinance doesn't need authentication.

        Returns:
            Always True
        """
        logger.info("✅ YFinance - No authentication needed")
        return True

    def is_authenticated(self) -> bool:
        """Check if client is ready."""
        return self._initialized

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def get_ltp(self, symbol: str) -> Optional[float]:
        """
        Get Last Traded Price for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS', 'TCS.NS')

        Returns:
            Current price or None
        """
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')

        if data.empty:
            logger.warning(f"No data for {symbol}")
            return None

        # Return the close price
        return float(data['Close'].iloc[-1])

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def get_ohlcv(self, symbol: str) -> Optional[Dict]:
        """
        Get OHLCV data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dict with OHLCV data or None
        """
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')

        if data.empty:
            logger.warning(f"No data for {symbol}")
            return None

        latest = data.iloc[-1]

        return {
            'symbol': symbol,
            'open': float(latest['Open']),
            'high': float(latest['High']),
            'low': float(latest['Low']),
            'close': float(latest['Close']),
            'ltp': float(latest['Close']),
            'volume': int(latest['Volume']),
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_batch_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch OHLCV for multiple symbols.

        Args:
            symbols: List of symbols

        Returns:
            Dict mapping symbol -> OHLCV data
        """
        result = {}

        for symbol in symbols:
            try:
                ohlcv = self.get_ohlcv(symbol)
                if ohlcv:
                    result[symbol] = ohlcv
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                continue

        logger.debug(f"Fetched prices for {len(result)}/{len(symbols)} symbols")
        return result

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def get_historical_data(self, symbol: str, days: int = 200) -> Optional[List[Dict]]:
        """
        Get historical OHLCV data.

        Args:
            symbol: Stock symbol
            days: Number of days of historical data

        Returns:
            List of OHLC dicts or None
        """
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=f'{days}d')

        if data.empty:
            logger.warning(f"No historical data for {symbol}")
            return None

        # Convert to list of dicts
        ohlc_list = []
        for date, row in data.iterrows():
            ohlc_list.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })

        logger.info(f"Fetched {len(ohlc_list)} days of data for {symbol}")
        return ohlc_list

    def validate_data_quality(self, ohlc_data: List[Dict]) -> bool:
        """
        Validate OHLC data quality.

        Args:
            ohlc_data: List of OHLC dicts

        Returns:
            True if data quality is good
        """
        if not ohlc_data:
            return False

        issues = 0
        for item in ohlc_data:
            o, h, l, c = item['open'], item['high'], item['low'], item['close']

            # Check if prices are positive
            if o <= 0 or h <= 0 or l <= 0 or c <= 0:
                issues += 1
                continue

            # Check OHLC relationships
            if not (l <= o <= h and l <= c <= h):
                issues += 1

        if issues > 0:
            logger.warning(f"Data quality issues in {len(ohlc_data)} candles: {issues} anomalies")
            return issues < len(ohlc_data) * 0.1  # Allow <10% bad data

        logger.info(f"Data quality check passed: {len(ohlc_data)} candles")
        return True


# Global instance
_yfinance_client_instance = None


def get_yfinance_client() -> YFinanceClient:
    """
    Get or create global YFinanceClient instance (singleton).

    Returns:
        YFinanceClient instance
    """
    global _yfinance_client_instance
    if _yfinance_client_instance is None:
        _yfinance_client_instance = YFinanceClient()
    return _yfinance_client_instance
