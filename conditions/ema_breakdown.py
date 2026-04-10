"""
EMA Consolidation Breakdown Condition
Detects when price breaks DOWN below consolidation period (all EMAs in narrow range)
"""

from typing import Dict, Any, List
from conditions.base_condition import BaseCondition
from fetcher.ema_calculator import EMACalculator
from engine.consolidation_tracker import ConsolidationTracker
from storage.price_history_repository import PriceHistoryRepository
from utils.logger import logger


class EMAConsolidationBreakdown(BaseCondition):
    """
    Alert when price breaks DOWN below EMA in a consolidation period.

    How it works:
    1. Track last 3-6 days of closing prices
    2. Check if all 5 EMAs (20,50,100,150,200) are within 5% range
    3. If 3+ consecutive days consolidated, mark as consolidation active
    4. When today's close < any EMA low, trigger breakdown alert

    Parameters:
        ema_periods: [20, 50, 100, 150, 200]
        narrow_range_percent: 5.0 (consolidation tolerance)
        min_consolidation_days: 3 (days to confirm consolidation)
        max_consolidation_days: 30 (stop tracking after this)
        breakdown_emas: [20, 50, 100, 150, 200] (which EMAs trigger alert)
    """

    def evaluate(self, price_data: Dict[str, Any]) -> bool:
        """
        Evaluate if EMA breakdown is occurring.

        Args:
            price_data: Current price data with symbol, close, date

        Returns:
            True if breakdown detected (close < any EMA after 3+ day consolidation)
        """
        try:
            symbol = self.parameters.get('symbol') or price_data.get('symbol')
            current_close = price_data.get('ltp') or price_data.get('close')

            if not symbol or current_close is None:
                logger.error(f"Condition {self.alert_id}: Missing symbol or close price")
                return False

            # Get historical data with EMAs
            candles = PriceHistoryRepository.get_last_n_candles(symbol, n=200)
            if len(candles) < 50:
                logger.warning(f"Not enough data for {symbol}: {len(candles)} candles")
                return False

            # Extract closes for EMA calculation
            closes = [c['close'] for c in candles if c['close'] is not None]

            # Calculate EMAs
            ema_periods = self.get_parameter('ema_periods', [20, 50, 100, 150, 200])
            ema_dict = EMACalculator.calculate_multiple_emas(closes, ema_periods)

            # Get last EMA values (today)
            today_emas = {}
            for period in ema_periods:
                ema_list = ema_dict[period]
                if ema_list and ema_list[-1] is not None:
                    today_emas[period] = ema_list[-1]

            if not today_emas:
                logger.error(f"Condition {self.alert_id}: Could not calculate EMAs")
                return False

            # Check if today's price is BELOW the LOWEST EMA (breakdown)
            # Get the lowest EMA value
            min_ema = min(today_emas.values()) if today_emas else None

            if not min_ema or current_close >= min_ema:
                # Not below the lowest EMA
                return False

            # Check consolidation status
            narrow_range_percent = self.get_parameter('narrow_range_percent', 5.0)
            is_consolidated = EMACalculator.is_consolidated(today_emas, narrow_range_percent)

            consolidation_state = ConsolidationTracker.get_consolidation_state(symbol)
            consolidation_days = consolidation_state['consecutive_days'] if consolidation_state else 0
            min_days = self.get_parameter('min_consolidation_days', 3)

            # Check previous day consolidation
            if len(candles) >= 2:
                yesterday = candles[-2]
                yesterday_emas = {
                    20: yesterday.get('ema_20'),
                    50: yesterday.get('ema_50'),
                    100: yesterday.get('ema_100'),
                    150: yesterday.get('ema_150'),
                    200: yesterday.get('ema_200')
                }

                # Remove None values
                yesterday_emas = {k: v for k, v in yesterday_emas.items() if v is not None}

                was_consolidated = (yesterday.get('is_consolidated') == 1 or
                                   EMACalculator.is_consolidated(yesterday_emas, narrow_range_percent))
            else:
                was_consolidated = False

            # Trigger condition:
            # Close is below lowest EMA AND (was consolidated OR is actively consolidating)
            trigger = (current_close < min_ema) and (was_consolidated or consolidation_days >= min_days)

            if trigger:
                logger.info(f"✓ EMA Breakdown triggered for {symbol}:")
                logger.info(f"  Close: {current_close}, Below EMA: {min_ema}")
                logger.info(f"  Was consolidated: {was_consolidated}, Days: {consolidation_days}")

                # Store breakdown info in price_data for alert message
                price_data['ema_breakdown'] = {
                    'lowest_ema': min_ema,
                    'today_emas': today_emas,
                    'consolidation_days': consolidation_days,
                    'consolidation_range': EMACalculator.get_consolidation_range(today_emas)
                }

            # Update consolidation state
            range_high, range_low = EMACalculator.get_consolidation_range(today_emas)
            ConsolidationTracker.update_consolidation(
                symbol,
                is_consolidated=is_consolidated,
                range_high=range_high,
                range_low=range_low,
                narrow_range_percent=narrow_range_percent
            )

            return trigger

        except Exception as e:
            logger.error(f"Condition {self.alert_id}: Evaluation error: {e}")
            return False

    def describe(self) -> str:
        """Return human-readable description."""
        narrow = self.get_parameter('narrow_range_percent', 5.0)
        min_days = self.get_parameter('min_consolidation_days', 3)
        return f"{self.name}: EMA consolidation breakdown (±{narrow}%, {min_days}+ days)"

    def validate_parameters(self) -> bool:
        """Validate required parameters."""
        narrow = self.get_parameter('narrow_range_percent')
        min_days = self.get_parameter('min_consolidation_days')

        if narrow is None or min_days is None:
            logger.error(f"Condition {self.alert_id}: Missing EMA parameters")
            return False

        if not isinstance(narrow, (int, float)) or narrow <= 0:
            logger.error(f"Condition {self.alert_id}: Invalid narrow_range_percent")
            return False

        if not isinstance(min_days, int) or min_days < 1:
            logger.error(f"Condition {self.alert_id}: Invalid min_consolidation_days")
            return False

        return True
