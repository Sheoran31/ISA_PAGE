#!/usr/bin/env python3
"""
Test script: Fetch 1 year of TCS.NS data and test conditions
"""

import sys
from datetime import datetime
from fetcher.yfinance_client import get_yfinance_client
from utils.logger import logger

def main():
    logger.info("=" * 70)
    logger.info("TCS.NS - 1 YEAR DATA TEST")
    logger.info("=" * 70)

    # Initialize client
    yfinance = get_yfinance_client()

    symbol = "TCS.NS"

    # Fetch 1 year of data
    logger.info(f"\n📊 Fetching 1 year of data for {symbol}...")
    historical_data = yfinance.get_historical_data(symbol, days=365)

    if not historical_data:
        logger.error(f"❌ No data fetched for {symbol}")
        return 1

    logger.info(f"✅ Fetched {len(historical_data)} days of data")

    # Show first and last records
    if len(historical_data) > 0:
        logger.info(f"\n📈 Data Range:")
        logger.info(f"   First: {historical_data[0]['date']} - Close: ₹{historical_data[0]['close']:.2f}")
        logger.info(f"   Last:  {historical_data[-1]['date']} - Close: ₹{historical_data[-1]['close']:.2f}")

        # Calculate some stats
        closes = [d['close'] for d in historical_data]
        highs = [d['high'] for d in historical_data]
        lows = [d['low'] for d in historical_data]

        logger.info(f"\n📊 Statistics:")
        logger.info(f"   Min: ₹{min(closes):.2f}")
        logger.info(f"   Max: ₹{max(closes):.2f}")
        logger.info(f"   Avg: ₹{sum(closes)/len(closes):.2f}")
        logger.info(f"   Last: ₹{closes[-1]:.2f}")

        # Get current price
        logger.info(f"\n💹 Current Price:")
        current = yfinance.get_ohlcv(symbol)
        if current:
            logger.info(f"   LTP: ₹{current['ltp']:.2f}")
            logger.info(f"   Open: ₹{current['open']:.2f}")
            logger.info(f"   High: ₹{current['high']:.2f}")
            logger.info(f"   Low: ₹{current['low']:.2f}")
            logger.info(f"   Volume: {current['volume']:,}")

    # Display sample historical data for analysis
    logger.info(f"\n📋 Last 10 Days of Data:")
    logger.info("-" * 70)
    for candle in historical_data[-10:]:
        logger.info(
            f"   {candle['date']} | O: ₹{candle['open']:.2f} | "
            f"H: ₹{candle['high']:.2f} | L: ₹{candle['low']:.2f} | "
            f"C: ₹{candle['close']:.2f} | V: {candle['volume']:,}"
        )

    logger.info("\n" + "=" * 70)
    logger.info("TEST COMPLETE")
    logger.info("=" * 70)

    return 0

if __name__ == '__main__':
    sys.exit(main())
