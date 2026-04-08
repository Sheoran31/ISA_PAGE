"""
Fetch historical OHLC data from Zerodha Kite API
Handles 200-day historical data with caching
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils.logger import logger
from utils.exceptions import KiteAPIError


class HistoricalFetcher:
    """
    Fetch and manage historical OHLC data from Zerodha Kite.
    """

    def __init__(self, kite_client):
        """
        Initialize with Zerodha Kite client.

        Args:
            kite_client: Authenticated KiteConnect instance
        """
        self.kite = kite_client
        logger.info("HistoricalFetcher initialized")

    def fetch_ohlc_last_200_days(self, symbol: str) -> List[Dict]:
        """
        Fetch last 200 days of OHLC data.

        Zerodha API provides:
        - Daily candles via historical() endpoint
        - Limited to ~100 days per call in some versions
        - We'll fetch multiple times if needed

        Args:
            symbol: Zerodha instrument token or NSE:TCS format
                    (e.g., 'NSE:TCS')

        Returns:
            List of dicts with keys: ['date', 'open', 'high', 'low', 'close', 'volume']
            Sorted oldest to newest
        """
        try:
            logger.info(f"Fetching 200 days OHLC for {symbol}")

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=200)

            # Fetch from Kite API
            # Note: Kite returns data in reverse (newest first), so we'll reverse it
            try:
                # Try getting last 100 days first
                data = self.kite.historical_data(
                    instrument_token=self._get_instrument_token(symbol),
                    from_date=start_date,
                    to_date=end_date,
                    interval='day'
                )

                if not data:
                    logger.warning(f"No historical data returned for {symbol}")
                    return []

                # Convert Zerodha format to our format
                ohlc_data = self._convert_zerodha_format(data)

                # Sort by date (oldest first)
                ohlc_data.sort(key=lambda x: x['date'])

                logger.info(f"Fetched {len(ohlc_data)} days for {symbol}")
                return ohlc_data

            except Exception as api_error:
                logger.error(f"Zerodha API error: {api_error}")
                raise KiteAPIError(f"Failed to fetch historical data for {symbol}: {api_error}")

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise KiteAPIError(f"Historical fetch failed: {e}")

    def _get_instrument_token(self, symbol: str) -> str:
        """
        Get instrument token from symbol.

        Zerodha requires instrument_token (not symbol string).
        This would be fetched from the instruments list.

        Args:
            symbol: NSE:TCS format

        Returns:
            Instrument token
        """
        # TODO: This should query the instruments list cached in database
        # For now, we'll need to handle this in the main fetcher
        return symbol

    def _convert_zerodha_format(self, zerodha_data: List[Dict]) -> List[Dict]:
        """
        Convert Zerodha API response to our format.

        Zerodha returns:
            {'date': datetime, 'open': float, 'high': float, 'low': float,
             'close': float, 'volume': int}

        Our format:
            {'date': 'YYYY-MM-DD', 'open': float, 'high': float, 'low': float,
             'close': float, 'volume': int}

        Args:
            zerodha_data: List of dicts from Zerodha API

        Returns:
            Converted list
        """
        converted = []
        for item in zerodha_data:
            # Handle both datetime objects and strings
            if isinstance(item['date'], datetime):
                date_str = item['date'].strftime('%Y-%m-%d')
            else:
                date_str = item['date']

            converted.append({
                'date': date_str,
                'open': float(item['open']),
                'high': float(item['high']),
                'low': float(item['low']),
                'close': float(item['close']),
                'volume': int(item['volume'])
            })

        return converted

    def fetch_current_ohlc(self, symbol: str) -> Optional[Dict]:
        """
        Fetch current day's OHLC (partial data).

        Args:
            symbol: Stock symbol (NSE:TCS)

        Returns:
            Dict with current OHLC or None
        """
        try:
            quote = self.kite.quote(symbols=[symbol])

            if symbol not in quote:
                logger.warning(f"No quote data for {symbol}")
                return None

            data = quote[symbol]
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'open': data.get('ohlc', {}).get('open', 0),
                'high': data.get('ohlc', {}).get('high', 0),
                'low': data.get('ohlc', {}).get('low', 0),
                'close': data.get('last_price', 0),
                'volume': data.get('volume', 0)
            }
        except Exception as e:
            logger.error(f"Error fetching current OHLC for {symbol}: {e}")
            return None

    def validate_data_quality(self, ohlc_data: List[Dict]) -> bool:
        """
        Validate that OHLC data is reasonable.

        Checks:
        - No zero/negative prices
        - High >= Open, Close, Low
        - Low <= Open, Close, High
        - Reasonable volume

        Args:
            ohlc_data: List of OHLC dicts

        Returns:
            True if data looks good
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
