"""
Scan all NIFTY 50 stocks for EMA Breakout/Breakdown signals
Identifies which stocks have active buy/sell signals
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict

class NiftyScannerEMA:
    """Scan Nifty 50 for EMA breakout/breakdown signals"""

    NIFTY_50 = [
        'TCS.NS', 'RELIANCE.NS', 'HDFCBANK.NS', 'INFY.NS', 'WIPRO.NS',
        'LT.NS', 'ITC.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'HINDUNILVR.NS',
        'MARUTI.NS', 'BAJAJFINSV.NS', 'SUNPHARMA.NS', 'ASIANPAINT.NS', 'POWERGRID.NS',
        'TITAN.NS', 'BAJAJAUT.NS', 'NTPC.NS', 'GAIL.NS', 'COALINDIA.NS',
        'MM.NS', 'NESTLEIND.NS', 'DRREDDY.NS', 'SBIN.NS', 'KOTAKBANK.NS',
        'IDFCBANK.NS', 'HCLTECH.NS', 'TECHM.NS', 'TATASTEEL.NS', 'JSWSTEEL.NS',
        'VEDL.NS', 'BHARTIARTL.NS', 'VODAFONE.NS', 'GRASIM.NS', 'ULTRACEMCO.NS',
        'TATAMOTORS.NS', 'HEROMOTOCO.NS', 'ADANIPORTS.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS',
        'ADANIENT.NS', 'ONGC.NS', 'BPCL.NS', 'CIPLA.NS', 'UPL.NS',
        'SHRIRAMFIN.NS', 'INDIGO.NS', 'SIEMENSIND.NS', 'CUMMINSIND.NS', 'GMRINFRA.NS'
    ]

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """Calculate EMA for prices"""
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

    @staticmethod
    def scan_stock(symbol: str) -> Dict:
        """Scan a single stock for signals"""
        try:
            # Download last 1 year data
            df = yf.download(symbol, period='1y', progress=False)

            if df.empty or len(df) < 200:
                return {
                    'symbol': symbol,
                    'status': 'NOT_ENOUGH_DATA',
                    'close': 0,
                    'signal': None
                }

            # Handle MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Get latest close
            latest_close = float(df['Close'].values[-1])

            # Calculate EMAs
            closes = np.array(df['Close']).flatten().tolist()
            ema_periods = [20, 50, 100, 150, 200]

            ema_vals = {}
            for period in ema_periods:
                ema_list = NiftyScannerEMA.calculate_ema(closes, period)
                if ema_list[-1] is not None:
                    ema_vals[period] = float(ema_list[-1])

            if not ema_vals or len(ema_vals) < 5:
                return {
                    'symbol': symbol,
                    'status': 'ERROR',
                    'close': latest_close,
                    'signal': None
                }

            # Check for breakout/breakdown
            highest_ema = max(ema_vals.values())
            lowest_ema = min(ema_vals.values())
            ema_avg = sum(ema_vals.values()) / len(ema_vals)
            spread_pct = ((highest_ema - lowest_ema) / ema_avg) * 100

            is_breakout = latest_close > highest_ema
            is_breakdown = latest_close < lowest_ema

            signal = None
            if is_breakout:
                signal = 'BREAKOUT'
            elif is_breakdown:
                signal = 'BREAKDOWN'

            return {
                'symbol': symbol,
                'status': 'OK',
                'close': latest_close,
                'signal': signal,
                'ema_high': highest_ema,
                'ema_low': lowest_ema,
                'spread_pct': spread_pct,
                'ema_vals': ema_vals
            }

        except Exception as e:
            return {
                'symbol': symbol,
                'status': 'ERROR',
                'close': 0,
                'signal': None,
                'error': str(e)
            }


def main():
    """Scan all Nifty 50 stocks"""
    print("\n" + "="*100)
    print("🚀 NIFTY 50 EMA BREAKOUT/BREAKDOWN SCANNER")
    print("="*100)
    print(f"\n📊 Scanning {len(NiftyScannerEMA.NIFTY_50)} stocks...\n")

    breakout_stocks = []
    breakdown_stocks = []
    error_stocks = []
    scanned = 0

    for i, symbol in enumerate(NiftyScannerEMA.NIFTY_50, 1):
        print(f"[{i}/{len(NiftyScannerEMA.NIFTY_50)}] Scanning {symbol}...", end=' ')

        result = NiftyScannerEMA.scan_stock(symbol)
        scanned += 1

        if result['status'] == 'OK':
            if result['signal'] == 'BREAKOUT':
                breakout_stocks.append(result)
                print(f"✅ BREAKOUT DETECTED!")
            elif result['signal'] == 'BREAKDOWN':
                breakdown_stocks.append(result)
                print(f"⚠️ BREAKDOWN DETECTED!")
            else:
                print(f"➖ No signal")
        else:
            error_stocks.append(result)
            print(f"❌ {result['status']}")

    # Print results
    print("\n" + "="*100)
    print("📋 SCAN RESULTS")
    print("="*100)

    print(f"\n✅ BREAKOUT SIGNALS (BUY) - {len(breakout_stocks)} stocks:\n")

    if breakout_stocks:
        for i, stock in enumerate(breakout_stocks, 1):
            print(f"{i}. {stock['symbol']}")
            print(f"   Close: ₹{stock['close']:.2f}")
            print(f"   EMA Range: ₹{stock['ema_low']:.2f} - ₹{stock['ema_high']:.2f}")
            print(f"   Spread: {stock['spread_pct']:.2f}%")
            print(f"   Status: Price ABOVE all EMAs 🟢\n")
    else:
        print("   No breakout signals detected.\n")

    print(f"\n🔴 BREAKDOWN SIGNALS (SELL) - {len(breakdown_stocks)} stocks:\n")

    if breakdown_stocks:
        for i, stock in enumerate(breakdown_stocks, 1):
            print(f"{i}. {stock['symbol']}")
            print(f"   Close: ₹{stock['close']:.2f}")
            print(f"   EMA Range: ₹{stock['ema_low']:.2f} - ₹{stock['ema_high']:.2f}")
            print(f"   Spread: {stock['spread_pct']:.2f}%")
            print(f"   Status: Price BELOW all EMAs 🔴\n")
    else:
        print("   No breakdown signals detected.\n")

    print("\n" + "="*100)
    print(f"📊 SUMMARY")
    print("="*100)
    print(f"Total Scanned: {scanned}")
    print(f"Breakout (BUY): {len(breakout_stocks)} 🟢")
    print(f"Breakdown (SELL): {len(breakdown_stocks)} 🔴")
    print(f"No Signal: {scanned - len(breakout_stocks) - len(breakdown_stocks) - len(error_stocks)}")
    print(f"Errors: {len(error_stocks)}")
    print("="*100)

    # Save results
    if breakout_stocks or breakdown_stocks:
        with open('/Users/purushottam/YOGESH/WORKPLACE/ISA_BOT/NIFTY50_SCAN_RESULTS.txt', 'w') as f:
            f.write(f"NIFTY 50 EMA SCAN RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n")
            f.write("="*100 + "\n\n")

            f.write(f"BREAKOUT SIGNALS (BUY): {len(breakout_stocks)}\n\n")
            for stock in breakout_stocks:
                f.write(f"{stock['symbol']}\n")
                f.write(f"  Close: ₹{stock['close']:.2f}\n")
                f.write(f"  EMA Range: ₹{stock['ema_low']:.2f} - ₹{stock['ema_high']:.2f}\n")
                f.write(f"  Spread: {stock['spread_pct']:.2f}%\n\n")

            f.write(f"\nBREAKDOWN SIGNALS (SELL): {len(breakdown_stocks)}\n\n")
            for stock in breakdown_stocks:
                f.write(f"{stock['symbol']}\n")
                f.write(f"  Close: ₹{stock['close']:.2f}\n")
                f.write(f"  EMA Range: ₹{stock['ema_low']:.2f} - ₹{stock['ema_high']:.2f}\n")
                f.write(f"  Spread: {stock['spread_pct']:.2f}%\n\n")

        print(f"\n📄 Results saved to: NIFTY50_SCAN_RESULTS.txt")


if __name__ == "__main__":
    main()
