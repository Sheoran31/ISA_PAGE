"""
Condition Type Registry
Maps condition type strings to their corresponding classes.
This allows dynamic instantiation of conditions from JSON configuration.
"""

from typing import Dict, Type
from conditions.base_condition import BaseCondition
from conditions.price_above import PriceAboveCondition
from conditions.price_below import PriceBelowCondition
from conditions.price_between import PriceBetweenCondition
from conditions.percent_change import PercentChangeCondition
from conditions.volume_spike import VolumeSpikeCondition
from conditions.ema_consolidation import EMAConsolidationBreakout
from conditions.ema_breakdown import EMAConsolidationBreakdown
from conditions.ema_smart_breakout import EMASmartBreakout
from utils.logger import logger
from utils.exceptions import InvalidConditionError


class ConditionRegistry:
    """
    Registry of all available condition types.

    Usage:
        ConditionRegistry.register('price_above', PriceAboveCondition)
        condition_class = ConditionRegistry.get('price_above')
        instance = condition_class(alert_id, name, symbol, parameters)
    """

    # Registry mapping: type_string -> condition_class
    _registry: Dict[str, Type[BaseCondition]] = {}

    @staticmethod
    def register(type_name: str, condition_class: Type[BaseCondition]) -> None:
        """
        Register a condition type.

        Args:
            type_name: String identifier (e.g., 'price_above')
            condition_class: Class that inherits from BaseCondition
        """
        ConditionRegistry._registry[type_name] = condition_class
        logger.debug(f"Registered condition type: {type_name} -> {condition_class.__name__}")

    @staticmethod
    def get(type_name: str) -> Type[BaseCondition]:
        """
        Get a condition class by type name.

        Args:
            type_name: String identifier

        Returns:
            Condition class

        Raises:
            InvalidConditionError if type not found
        """
        if type_name not in ConditionRegistry._registry:
            available = ', '.join(ConditionRegistry._registry.keys())
            error_msg = f"Unknown condition type: '{type_name}'. Available: {available}"
            logger.error(error_msg)
            raise InvalidConditionError(error_msg)

        return ConditionRegistry._registry[type_name]

    @staticmethod
    def is_registered(type_name: str) -> bool:
        """Check if a condition type is registered."""
        return type_name in ConditionRegistry._registry

    @staticmethod
    def list_all() -> Dict[str, Type[BaseCondition]]:
        """Get all registered condition types."""
        return dict(ConditionRegistry._registry)

    @staticmethod
    def create_condition(
        type_name: str,
        alert_id: str,
        name: str,
        symbol: str,
        parameters: Dict
    ) -> BaseCondition:
        """
        Create a condition instance from type name.

        Args:
            type_name: Condition type (e.g., 'price_above')
            alert_id: Unique alert ID
            name: Human-readable name
            symbol: Stock symbol
            parameters: Condition parameters

        Returns:
            Instantiated condition object

        Raises:
            InvalidConditionError if type not found
        """
        try:
            condition_class = ConditionRegistry.get(type_name)
            instance = condition_class(alert_id, name, symbol, parameters)

            # Validate parameters
            if not instance.validate_parameters():
                raise InvalidConditionError(f"Invalid parameters for {type_name}")

            return instance
        except InvalidConditionError:
            raise
        except Exception as e:
            error_msg = f"Failed to create condition {type_name}: {e}"
            logger.error(error_msg)
            raise InvalidConditionError(error_msg)


# ============================================================
# INITIALIZE REGISTRY WITH ALL CONDITION TYPES
# ============================================================

def initialize_registry() -> None:
    """
    Register all available condition types.
    Call this once at application startup.
    """
    # Basic price conditions
    ConditionRegistry.register('price_above', PriceAboveCondition)
    ConditionRegistry.register('price_below', PriceBelowCondition)
    ConditionRegistry.register('price_between', PriceBetweenCondition)

    # Technical indicator conditions
    ConditionRegistry.register('percent_change', PercentChangeCondition)
    ConditionRegistry.register('volume_spike', VolumeSpikeCondition)

    # Advanced conditions
    ConditionRegistry.register('ema_consolidation', EMAConsolidationBreakout)
    ConditionRegistry.register('ema_breakdown', EMAConsolidationBreakdown)
    ConditionRegistry.register('ema_smart_breakout', EMASmartBreakout)

    logger.info(f"Condition registry initialized with {len(ConditionRegistry.list_all())} types")


# Call on import
initialize_registry()
