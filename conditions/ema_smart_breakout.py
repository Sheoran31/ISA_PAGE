"""
Smart EMA Consolidation Breakout/Breakdown
Detects when ALL EMAs are naturally tight together (not using fixed %)
Then alerts on breakout/breakdown
"""

from typing import Dict, Any, List
from conditions.base_condition import BaseCondition
from fetcher.ema_calculator import EMACalculator
from storage.price_history_repository import PriceHistoryRepository
from utils.logger import logger


class EMASmartBreakout(BaseCondition):
    """
    Smart alert when EMAs are tight together and price breaks out/down.

    How it works:
    1. Check if all EMAs (20,50,100,150,200) are CLOSE TO EACH OTHER
       - Not using fixed %, but natural clustering
    2. Monitor when price breaks:
       - ABOVE highest EMA → BUY ALERT
       - BELOW lowest EMA → SELL ALERT
    """

    def evaluate(self, price_data: Dict[str, Any]) -> bool:
        """
        Evaluate if price breaks above/below all EMAs.

        Simple logic:
        - Alert when price closes ABOVE all EMAs (BUY)
        - Alert when price closes BELOW all EMAs (SELL)

        Args:
            price_data: Current price data with symbol, close, date

        Returns:
            True if breakout/breakdown detected
        """
        try:
            import yfinance as yf
            import pandas as pd
            import numpy as np

            symbol = self.parameters.get('symbol') or price_data.get('symbol')
            current_close = price_data.get('ltp') or price_data.get('close')

            if not symbol or current_close is None:
                logger.error(f"Condition {self.alert_id}: Missing symbol or close price")
                return False

            # Fetch historical data directly from yfinance
            df = yf.download(symbol, period='1y', progress=False)
            if df.empty or len(df) < 50:
                logger.warning(f"Not enough data for {symbol}")
                return False

            # Handle MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Extract closes for EMA calculation
            closes = np.array(df['Close']).flatten().tolist()

            # Calculate EMAs
            ema_periods = self.get_parameter('ema_periods', [20, 50, 100, 150, 200])
            ema_dict = EMACalculator.calculate_multiple_emas(closes, ema_periods)

            # Get today's EMA values
            today_emas = {}
            for period in ema_periods:
                ema_list = ema_dict[period]
                if ema_list and ema_list[-1] is not None:
                    today_emas[period] = ema_list[-1]

            if not today_emas:
                logger.error(f"Condition {self.alert_id}: Could not calculate EMAs")
                return False

            # ===== SIMPLE LOGIC: Check if price breaks above/below ALL EMAs =====
            ema_values = list(today_emas.values())
            highest_ema = max(ema_values)
            lowest_ema = min(ema_values)
            ema_spread = highest_ema - lowest_ema
            ema_avg = sum(ema_values) / len(ema_values)
            spread_percent = (ema_spread / ema_avg) * 100

            # Check breakout and breakdown
            is_breakout = current_close > highest_ema  # Price ABOVE all EMAs
            is_breakdown = current_close < lowest_ema  # Price BELOW all EMAs

            # Trigger on any breakout or breakdown (no consolidation requirement)
            trigger = is_breakout or is_breakdown

            if trigger:
                signal_type = "BREAKOUT ⬆️" if is_breakout else "BREAKDOWN ⬇️"
                logger.info(f"✅ {signal_type} triggered for {symbol}:")
                logger.info(f"   Close: {current_close}")
                logger.info(f"   EMA Spread: {spread_percent:.2f}%")
                logger.info(f"   EMA Range: {lowest_ema:.2f} - {highest_ema:.2f}")

                # Store signal info in price_data for alert message
                price_data['ema_signal'] = {
                    'signal_type': signal_type,
                    'is_breakout': is_breakout,
                    'is_breakdown': is_breakdown,
                    'ema_spread_percent': spread_percent,
                    'ema_high': highest_ema,
                    'ema_low': lowest_ema,
                    'today_emas': today_emas
                }

            return trigger

        except Exception as e:
            logger.error(f"Condition {self.alert_id}: Evaluation error: {e}")
            return False

    def describe(self) -> str:
        """Return human-readable description."""
        return f"{self.name}: Smart EMA breakout/breakdown (tight EMAs + price move)"

    def validate_parameters(self) -> bool:
        """Validate required parameters."""
        return True
