"""
Hourly Scan with Telegram Report
Runs alert check and sends summary report to Telegram
"""

import sys
import os
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.alert_engine import AlertEngine
from config.settings import CHECK_INTERVAL_MINUTES, MARKET_HOURS_ONLY
from utils.logger import logger


def send_report_to_telegram(result, alerts_fired_count):
    """Send scan report to Telegram"""
    env_file = Path(__file__).parent / '.env'
    load_dotenv(env_file, override=True)

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        logger.warning("Telegram credentials not configured")
        return

    # Create report message
    success_emoji = "✅" if result['success'] else "❌"
    report = f"""
{success_emoji} NIFTY 50 HOURLY SCAN REPORT

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}

📊 Scan Summary:
  Symbols Checked: {result['symbols_checked']}
  Alerts Fired: {result['alerts_fired']} 🔔
  Status: {'SUCCESS' if result['success'] else 'FAILED'}
  Elapsed: {result.get('elapsed_seconds', 0):.1f}s

{'🟢 BREAKOUT Signals (BUY): Detected!' if alerts_fired_count > 0 else '⏸️  No signals this hour'}

📱 Next scan: In 1 hour
"""

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": report,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info("✅ Report sent to Telegram")
        else:
            logger.warning(f"Failed to send report: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending report: {e}")


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
    """Run alert engine and send report"""
    print("\n" + "="*100)
    print("🚀 HOURLY NIFTY 50 SCAN - WITH TELEGRAM REPORT")
    print("="*100)
    print(f"⏰ Scan started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")

    # Check market hours if configured
    if MARKET_HOURS_ONLY and not is_market_hours():
        print("⏸️  Outside market hours. Skipping scan.")
        print("   Market hours: 9:15 AM - 3:30 PM IST (Mon-Fri)")
        return

    try:
        # Initialize alert engine
        engine = AlertEngine()

        # Run check cycle
        result = engine.run_check()

        # Extract alerts count
        alerts_fired = result.get('alerts_fired', 0)

        print("\n" + "="*100)
        print("📊 SCAN RESULTS")
        print("="*100)
        print(f"Success: {result['success']}")
        print(f"Alerts Fired: {alerts_fired}")
        print(f"Symbols Checked: {result['symbols_checked']}")
        print(f"Elapsed Time: {result.get('elapsed_seconds', 0):.2f}s")
        print("="*100 + "\n")

        if alerts_fired > 0:
            print(f"🔔 {alerts_fired} SIGNAL(S) DETECTED!\n")
        else:
            print("ℹ️  No signals detected in this cycle.\n")

        # Send report to Telegram
        print("📱 Sending report to Telegram...")
        send_report_to_telegram(result, alerts_fired)
        print("✅ Report sent!\n")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ ERROR: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
