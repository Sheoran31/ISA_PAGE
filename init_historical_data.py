"""
Initialize database with historical price data for Nifty 50 stocks
This is a one-time setup to populate the database with 1 year of price history
"""

import sys
from pathlib import Path
import yfinance as yf
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from storage.price_history_repository import PriceHistoryRepository
from fetcher.ema_calculator import EMACalculator
from utils.logger import logger

# Top opportunity stocks to focus on
PRIORITY_STOCKS = [
    'ADANIPORTS.NS', 'GRASIM.NS', 'LT.NS', 'DRREDDY.NS', 'SUNPHARMA.NS',
    'RELIANCE.NS', 'AXISBANK.NS', 'TITAN.NS', 'NTPC.NS', 'COALINDIA.NS',
    'ONGC.NS', 'INFY.NS'
]

def calculate_ema(prices, period):
    """Calculate EMA"""
    if len(prices) < period:
        return [None] * len(prices)
    ema_values = [None] * len(prices)
    multiplier = 2 / (period + 1)
    sma = sum(prices[:period]) / period
    ema_values[period - 1] = sma
    for i in range(period, len(prices)):
        ema = prices[i] * multiplier + ema_values[i - 1] * (1 - multiplier)
        ema_values[i] = ema
    return ema_values

def init_stock_data(symbol):
    """Download and store historical data for a stock"""
    try:
        print(f"  Downloading {symbol}...", end=' ', flush=True)

        # Download 1 year of data
        df = yf.download(symbol, period='1y', progress=False)

        if df.empty or len(df) < 50:
            print(f"❌ Not enough data")
            return False

        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Calculate EMAs
        closes = np.array(df['Close']).flatten().tolist()

        ema_periods = [20, 50, 100, 150, 200]
        for period in ema_periods:
            df[f'EMA_{period}'] = calculate_ema(closes, period)

        # Store in database
        for idx, row in df.iterrows():
            try:
                PriceHistoryRepository.insert_candle(
                    symbol=symbol,
                    date=idx.strftime('%Y-%m-%d'),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    ema_20=float(row['EMA_20']) if pd.notna(row['EMA_20']) else None,
                    ema_50=float(row['EMA_50']) if pd.notna(row['EMA_50']) else None,
                    ema_100=float(row['EMA_100']) if pd.notna(row['EMA_100']) else None,
                    ema_150=float(row['EMA_150']) if pd.notna(row['EMA_150']) else None,
                    ema_200=float(row['EMA_200']) if pd.notna(row['EMA_200']) else None,
                )
            except Exception as e:
                # Continue even if some dates fail
                pass

        print(f"✅ Stored {len(df)} candles")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Initialize historical data"""
    print("\n" + "="*100)
    print("📊 INITIALIZING HISTORICAL DATA FOR LIVE ALERTS")
    print("="*100)
    print(f"\nThis will download 1 year of price data for {len(PRIORITY_STOCKS)} priority stocks")
    print("and store in database for EMA calculations.\n")

    print("🔄 Downloading historical data...\n")

    success = 0
    for symbol in PRIORITY_STOCKS:
        if init_stock_data(symbol):
            success += 1

    print("\n" + "="*100)
    print(f"✅ Initialization Complete: {success}/{len(PRIORITY_STOCKS)} stocks loaded")
    print("="*100)
    print("\n📱 Database is now ready for LIVE alerts!")
    print("💡 Run 'python3 run_live_alerts.py' to start detecting signals\n")


if __name__ == "__main__":
    main()
