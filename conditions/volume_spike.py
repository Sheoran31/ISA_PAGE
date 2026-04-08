"""
Volume Spike Condition: Alert when trading volume exceeds threshold
"""

from typing import Dict, Any
from conditions.base_condition import BaseCondition
from utils.logger import logger


class VolumeSpikeCondition(BaseCondition):
    """
    Alert when trading volume exceeds a threshold.

    Parameters:
        volume_threshold (int): Absolute volume number or rolling average multiple
        comparison (str): 'absolute' (vs fixed number) or 'rolling_avg' (vs average)
        rolling_days (int): Days to use for rolling average (default 10)
    """

    def evaluate(self, price_data: Dict[str, Any]) -> bool:
        """
        Check if volume exceeds threshold.

        Args:
            price_data: Dict with 'volume' and optionally 'volume_avg_10'

        Returns:
            True if volume exceeds threshold
        """
        try:
            current_volume = price_data.get('volume')
            comparison = self.get_parameter('comparison', 'absolute')
            volume_threshold = self.get_parameter('volume_threshold')

            if current_volume is None or volume_threshold is None:
                logger.error(f"Condition {self.alert_id}: Missing 'volume' or 'volume_threshold'")
                return False

            if comparison == 'absolute':
                result = current_volume > volume_threshold
                if result:
                    logger.debug(f"Condition {self.alert_id}: Volume {current_volume} > {volume_threshold} ✓")
            else:  # rolling_avg
                volume_avg = price_data.get('volume_avg_10')
                if volume_avg is None:
                    logger.warning(f"Condition {self.alert_id}: No rolling average available, using absolute comparison")
                    result = current_volume > volume_threshold
                else:
                    multiplier = self.get_parameter('rolling_days', 10)
                    threshold_value = volume_avg * multiplier
                    result = current_volume > threshold_value
                    if result:
                        logger.debug(f"Condition {self.alert_id}: Volume {current_volume} > avg*{multiplier} ({threshold_value:.0f}) ✓")

            return result
        except Exception as e:
            logger.error(f"Condition {self.alert_id}: Evaluation error: {e}")
            return False

    def describe(self) -> str:
        """Return human-readable description."""
        volume_threshold = self.get_parameter('volume_threshold')
        comparison = self.get_parameter('comparison', 'absolute')

        if comparison == 'rolling_avg':
            rolling_days = self.get_parameter('rolling_days', 10)
            return f"{self.name}: {self.symbol} volume > {rolling_days}d avg × {volume_threshold}"
        else:
            return f"{self.name}: {self.symbol} volume > {volume_threshold:,.0f}"

    def validate_parameters(self) -> bool:
        """Validate required parameters."""
        volume_threshold = self.get_parameter('volume_threshold')
        comparison = self.get_parameter('comparison')

        if volume_threshold is None:
            logger.error(f"Condition {self.alert_id}: Missing 'volume_threshold'")
            return False

        if not isinstance(volume_threshold, (int, float)):
            logger.error(f"Condition {self.alert_id}: 'volume_threshold' must be numeric")
            return False

        if comparison not in ['absolute', 'rolling_avg']:
            logger.error(f"Condition {self.alert_id}: 'comparison' must be 'absolute' or 'rolling_avg'")
            return False

        return True
