"""
Abstract base class for all condition types.
Every condition must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseCondition(ABC):
    """
    Abstract base class for all alert conditions.

    Every condition type (price_above, ema_consolidation, etc.)
    inherits from this and implements the evaluate() method.
    """

    def __init__(self, alert_id: str, name: str, symbol: str, parameters: Dict[str, Any]):
        """
        Initialize condition.

        Args:
            alert_id: Unique ID for this alert
            name: Human-readable name
            symbol: Stock symbol (e.g., 'NSE:TCS')
            parameters: Condition-specific parameters dict
        """
        self.alert_id = alert_id
        self.name = name
        self.symbol = symbol
        self.parameters = parameters

    @abstractmethod
    def evaluate(self, price_data: Dict[str, Any]) -> bool:
        """
        Evaluate if condition is triggered.

        Args:
            price_data: Dict containing current price data
                {
                    'ltp': 3512.40,                    # Last traded price
                    'open': 3480.00,
                    'high': 3520.00,
                    'low': 3475.00,
                    'close': 3512.40,
                    'volume': 1200000,
                    'timestamp': '2026-04-08 15:30:00'
                }

        Returns:
            True if condition triggers, False otherwise
        """
        pass

    def describe(self) -> str:
        """
        Return human-readable description of condition.

        Returns:
            String describing the condition
        """
        return f"{self.name}: {self.__class__.__name__}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize condition to dictionary for storage.

        Returns:
            Dictionary representation
        """
        return {
            'alert_id': self.alert_id,
            'name': self.name,
            'symbol': self.symbol,
            'type': self.__class__.__name__,
            'parameters': self.parameters
        }

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a parameter value with optional default."""
        return self.parameters.get(key, default)

    def validate_parameters(self) -> bool:
        """
        Validate that all required parameters are present.
        Override in subclasses if needed.

        Returns:
            True if valid, False otherwise
        """
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.alert_id}, symbol={self.symbol})"
