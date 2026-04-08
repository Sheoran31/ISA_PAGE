"""
Price Between Condition: Alert when stock price is within a range
"""

from typing import Dict, Any
from conditions.base_condition import BaseCondition
from utils.logger import logger


class PriceBetweenCondition(BaseCondition):
    """
    Alert when current price is between lower and upper bounds.

    Parameters:
        lower (float): Lower bound price
        upper (float): Upper bound price
    """

    def evaluate(self, price_data: Dict[str, Any]) -> bool:
        """
        Check if current price is between bounds.

        Args:
            price_data: Dict with 'ltp' (last traded price)

        Returns:
            True if lower <= price <= upper
        """
        try:
            current_price = price_data.get('ltp') or price_data.get('close')
            lower = self.get_parameter('lower')
            upper = self.get_parameter('upper')

            if lower is None or upper is None:
                logger.error(f"Condition {self.alert_id}: Missing 'lower' or 'upper' parameter")
                return False

            result = lower <= current_price <= upper
            if result:
                logger.debug(f"Condition {self.alert_id}: Price {current_price} in range [{lower}, {upper}] ✓")
            return result
        except Exception as e:
            logger.error(f"Condition {self.alert_id}: Evaluation error: {e}")
            return False

    def describe(self) -> str:
        """Return human-readable description."""
        lower = self.get_parameter('lower')
        upper = self.get_parameter('upper')
        return f"{self.name}: {self.symbol} price between ₹{lower} - ₹{upper}"

    def validate_parameters(self) -> bool:
        """Validate required parameters."""
        lower = self.get_parameter('lower')
        upper = self.get_parameter('upper')

        if lower is None or upper is None:
            logger.error(f"Condition {self.alert_id}: Missing 'lower' or 'upper'")
            return False

        if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)):
            logger.error(f"Condition {self.alert_id}: bounds must be numeric")
            return False

        if lower >= upper:
            logger.error(f"Condition {self.alert_id}: lower must be < upper")
            return False

        return True
