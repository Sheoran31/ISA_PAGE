#!/usr/bin/env python3
"""
Test Telegram Connection - Send Test Message
"""

import sys
from alerts.telegram_sender import get_telegram_sender
from utils.logger import logger

def main():
    logger.info("=" * 70)
    logger.info("TELEGRAM CONNECTION TEST")
    logger.info("=" * 70)

    telegram = get_telegram_sender()

    # Test message
    test_message = (
        "✅ STOCK ALERT SYSTEM - TELEGRAM TEST\n\n"
        "🔔 Telegram Connection Working!\n\n"
        "System Status:\n"
        "• Nifty 50 Stocks: Monitoring\n"
        "• EMA Consolidation: Active\n"
        "• Alert Interval: Every 2 minutes\n"
        "• Breakout Detection: Enabled\n\n"
        "🚀 System is LIVE and READY to send alerts!\n\n"
        "Next market opening: 9:15 AM IST"
    )

    logger.info("\n📤 Sending test message to Telegram...\n")
    try:
        result = telegram.send_alert(test_message)
        if result:
            logger.info("✅ TEST MESSAGE SENT SUCCESSFULLY!")
            logger.info("✅ Telegram is working properly")
            logger.info("\nYou should receive the message on your Telegram now!")
        else:
            logger.error("❌ Failed to send message")
            return 1
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1

    logger.info("\n" + "=" * 70)
    logger.info("TEST COMPLETE")
    logger.info("=" * 70)

    return 0

if __name__ == '__main__':
    sys.exit(main())
