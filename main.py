#!/usr/bin/env python3
"""
Stock Alert System - Main Entry Point
Starts the alert engine and Telegram bot
"""

import signal
import sys
from datetime import datetime

from config.settings import MARKET_HOURS_ONLY
from fetcher.yfinance_client import get_yfinance_client
from alerts.telegram_sender import get_telegram_sender
from scheduler.job_scheduler import get_scheduler
from scheduler.market_calendar import MarketCalendar
from utils.logger import logger, setup_logger


class StockAlertApplication:
    """
    Main application class.
    Manages startup, shutdown, and overall lifecycle.
    """

    def __init__(self):
        """Initialize application."""
        self.scheduler = get_scheduler()
        self.telegram = get_telegram_sender()
        self.yfinance_client = get_yfinance_client()
        self.running = False

        logger.info("=" * 70)
        logger.info("STOCK ALERT SYSTEM - INITIALIZING")
        logger.info("=" * 70)

    def startup(self) -> bool:
        """
        Start the application.

        Steps:
        1. Initialize Yahoo Finance
        2. Connect to Telegram
        3. Start scheduler
        4. Send startup notification

        Returns:
            True if startup successful
        """
        try:
            logger.info("\n📋 STARTUP SEQUENCE")
            logger.info("=" * 70)

            # Step 1: Initialize Yahoo Finance (no auth needed)
            logger.info("\n1️⃣  Initializing Yahoo Finance...")
            if not self.yfinance_client.authenticate():
                logger.error("❌ Yahoo Finance initialization failed")
                return False

            logger.info("✅ Yahoo Finance ready")

            # Step 2: Telegram connection
            logger.info("\n2️⃣  Testing Telegram connection...")
            if not self.telegram.is_ready():
                logger.error("❌ Telegram connection failed")
                logger.error("   Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
                return False

            logger.info("✅ Telegram connected")

            # Step 3: Start scheduler
            logger.info("\n3️⃣  Starting scheduler...")
            self.scheduler.start()
            logger.info("✅ Scheduler started")

            # Step 4: Startup notification
            logger.info("\n4️⃣  Sending startup notification...")
            try:
                self.telegram.send_startup_message()
            except Exception as e:
                logger.warning(f"Failed to send startup message: {e}")

            # Done
            logger.info("\n" + "=" * 70)
            logger.info("✅ APPLICATION STARTED SUCCESSFULLY")
            logger.info("=" * 70)
            logger.info(f"\n⏰ Market Status: {MarketCalendar.get_market_status_text()}")
            logger.info(f"🔄 Check Interval: {self.scheduler.engine.price_fetcher}")
            logger.info(f"⏱️  Next Check: {self.scheduler.get_next_run_time()}")
            logger.info("\n📱 Telegram commands available:")
            logger.info("  /status - System status")
            logger.info("  /add_alert - Add new alert")
            logger.info("  /list_alerts - Show all alerts")
            logger.info("  /delete_alert - Remove alert")
            logger.info("\n" + "=" * 70 + "\n")

            self.running = True
            return True

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            return False

    def shutdown(self) -> None:
        """Shutdown the application gracefully."""
        logger.info("\n" + "=" * 70)
        logger.info("🛑 SHUTTING DOWN")
        logger.info("=" * 70)

        try:
            # Stop scheduler
            if self.scheduler.is_scheduled():
                logger.info("Stopping scheduler...")
                self.scheduler.stop()

            logger.info("✅ Shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        logger.info("=" * 70 + "\n")
        self.running = False

    def signal_handler(self, sig, frame):
        """Handle interrupt signals (Ctrl+C)."""
        logger.info("\n⚠️  Interrupt signal received")
        self.shutdown()
        sys.exit(0)

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Exit code
        """
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Startup
        if not self.startup():
            logger.error("Failed to start application")
            return 1

        # Keep running
        try:
            logger.info("💼 Application running. Press Ctrl+C to stop.\n")
            while self.running:
                # Let scheduler do its job
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nKeyboard interrupt received")
            self.shutdown()
            return 0
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.shutdown()
            return 1

        return 0


def main():
    """Main entry point."""
    app = StockAlertApplication()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
