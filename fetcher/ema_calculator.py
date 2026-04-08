"""
EMA (Exponential Moving Average) Calculator
Calculates EMAs for given periods and detects consolidation
"""

from typing import List, Dict, Tuple
from utils.logger import logger


class EMACalculator:
    """
    Calculate Exponential Moving Averages (EMAs) for price data.
    """

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """
        Calculate EMA for a list of prices.

        Formula: EMA = Close × multiplier + EMA(previous) × (1 - multiplier)
                 multiplier = 2 / (period + 1)

        Args:
            prices: List of closing prices (oldest to newest)
            period: EMA period (e.g., 20, 50, 200)

        Returns:
            List of EMA values (same length as prices)
        """
        if len(prices) < period:
            logger.warning(f"Not enough data: {len(prices)} prices for EMA{period}")
            return [None] * len(prices)

        ema_values = [None] * len(prices)
        multiplier = 2 / (period + 1)

        # First EMA = Simple Moving Average of first 'period' values
        sma = sum(prices[:period]) / period
        ema_values[period - 1] = sma

        # Calculate remaining EMAs
        for i in range(period, len(prices)):
            ema = prices[i] * multiplier + ema_values[i - 1] * (1 - multiplier)
            ema_values[i] = ema

        return ema_values

    @staticmethod
    def calculate_multiple_emas(prices: List[float], periods: List[int]) -> Dict[int, List[float]]:
        """
        Calculate multiple EMAs for different periods.

        Args:
            prices: List of closing prices
            periods: List of periods to calculate (e.g., [20, 50, 100, 150, 200])

        Returns:
            Dict mapping period -> list of EMA values
        """
        result = {}
        for period in periods:
            result[period] = EMACalculator.calculate_ema(prices, period)
        return result

    @staticmethod
    def is_consolidated(ema_dict: Dict[int, float], range_percent: float) -> bool:
        """
        Check if all EMAs are within a narrow range.

        Args:
            ema_dict: Dict of period -> current EMA value
                      e.g., {20: 3505.0, 50: 3498.5, 100: 3475.0, ...}
            range_percent: Range in % (e.g., 5.0 for 5%)

        Returns:
            True if all EMAs within range_percent of highest EMA
        """
        if not ema_dict or any(v is None for v in ema_dict.values()):
            return False

        values = [v for v in ema_dict.values() if v is not None]
        if not values:
            return False

        highest = max(values)
        lowest = min(values)

        # Calculate % difference
        pct_diff = ((highest - lowest) / lowest) * 100

        is_cons = pct_diff <= range_percent
        if is_cons:
            logger.debug(f"Consolidated: EMAs within {pct_diff:.2f}% (threshold: {range_percent}%)")
        return is_cons

    @staticmethod
    def get_consolidation_range(ema_dict: Dict[int, float]) -> Tuple[float, float]:
        """
        Get the high and low of all EMAs.

        Args:
            ema_dict: Dict of period -> current EMA value

        Returns:
            Tuple of (highest_ema, lowest_ema)
        """
        values = [v for v in ema_dict.values() if v is not None]
        if not values:
            return None, None
        return max(values), min(values)

    @staticmethod
    def detect_crossover(price: float, ema_dict: Dict[int, float]) -> List[int]:
        """
        Detect which EMAs the price has crossed above.

        Args:
            price: Current price
            ema_dict: Dict of period -> current EMA value
                      e.g., {20: 3505.0, 50: 3498.5, ...}

        Returns:
            List of EMA periods that price is above
        """
        crossed = []
        for period, ema_value in ema_dict.items():
            if ema_value is not None and price > ema_value:
                crossed.append(period)
        return sorted(crossed)

    @staticmethod
    def format_ema_report(symbol: str, close_price: float, ema_dict: Dict[int, float]) -> str:
        """
        Format EMAs into a readable report.

        Args:
            symbol: Stock symbol
            close_price: Current close price
            ema_dict: Dict of period -> EMA value

        Returns:
            Formatted string report
        """
        report = f"\n📊 EMA Analysis for {symbol}\n"
        report += f"Current Close: ₹{close_price:.2f}\n"
        report += "─" * 40 + "\n"

        for period in sorted(ema_dict.keys()):
            ema = ema_dict[period]
            if ema is not None:
                diff = close_price - ema
                diff_pct = (diff / ema) * 100
                direction = "↑" if diff >= 0 else "↓"
                report += f"EMA {period:3d}: ₹{ema:10.2f} {direction} ({diff_pct:+6.2f}%)\n"

        return report
