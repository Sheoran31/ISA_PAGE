"""
LIVE Alert Runner - Check stock prices and send Telegram alerts
Runs the alert engine to evaluate all conditions in real-time
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.alert_engine import AlertEngine
from config.settings import CHECK_INTERVAL_MINUTES, MARKET_HOURS_ONLY
from utils.logger import logger


def is_market_hours():
    """Check if current time is during market hours (9:15 AM - 3:30 PM IST)"""
    from datetime import datetime
    import pytz

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)

    # Market hours: 9:15 AM to 3:30 PM on weekdays
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

    is_weekday = now.weekday() < 5  # 0-4 are Mon-Fri
    is_trading_hours = market_open <= now <= market_close

    return is_weekday and is_trading_hours


def main():
    """Run alert engine once"""
    print("\n" + "="*100)
    print("🚀 LIVE ALERT ENGINE - REAL-TIME SIGNAL DETECTION")
    print("="*100)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"📊 Checking top opportunity stocks for EMA breakout/breakdown signals...\n")

    # Check market hours if configured
    if MARKET_HOURS_ONLY and not is_market_hours():
        print("⏸️  Outside market hours. Skipping check.")
        print("   Market hours: 9:15 AM - 3:30 PM IST (Mon-Fri)")
        return

    try:
        # Initialize alert engine
        engine = AlertEngine()

        # Run check cycle
        result = engine.run_check()

        print("\n" + "="*100)
        print("✅ ALERT CHECK COMPLETED")
        print("="*100)
        print(f"Success: {result['success']}")
        print(f"Alerts Fired: {result['alerts_fired']}")
        print(f"Symbols Checked: {result['symbols_checked']}")
        print(f"Elapsed Time: {result.get('elapsed_seconds', 0):.2f}s")
        print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        print("="*100 + "\n")

        if result['alerts_fired'] > 0:
            print(f"📱 {result['alerts_fired']} TELEGRAM ALERT(S) SENT!\n")
        else:
            print("ℹ️  No signals detected in this cycle.\n")

    except Exception as e:
        logger.error(f"Fatal error in alert engine: {e}")
        print(f"\n❌ ERROR: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
