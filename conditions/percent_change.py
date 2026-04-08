"""
Percent Change Condition: Alert when stock moves X% from open
"""

from typing import Dict, Any
from conditions.base_condition import BaseCondition
from utils.logger import logger


class PercentChangeCondition(BaseCondition):
    """
    Alert when price moves X% from day's open price.

    Parameters:
        percent (float): Percentage change threshold (e.g., 5.0 for 5%)
        direction (str): 'up' (up only), 'down' (down only), or 'either' (both)
    """

    def evaluate(self, price_data: Dict[str, Any]) -> bool:
        """
        Check if price has moved X% from open.

        Args:
            price_data: Dict with 'open' and 'ltp' or 'close'

        Returns:
            True if percent change meets threshold
        """
        try:
            current_price = price_data.get('ltp') or price_data.get('close')
            open_price = price_data.get('open')
            percent_threshold = self.get_parameter('percent')
            direction = self.get_parameter('direction', 'either')

            if open_price is None or percent_threshold is None:
                logger.error(f"Condition {self.alert_id}: Missing 'open' price or 'percent'")
                return False

            if open_price == 0:
                return False

            # Calculate percentage change
            pct_change = ((current_price - open_price) / open_price) * 100

            # Check direction
            if direction == 'up':
                result = pct_change >= percent_threshold
            elif direction == 'down':
                result = pct_change <= -percent_threshold
            else:  # 'either'
                result = abs(pct_change) >= percent_threshold

            if result:
                logger.debug(f"Condition {self.alert_id}: Price moved {pct_change:.2f}% (threshold: {percent_threshold}%) ✓")
            return result
        except Exception as e:
            logger.error(f"Condition {self.alert_id}: Evaluation error: {e}")
            return False

    def describe(self) -> str:
        """Return human-readable description."""
        percent = self.get_parameter('percent')
        direction = self.get_parameter('direction', 'either')
        direction_text = f"{direction}" if direction != 'either' else 'either direction'
        return f"{self.name}: {self.symbol} moved {percent}% ({direction_text})"

    def validate_parameters(self) -> bool:
        """Validate required parameters."""
        percent = self.get_parameter('percent')
        direction = self.get_parameter('direction')

        if percent is None:
            logger.error(f"Condition {self.alert_id}: Missing 'percent'")
            return False

        if not isinstance(percent, (int, float)):
            logger.error(f"Condition {self.alert_id}: 'percent' must be numeric")
            return False

        if direction not in ['up', 'down', 'either']:
            logger.error(f"Condition {self.alert_id}: 'direction' must be 'up', 'down', or 'either'")
            return False

        return True
