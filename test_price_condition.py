#!/usr/bin/env python3
"""
Debug: Test price_above condition directly
"""

import sys
from conditions.registry import ConditionRegistry
from utils.logger import logger

def main():
    logger.info("=" * 80)
    logger.info("TESTING PRICE_ABOVE CONDITION")
    logger.info("=" * 80)

    registry = ConditionRegistry()

    # Create price_above condition with 3500 threshold
    parameters = {'threshold': 3500.0}
    condition = registry.create_condition(
        type_name='price_above',
        alert_id='test_001',
        name='Test Price Above 3500',
        symbol='TCS.NS',
        parameters=parameters
    )

    logger.info(f"\nCondition: Price Above ₹3500")
    logger.info(f"Parameters: {parameters}")
    logger.info("-" * 80)

    # Test cases
    test_cases = [
        {'symbol': 'TCS.NS', 'price': 3200, 'ltp': 3200, 'should_trigger': False},
        {'symbol': 'TCS.NS', 'price': 3500, 'ltp': 3500, 'should_trigger': False},
        {'symbol': 'TCS.NS', 'price': 3501, 'ltp': 3501, 'should_trigger': True},
        {'symbol': 'TCS.NS', 'price': 4000, 'ltp': 4000, 'should_trigger': True},
        {'symbol': 'TCS.NS', 'price': 4246, 'ltp': 4246, 'should_trigger': True},
    ]

    logger.info(f"\n📊 Test Cases:")
    for test in test_cases:
        price_data = {
            'symbol': test['symbol'],
            'open': test['price'],
            'high': test['price'],
            'low': test['price'],
            'close': test['price'],
            'ltp': test['ltp'],
            'volume': 1000000,
            'timestamp': '2026-04-08T16:00:00'
        }

        try:
            triggered, message = condition.evaluate(test['symbol'], price_data)
            expected = test['should_trigger']
            status = "✅" if triggered == expected else "❌"

            logger.info(f"{status} Price: ₹{test['price']:<6} | Triggered: {triggered:<5} | {message}")

        except Exception as e:
            logger.error(f"❌ Price: ₹{test['price']:<6} | Error: {e}")

    logger.info("\n" + "=" * 80)

    return 0

if __name__ == '__main__':
    sys.exit(main())
