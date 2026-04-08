"""
Price Fetcher: Fetch real-time and historical prices from Yahoo Finance.
Handles batch fetching, caching, and data normalization.
"""

from typing import Dict, List, Optional
from datetime import datetime

from fetcher.yfinance_client import get_yfinance_client
from storage.price_history_repository import PriceHistoryRepository
from utils.logger import logger
from utils.exceptions import KiteAPIError


class PriceFetcher:
    """
    Fetch prices from Yahoo Finance (yfinance).

    Responsibilities:
    - Fetch real-time LTP (last traded price)
    - Fetch OHLCV (Open, High, Low, Close, Volume)
    - Batch fetch multiple symbols
    - Cache results
    - Normalize data format
    """

    def __init__(self):
        """Initialize price fetcher."""
        self.yfinance_client = get_yfinance_client()
        logger.info("PriceFetcher initialized")

    def fetch_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch current Last Traded Price (LTP) for multiple symbols.

        Args:
            symbols: List of symbols (e.g., ['TCS.NS', 'RELIANCE.NS'])

        Returns:
            Dict mapping symbol -> price
        """
        try:
            if not symbols:
                return {}

            ltp_dict = {}
            for symbol in symbols:
                price = self.yfinance_client.get_ltp(symbol)
                if price is not None:
                    ltp_dict[symbol] = price
                else:
                    logger.warning(f"No LTP data for {symbol}")

            logger.debug(f"Fetched LTP for {len(ltp_dict)}/{len(symbols)} symbols")
            return ltp_dict
        except Exception as e:
            logger.error(f"Failed to fetch LTP: {e}")
            raise KiteAPIError(f"LTP fetch failed: {e}")

    def fetch_ohlcv(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch OHLCV data for symbols.

        Args:
            symbols: List of symbols

        Returns:
            Dict mapping symbol -> OHLCV data
        """
        try:
            if not symbols:
                return {}

            ohlcv_dict = self.yfinance_client.get_batch_prices(symbols)
            logger.debug(f"Fetched OHLCV for {len(ohlcv_dict)}/{len(symbols)} symbols")
            return ohlcv_dict
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV: {e}")
            raise KiteAPIError(f"OHLCV fetch failed: {e}")

    def fetch_historical_for_ema(self, symbol: str) -> Optional[List[Dict]]:
        """
        Fetch historical data for EMA calculation.

        Args:
            symbol: Stock symbol

        Returns:
            List of OHLC candles (last 200 days)
        """
        try:
            logger.info(f"Fetching 200-day history for {symbol}")

            # Fetch from yfinance
            ohlc_data = self.yfinance_client.get_historical_data(symbol, days=200)

            if not ohlc_data:
                logger.warning(f"No historical data for {symbol}")
                return None

            # Validate quality
            if not self.yfinance_client.validate_data_quality(ohlc_data):
                logger.warning(f"Data quality issues for {symbol}")
                return None

            # Store in database
            count = PriceHistoryRepository.insert_or_update_ohlc(symbol, ohlc_data)
            logger.info(f"Stored {count} candles for {symbol}")

            return ohlc_data
        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            return None

    def get_current_price_data(self, symbol: str) -> Optional[Dict]:
        """
        Get complete current price data for a symbol.

        Returns dict with: open, high, low, close, ltp, volume, timestamp

        Args:
            symbol: Stock symbol

        Returns:
            Price data dict or None
        """
        try:
            return self.yfinance_client.get_ohlcv(symbol)
        except Exception as e:
            logger.error(f"Failed to get price data for {symbol}: {e}")
            return None

    def fetch_batch_prices(self, symbols: List[str], batch_size: int = 100) -> Dict[str, Dict]:
        """
        Fetch prices for many symbols in batches.

        Args:
            symbols: List of symbols
            batch_size: Max symbols per API call (yfinance has no hard limit, batching is optional)

        Returns:
            Dict mapping symbol -> price data
        """
        try:
            all_data = {}

            # Process in batches for rate limiting
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                logger.debug(f"Fetching batch {i//batch_size + 1}: {len(batch)} symbols")

                try:
                    batch_data = self.yfinance_client.get_batch_prices(batch)
                    all_data.update(batch_data)
                except Exception as batch_error:
                    logger.warning(f"Batch fetch failed: {batch_error}")
                    continue

            logger.info(f"Fetched prices for {len(all_data)}/{len(symbols)} symbols")
            return all_data
        except Exception as e:
            logger.error(f"Batch fetch failed: {e}")
            raise KiteAPIError(f"Batch fetch failed: {e}")

    def is_ready(self) -> bool:
        """Check if price fetcher is ready to use."""
        return self.yfinance_client.is_authenticated()


# Global instance
_price_fetcher_instance = None


def get_price_fetcher() -> PriceFetcher:
    """Get or create global PriceFetcher instance."""
    global _price_fetcher_instance
    if _price_fetcher_instance is None:
        _price_fetcher_instance = PriceFetcher()
    return _price_fetcher_instance
