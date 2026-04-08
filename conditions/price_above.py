"""
Price Above Condition: Alert when stock price > threshold
"""

from typing import Dict, Any
from conditions.base_condition import BaseCondition
from utils.logger import logger


class PriceAboveCondition(BaseCondition):
    """
    Alert when current price goes above a threshold.

    Parameters:
        threshold (float): Price level to watch
    """

    def evaluate(self, price_data: Dict[str, Any]) -> bool:
        """
        Check if current price is above threshold.

        Args:
            price_data: Dict with 'ltp' (last traded price)

        Returns:
            True if price > threshold
        """
        try:
            current_price = price_data.get('ltp') or price_data.get('close')
            threshold = self.get_parameter('threshold')

            if threshold is None:
                logger.error(f"Condition {self.alert_id}: Missing 'threshold' parameter")
                return False

            result = current_price > threshold
            if result:
                logger.debug(f"Condition {self.alert_id}: Price {current_price} > {threshold} ✓")
            return result
        except Exception as e:
            logger.error(f"Condition {self.alert_id}: Evaluation error: {e}")
            return False

    def describe(self) -> str:
        """Return human-readable description."""
        threshold = self.get_parameter('threshold')
        return f"{self.name}: {self.symbol} price > ₹{threshold}"

    def validate_parameters(self) -> bool:
        """Validate required parameters."""
        threshold = self.get_parameter('threshold')
        if threshold is None:
            logger.error(f"Condition {self.alert_id}: Missing 'threshold'")
            return False
        if not isinstance(threshold, (int, float)):
            logger.error(f"Condition {self.alert_id}: 'threshold' must be numeric")
            return False
        return True
