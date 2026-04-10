"""
Test Smart EMA Breakout/Breakdown on HDFCBANK (2025)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

class EMAAnalyzer:
    """Analyze EMA consolidation with smart detection"""

    @staticmethod
    def calculate_ema(prices, period):
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

# Download data
print("\n📥 Downloading HDFCBANK data...")
df = yf.download('HDFCBANK.NS', start='2025-01-01', end='2025-12-31', progress=False)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Calculate EMAs
closes = np.array(df['Close']).flatten().tolist()

ema_periods = [20, 50, 100, 150, 200]
for period in ema_periods:
    df[f'EMA_{period}'] = EMAAnalyzer.calculate_ema(closes, period)

print(f"✓ Calculated EMAs\n")

# Detect signals
print("="*80)
print("🎯 SMART EMA BREAKOUT/BREAKDOWN SIGNALS")
print("="*80)

breakouts = []
breakdowns = []

for idx in range(200, len(df)):
    close_price = float(df['Close'].values[idx])

    # Get today's EMAs
    ema_vals = {}
    for period in ema_periods:
        ema_val = df[f'EMA_{period}'].values[idx]
        if pd.notna(ema_val):
            ema_vals[period] = float(ema_val)

    if not ema_vals or len(ema_vals) < 5:
        continue

    # Calculate spread
    highest_ema = max(ema_vals.values())
    lowest_ema = min(ema_vals.values())
    ema_spread = highest_ema - lowest_ema
    ema_avg = sum(ema_vals.values()) / len(ema_vals)
    spread_pct = (ema_spread / ema_avg) * 100

    is_tight = spread_pct <= 1.5  # Natural tight range
    is_breakout = close_price > highest_ema
    is_breakdown = close_price < lowest_ema

    # Alert if tight EMAs + price move
    if is_tight and is_breakout:
        breakouts.append({
            'date': df.index[idx],
            'price': close_price,
            'spread_pct': spread_pct,
            'ema_high': highest_ema,
            'ema_low': lowest_ema,
            'ema_vals': ema_vals
        })

    if is_tight and is_breakdown:
        breakdowns.append({
            'date': df.index[idx],
            'price': close_price,
            'spread_pct': spread_pct,
            'ema_high': highest_ema,
            'ema_low': lowest_ema,
            'ema_vals': ema_vals
        })

# Print results
print(f"\n✅ FOUND {len(breakouts)} BREAKOUT SIGNALS (🟢 BUY):\n")
for i, sig in enumerate(breakouts, 1):
    print(f"{i}. {sig['date'].strftime('%Y-%m-%d')} | Price: ₹{sig['price']:.2f} | Spread: {sig['spread_pct']:.2f}%")
    print(f"   EMA Range: ₹{sig['ema_low']:.2f} - ₹{sig['ema_high']:.2f}")
    print()

print(f"\n❌ FOUND {len(breakdowns)} BREAKDOWN SIGNALS (🔴 SELL):\n")
for i, sig in enumerate(breakdowns, 1):
    print(f"{i}. {sig['date'].strftime('%Y-%m-%d')} | Price: ₹{sig['price']:.2f} | Spread: {sig['spread_pct']:.2f}%")
    print(f"   EMA Range: ₹{sig['ema_low']:.2f} - ₹{sig['ema_high']:.2f}")
    print()

print("="*80)
print(f"Total Signals: {len(breakouts) + len(breakdowns)}")
print("="*80)
