#!/usr/bin/env python3
"""
Test: Evaluate all conditions against TCS historical data (1 year)
Shows which conditions would have triggered in the past year
"""

import sys
from datetime import datetime
from fetcher.yfinance_client import get_yfinance_client
from storage.price_history_repository import PriceHistoryRepository
from conditions.registry import ConditionRegistry
from config.conditions import load_conditions
from utils.logger import logger

def main():
    logger.info("=" * 80)
    logger.info("TCS.NS - CONDITION BACKTESTING (1 YEAR HISTORY)")
    logger.info("=" * 80)

    symbol = "TCS.NS"
    yfinance = get_yfinance_client()
    registry = ConditionRegistry()

    # Fetch 1 year of data
    logger.info(f"\n📊 Fetching historical data for {symbol}...")
    historical_data = yfinance.get_historical_data(symbol, days=365)

    if not historical_data:
        logger.error(f"❌ No data for {symbol}")
        return 1

    logger.info(f"✅ Fetched {len(historical_data)} days")

    # Load all conditions
    logger.info(f"\n📋 Loading conditions...")
    all_conditions = load_conditions()

    # Filter for TCS conditions only
    tcs_conditions = [c for c in all_conditions if c.get('symbol') == "TCS.NS"]
    logger.info(f"✅ Found {len(tcs_conditions)} conditions for TCS.NS")

    for cond in tcs_conditions:
        logger.info(f"   - {cond.get('name')} (Type: {cond.get('type')})")

    # Store historical data in database
    logger.info(f"\n💾 Storing historical data in database...")
    count = PriceHistoryRepository.insert_or_update_ohlc(symbol, historical_data)
    logger.info(f"✅ Stored {count} candles")

    # Simulate day-by-day checking
    logger.info(f"\n🔍 Simulating daily checks...")
    logger.info("=" * 80)

    triggered_alerts = []

    # For each day, check all conditions
    for i, day_data in enumerate(historical_data):
        date = day_data['date']
        close = day_data['close']

        # Show progress every 50 days, and always show last 30 days
        show_day = (i % 50 == 0) or (i >= len(historical_data) - 30)

        if not show_day:
            continue

        logger.info(f"\n📅 {date} | Close: ₹{close:.2f}")
        logger.info("-" * 80)

        day_triggered = False

        for condition in tcs_conditions:
            try:
                # Create a mock price data dict for this day
                price_data = {
                    'symbol': symbol,
                    'open': day_data['open'],
                    'high': day_data['high'],
                    'low': day_data['low'],
                    'close': day_data['close'],
                    'ltp': day_data['close'],
                    'volume': day_data['volume'],
                    'timestamp': datetime.now().isoformat()
                }

                # Evaluate condition
                cond_type = condition.get('type')
                cond_params = condition.get('parameters', {})
                cond_name = condition.get('name')

                condition_instance = registry.create(cond_type, cond_params)
                triggered, message = condition_instance.evaluate(symbol, price_data)

                if triggered:
                    logger.info(f"   ✅ TRIGGERED: {cond_name}")
                    logger.info(f"      Type: {cond_type}")
                    logger.info(f"      Message: {message}")
                    triggered_alerts.append({
                        'date': date,
                        'price': close,
                        'condition': cond_name,
                        'type': cond_type
                    })
                    day_triggered = True

            except Exception as e:
                logger.debug(f"   Error evaluating {condition.get('name')}: {e}")

        if not day_triggered:
            logger.info(f"   ℹ️  No alerts triggered today")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 BACKTESTING SUMMARY (FULL 1 YEAR)")
    logger.info("=" * 80)

    if triggered_alerts:
        logger.info(f"\n✅ Total Alerts That Would Have Triggered: {len(triggered_alerts)}\n")

        # Group by condition
        by_condition = {}
        for alert in triggered_alerts:
            cond = alert['condition']
            if cond not in by_condition:
                by_condition[cond] = []
            by_condition[cond].append(alert)

        for cond_name, alerts in sorted(by_condition.items()):
            logger.info(f"\n🔔 {cond_name} - {len(alerts)} trigger(s):")
            # Show first 5 and last 5 triggers
            if len(alerts) <= 10:
                for alert in alerts:
                    logger.info(f"   {alert['date']} @ ₹{alert['price']:.2f}")
            else:
                logger.info("   First 5 triggers:")
                for alert in alerts[:5]:
                    logger.info(f"     {alert['date']} @ ₹{alert['price']:.2f}")
                logger.info(f"   ... ({len(alerts) - 10} more triggers) ...")
                logger.info("   Last 5 triggers:")
                for alert in alerts[-5:]:
                    logger.info(f"     {alert['date']} @ ₹{alert['price']:.2f}")
    else:
        logger.info("\n⚠️  No alerts would have triggered in the entire 1-year history")
        logger.info("\nCurrent Conditions for TCS.NS:")
        for cond in tcs_conditions:
            logger.info(f"   - {cond.get('name')}")
            logger.info(f"     Parameters: {cond.get('parameters')}")

    logger.info("\n" + "=" * 80)
    logger.info("BACKTEST COMPLETE")
    logger.info("=" * 80)

    return 0

if __name__ == '__main__':
    sys.exit(main())
