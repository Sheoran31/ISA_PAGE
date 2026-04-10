"""
Backtest EMA Consolidation Breakout Algorithm on RELIANCE.NS (2025 data)
Analyzes accuracy, signal quality, and trading performance
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

class EMAAnalyzer:
    """Analyze EMA consolidation breakout signals"""

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
    def detect_crossover(price: float, ema_dict: Dict[int, float]) -> List[int]:
        """Detect which EMAs the price crossed above."""
        crossed = []
        for period, ema_value in ema_dict.items():
            if ema_value is not None and price > ema_value:
                crossed.append(period)
        return sorted(crossed)

    @staticmethod
    def get_consolidation_range(ema_dict: Dict[int, float]) -> Tuple[float, float]:
        """Get high and low of all EMAs."""
        values = [v for v in ema_dict.values() if v is not None]
        if not values:
            return None, None
        return max(values), min(values)


class BacktestEngine:
    """Backtest EMA consolidation strategy"""

    def __init__(self, symbol: str, year: int = 2025):
        self.symbol = symbol
        self.year = year
        self.analyzer = EMAAnalyzer()
        self.df = None
        self.signals = []
        self.trades = []

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

    def detect_consolidation(self):
        """Detect consolidation periods."""
        print("\n🔍 Detecting consolidation periods...")

        ema_periods = [20, 50, 100, 150, 200]
        consolidation_days = 0
        consolidation_start = None

        consolidation_list = []

        for idx in range(200, len(self.df)):  # Need 200 candles for EMA200
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
                if consolidation_days > 0:
                    consolidation_list.append({
                        'start_idx': consolidation_start,
                        'start_date': self.df.index[consolidation_start],
                        'days': consolidation_days,
                        'end_date': self.df.index[idx-1]
                    })
                consolidation_days = 0

        # Handle end of data
        if consolidation_days > 0:
            consolidation_list.append({
                'start_idx': consolidation_start,
                'start_date': self.df.index[consolidation_start],
                'days': consolidation_days,
                'end_date': self.df.index[-1]
            })

        self.consolidation_periods = consolidation_list
        print(f"✓ Found {len(consolidation_list)} consolidation periods")

        return consolidation_list

    def detect_breakouts(self):
        """Detect breakout signals after consolidation."""
        print("\n⚡ Detecting breakout signals...")

        ema_periods = [20, 50, 100, 150, 200]
        signals = []

        for cons_period in self.consolidation_periods:
            if cons_period['days'] < 3:  # Need minimum 3 days
                continue

            # Start checking from day after consolidation ends
            start_idx = cons_period['start_idx'] + cons_period['days']

            if start_idx >= len(self.df):
                break

            # Look for first breakout in next 5 days
            for offset in range(min(5, len(self.df) - start_idx)):
                check_idx = start_idx + offset

                close_price = float(self.df['Close'].values[check_idx])
                today_emas = {}

                for period in ema_periods:
                    ema_val = self.df[f'EMA_{period}'].values[check_idx]
                    if pd.notna(ema_val):
                        today_emas[period] = float(ema_val)

                # Check crossover
                crossed = self.analyzer.detect_crossover(close_price, today_emas)

                if crossed:
                    range_high, range_low = self.analyzer.get_consolidation_range(today_emas)

                    signal = {
                        'consolidation_start': cons_period['start_date'],
                        'consolidation_end': cons_period['end_date'],
                        'consolidation_days': cons_period['days'],
                        'breakout_date': self.df.index[check_idx],
                        'breakout_price': close_price,
                        'crossed_emas': crossed,
                        'ema_high': range_high,
                        'ema_low': range_low,
                        'days_after_consolidation': offset
                    }
                    signals.append(signal)
                    break

        self.signals = signals
        print(f"✓ Found {len(signals)} breakout signals")

        return signals

    def analyze_trades(self):
        """Analyze trades: entry at breakout, exit at next candle close."""
        print("\n💰 Analyzing trades...")

        trades = []

        for signal in self.signals:
            breakout_date = signal['breakout_date']
            breakout_idx = self.df.index.get_loc(breakout_date)

            entry_price = signal['breakout_price']

            # Exit at next candle close (or 5 days later, whichever comes first)
            exit_idx = min(breakout_idx + 1, len(self.df) - 1)
            exit_price = float(self.df['Close'].values[exit_idx])
            exit_date = self.df.index[exit_idx]

            pnl = exit_price - entry_price
            pnl_pct = (pnl / entry_price) * 100

            trade = {
                **signal,
                'entry_price': entry_price,
                'entry_date': breakout_date,
                'exit_price': exit_price,
                'exit_date': exit_date,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'holding_days': (exit_date - breakout_date).days + 1,
                'win': pnl > 0
            }
            trades.append(trade)

        self.trades = trades
        print(f"✓ Analyzed {len(trades)} trades")

        return trades

    def generate_report(self) -> str:
        """Generate detailed backtest report."""

        report = "\n" + "="*80 + "\n"
        report += f"🎯 BACKTEST REPORT: {self.symbol} ({self.year})\n"
        report += "="*80 + "\n"

        # Summary
        total_signals = len(self.signals)
        total_trades = len(self.trades)

        report += f"\n📊 SUMMARY\n"
        report += f"  Total Consolidation Periods: {len(self.consolidation_periods)}\n"
        report += f"  Consolidations >= 3 days: {sum(1 for c in self.consolidation_periods if c['days'] >= 3)}\n"
        report += f"  Total Breakout Signals: {total_signals}\n"
        report += f"  Total Trades Executed: {total_trades}\n"

        if total_trades == 0:
            report += "\n⚠️  No trades to analyze\n"
            report += "="*80 + "\n"
            return report

        # Trade Statistics
        winning_trades = sum(1 for t in self.trades if t['win'])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades) * 100

        avg_win = np.mean([t['pnl'] for t in self.trades if t['win']]) if winning_trades > 0 else 0
        avg_loss = np.mean([t['pnl'] for t in self.trades if not t['win']]) if losing_trades > 0 else 0

        total_pnl = sum(t['pnl'] for t in self.trades)
        total_pnl_pct = sum(t['pnl_pct'] for t in self.trades)

        best_trade = max(self.trades, key=lambda x: x['pnl'])
        worst_trade = min(self.trades, key=lambda x: x['pnl'])

        report += f"\n💹 TRADING RESULTS\n"
        report += f"  Win Rate: {winning_trades}/{total_trades} ({win_rate:.1f}%)\n"
        report += f"  Winning Trades: {winning_trades}\n"
        report += f"  Losing Trades: {losing_trades}\n"
        report += f"  Avg Win: ₹{avg_win:.2f}\n"
        report += f"  Avg Loss: ₹{avg_loss:.2f}\n"
        report += f"  Total P&L: ₹{total_pnl:.2f}\n"
        report += f"  Total Return: {total_pnl_pct:.2f}%\n"

        if winning_trades > 0 and losing_trades > 0:
            profit_factor = (sum(t['pnl'] for t in self.trades if t['win']) /
                           abs(sum(t['pnl'] for t in self.trades if not t['win'])))
            report += f"  Profit Factor: {profit_factor:.2f}x\n"

        # Best & Worst
        report += f"\n🏆 BEST TRADE\n"
        report += f"  Entry: {best_trade['entry_date'].strftime('%Y-%m-%d')} @ ₹{best_trade['entry_price']:.2f}\n"
        report += f"  Exit: {best_trade['exit_date'].strftime('%Y-%m-%d')} @ ₹{best_trade['exit_price']:.2f}\n"
        report += f"  P&L: ₹{best_trade['pnl']:.2f} ({best_trade['pnl_pct']:+.2f}%)\n"

        report += f"\n💔 WORST TRADE\n"
        report += f"  Entry: {worst_trade['entry_date'].strftime('%Y-%m-%d')} @ ₹{worst_trade['entry_price']:.2f}\n"
        report += f"  Exit: {worst_trade['exit_date'].strftime('%Y-%m-%d')} @ ₹{worst_trade['exit_price']:.2f}\n"
        report += f"  P&L: ₹{worst_trade['pnl']:.2f} ({worst_trade['pnl_pct']:+.2f}%)\n"

        # Consolidation Analysis
        consolidations_3_plus = [c for c in self.consolidation_periods if c['days'] >= 3]
        if consolidations_3_plus:
            avg_cons_days = np.mean([c['days'] for c in consolidations_3_plus])
            report += f"\n📈 CONSOLIDATION ANALYSIS\n"
            report += f"  Avg Consolidation Duration: {avg_cons_days:.1f} days\n"
            report += f"  Longest Consolidation: {max(c['days'] for c in consolidations_3_plus)} days\n"
            report += f"  Shortest Consolidation: {min(c['days'] for c in consolidations_3_plus)} days\n"

        # Top 5 trades
        report += f"\n📋 TOP 5 WINNING TRADES\n"
        top_trades = sorted(self.trades, key=lambda x: x['pnl_pct'], reverse=True)[:5]
        for i, trade in enumerate(top_trades, 1):
            report += f"  {i}. {trade['entry_date'].strftime('%Y-%m-%d')}: +{trade['pnl_pct']:.2f}% (₹{trade['pnl']:.2f})\n"

        report += f"\n📋 TOP 5 LOSING TRADES\n"
        bottom_trades = sorted(self.trades, key=lambda x: x['pnl_pct'])[:5]
        for i, trade in enumerate(bottom_trades, 1):
            report += f"  {i}. {trade['entry_date'].strftime('%Y-%m-%d')}: {trade['pnl_pct']:.2f}% (₹{trade['pnl']:.2f})\n"

        report += "\n" + "="*80 + "\n"

        return report

    def run_backtest(self) -> str:
        """Run complete backtest workflow."""
        if not self.fetch_data():
            return "Failed to fetch data"

        self.calculate_emas()
        self.detect_consolidation()
        self.detect_breakouts()
        self.analyze_trades()

        return self.generate_report()


def main():
    """Run backtest on Reliance 2025 data"""
    backtest = BacktestEngine(symbol="RELIANCE.NS", year=2025)
    report = backtest.run_backtest()
    print(report)

    # Save report
    with open('/Users/purushottam/yogesh/workplace/ISA_BOT/RELIANCE_BACKTEST_2025.txt', 'w') as f:
        f.write(report)

    print("\n📄 Report saved to: RELIANCE_BACKTEST_2025.txt")


if __name__ == "__main__":
    main()
