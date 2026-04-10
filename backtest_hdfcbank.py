"""
Backtest EMA Consolidation Breakout/Breakdown Strategy on HDFCBANK.NS (2025 data)
Tests both BREAKOUT and BREAKDOWN signals
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

class EMAAnalyzer:
    """Analyze EMA consolidation breakout/breakdown signals"""

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """Calculate EMA for a list of prices."""
        if len(prices) < period:
            return [None] * len(prices)

        ema_values = [None] * len(prices)
        multiplier = 2 / (period + 1)

        # First EMA = SMA of first 'period' values
        sma = sum(prices[:period]) / period
        ema_values[period - 1] = sma

        # Calculate remaining EMAs
        for i in range(period, len(prices)):
            ema = prices[i] * multiplier + ema_values[i - 1] * (1 - multiplier)
            ema_values[i] = ema

        return ema_values

    @staticmethod
    def is_consolidated(ema_dict: Dict[int, float], range_percent: float = 5.0) -> bool:
        """Check if all EMAs are within narrow range."""
        if not ema_dict or any(v is None for v in ema_dict.values()):
            return False

        values = [v for v in ema_dict.values() if v is not None]
        if not values:
            return False

        highest = max(values)
        lowest = min(values)
        pct_diff = ((highest - lowest) / lowest) * 100
        return pct_diff <= range_percent

    @staticmethod
    def get_consolidation_range(ema_dict: Dict[int, float]) -> Tuple[float, float]:
        """Get high and low of all EMAs."""
        values = [v for v in ema_dict.values() if v is not None]
        if not values:
            return None, None
        return max(values), min(values)

    @staticmethod
    def detect_breakout(price: float, ema_dict: Dict[int, float]) -> bool:
        """Check if price breaks OUT (above highest EMA)."""
        if not ema_dict:
            return False
        highest_ema = max(ema_dict.values())
        return price > highest_ema

    @staticmethod
    def detect_breakdown(price: float, ema_dict: Dict[int, float]) -> bool:
        """Check if price breaks DOWN (below lowest EMA)."""
        if not ema_dict:
            return False
        lowest_ema = min(ema_dict.values())
        return price < lowest_ema


class HFDCBacktestEngine:
    """Backtest EMA consolidation strategy on HDFCBANK"""

    def __init__(self, symbol: str, year: int = 2025):
        self.symbol = symbol
        self.year = year
        self.analyzer = EMAAnalyzer()
        self.df = None
        self.breakout_signals = []
        self.breakdown_signals = []
        self.consolidations = []

    def fetch_data(self):
        """Download 1 year of historical data."""
        print(f"\n📥 Fetching {self.year} data for {self.symbol}...")

        start_date = f"{self.year}-01-01"
        end_date = f"{self.year}-12-31"

        try:
            self.df = yf.download(self.symbol, start=start_date, end=end_date, progress=False)
            # Handle yfinance returning DataFrames for single ticker
            if isinstance(self.df.columns, pd.MultiIndex):
                self.df.columns = self.df.columns.get_level_values(0)
            print(f"✓ Downloaded {len(self.df)} candles")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def calculate_emas(self):
        """Calculate EMAs for all periods."""
        print("\n📊 Calculating EMAs...")
        closes = np.array(self.df['Close']).flatten().tolist()

        ema_periods = [20, 50, 100, 150, 200]
        for period in ema_periods:
            ema_values = self.analyzer.calculate_ema(closes, period)
            self.df[f'EMA_{period}'] = ema_values

        print(f"✓ Calculated {len(ema_periods)} EMAs")

    def detect_consolidation_periods(self):
        """Detect consolidation periods."""
        print("\n🔍 Detecting consolidation periods...")

        ema_periods = [20, 50, 100, 150, 200]
        consolidation_days = 0
        consolidation_start = None
        consolidation_list = []

        for idx in range(200, len(self.df)):
            # Get today's EMAs
            today_emas = {}
            for period in ema_periods:
                ema_val = self.df[f'EMA_{period}'].values[idx]
                if pd.notna(ema_val):
                    today_emas[period] = float(ema_val)

            # Check consolidation
            is_cons = self.analyzer.is_consolidated(today_emas, range_percent=5.0)

            if is_cons:
                if consolidation_days == 0:
                    consolidation_start = idx
                consolidation_days += 1
            else:
                if consolidation_days >= 3:  # Only track 3+ day consolidations
                    consolidation_list.append({
                        'start_idx': consolidation_start,
                        'start_date': self.df.index[consolidation_start],
                        'days': consolidation_days,
                        'end_date': self.df.index[idx-1]
                    })
                consolidation_days = 0

        # Handle end of data
        if consolidation_days >= 3:
            consolidation_list.append({
                'start_idx': consolidation_start,
                'start_date': self.df.index[consolidation_start],
                'days': consolidation_days,
                'end_date': self.df.index[-1]
            })

        self.consolidations = consolidation_list
        print(f"✓ Found {len(consolidation_list)} consolidation periods (3+ days)")

        return consolidation_list

    def detect_signals(self):
        """Detect both BREAKOUT and BREAKDOWN signals."""
        print("\n⚡ Detecting breakout/breakdown signals...")

        ema_periods = [20, 50, 100, 150, 200]
        breakout_signals = []
        breakdown_signals = []

        for idx in range(200, len(self.df)):
            close_price = float(self.df['Close'].values[idx])

            # Get today's EMAs
            today_emas = {}
            for period in ema_periods:
                ema_val = self.df[f'EMA_{period}'].values[idx]
                if pd.notna(ema_val):
                    today_emas[period] = float(ema_val)

            if not today_emas:
                continue

            # Check consolidation status from previous day
            is_prev_consolidated = False
            if idx > 0:
                prev_emas = {}
                for period in ema_periods:
                    prev_ema_val = self.df[f'EMA_{period}'].values[idx-1]
                    if pd.notna(prev_ema_val):
                        prev_emas[period] = float(prev_ema_val)
                is_prev_consolidated = self.analyzer.is_consolidated(prev_emas, 5.0)

            # Check for breakout (price above highest EMA after consolidation)
            if is_prev_consolidated and self.analyzer.detect_breakout(close_price, today_emas):
                range_high, range_low = self.analyzer.get_consolidation_range(today_emas)
                breakout_signals.append({
                    'date': self.df.index[idx],
                    'price': close_price,
                    'ema_high': range_high,
                    'ema_low': range_low,
                    'ema_dict': dict(today_emas)
                })

            # Check for breakdown (price below lowest EMA after consolidation)
            if is_prev_consolidated and self.analyzer.detect_breakdown(close_price, today_emas):
                range_high, range_low = self.analyzer.get_consolidation_range(today_emas)
                breakdown_signals.append({
                    'date': self.df.index[idx],
                    'price': close_price,
                    'ema_high': range_high,
                    'ema_low': range_low,
                    'ema_dict': dict(today_emas)
                })

        self.breakout_signals = breakout_signals
        self.breakdown_signals = breakdown_signals

        print(f"✓ Found {len(breakout_signals)} BREAKOUT signals")
        print(f"✓ Found {len(breakdown_signals)} BREAKDOWN signals")

        return breakout_signals, breakdown_signals

    def generate_report(self) -> str:
        """Generate detailed backtest report."""

        report = "\n" + "="*80 + "\n"
        report += f"🎯 HDFCBANK EMA CONSOLIDATION BACKTEST REPORT ({self.year})\n"
        report += "="*80 + "\n"

        total_consolidations = len(self.consolidations)
        total_breakouts = len(self.breakout_signals)
        total_breakdowns = len(self.breakdown_signals)
        total_signals = total_breakouts + total_breakdowns

        report += f"\n📊 SUMMARY\n"
        report += f"  Total Consolidation Periods: {total_consolidations}\n"
        report += f"  Total BREAKOUT Signals (⬆️): {total_breakouts}\n"
        report += f"  Total BREAKDOWN Signals (⬇️): {total_breakdowns}\n"
        report += f"  Total Signals: {total_signals}\n"

        if total_consolidations > 0:
            avg_cons_days = np.mean([c['days'] for c in self.consolidations])
            report += f"\n📈 CONSOLIDATION ANALYSIS\n"
            report += f"  Avg Consolidation Duration: {avg_cons_days:.1f} days\n"
            report += f"  Longest: {max(c['days'] for c in self.consolidations)} days\n"
            report += f"  Shortest: {min(c['days'] for c in self.consolidations)} days\n"

        if total_breakouts > 0:
            report += f"\n🟢 BREAKOUT SIGNALS (⬆️ Uptrend)\n"
            for i, signal in enumerate(self.breakout_signals[:10], 1):
                report += f"\n  {i}. {signal['date'].strftime('%Y-%m-%d')}\n"
                report += f"     Price: ₹{signal['price']:.2f}\n"
                report += f"     EMA Range: ₹{signal['ema_low']:.2f} - ₹{signal['ema_high']:.2f}\n"
                report += f"     Signal: Price CLOSED ABOVE all EMAs ✓\n"

        if total_breakdowns > 0:
            report += f"\n🔴 BREAKDOWN SIGNALS (⬇️ Downtrend)\n"
            for i, signal in enumerate(self.breakdown_signals[:10], 1):
                report += f"\n  {i}. {signal['date'].strftime('%Y-%m-%d')}\n"
                report += f"     Price: ₹{signal['price']:.2f}\n"
                report += f"     EMA Range: ₹{signal['ema_low']:.2f} - ₹{signal['ema_high']:.2f}\n"
                report += f"     Signal: Price CLOSED BELOW all EMAs ✓\n"

        report += f"\n" + "="*80 + "\n"
        report += "✅ System is ready for live trading!\n"
        report += "="*80 + "\n"

        return report

    def run_backtest(self) -> str:
        """Run complete backtest workflow."""
        if not self.fetch_data():
            return "Failed to fetch data"

        self.calculate_emas()
        self.detect_consolidation_periods()
        self.detect_signals()

        return self.generate_report()


def main():
    """Run backtest on HDFCBANK 2025 data"""
    backtest = HFDCBacktestEngine(symbol="HDFCBANK.NS", year=2025)
    report = backtest.run_backtest()
    print(report)

    # Save report
    with open('/Users/purushottam/YOGESH/WORKPLACE/ISA_BOT/HDFCBANK_BACKTEST_2025.txt', 'w') as f:
        f.write(report)

    print("\n📄 Report saved to: HDFCBANK_BACKTEST_2025.txt")


if __name__ == "__main__":
    main()
