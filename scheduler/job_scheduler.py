"""
Job Scheduler: Schedule alert engine to run periodically.
Uses APScheduler to manage background jobs.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import pytz

from config.settings import CHECK_INTERVAL_MINUTES, MARKET_HOURS_ONLY
from engine.alert_engine import AlertEngine
from scheduler.market_calendar import MarketCalendar
from utils.logger import logger


class JobScheduler:
    """
    Schedule and manage background jobs using APScheduler.

    Responsibilities:
    - Run alert engine periodically
    - Respect market hours
    - Handle job lifecycle (start, stop, status)
    """

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = BackgroundScheduler(
            timezone=pytz.timezone('Asia/Kolkata')
        )
        self.engine = AlertEngine()
        self.is_running = False

        logger.info("JobScheduler initialized")

    def start(self) -> None:
        """
        Start the scheduler.

        Registers jobs and starts background scheduling.
        """
        try:
            # Register the check job
            self.scheduler.add_job(
                func=self._check_wrapper,
                trigger=IntervalTrigger(minutes=CHECK_INTERVAL_MINUTES),
                id='alert_check_job',
                name='Alert Check',
                replace_existing=True
            )

            # Start scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info(f"✓ Scheduler started (interval: {CHECK_INTERVAL_MINUTES} minutes)")
            logger.info(f"  Market hours only: {MARKET_HOURS_ONLY}")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    def stop(self) -> None:
        """Stop the scheduler."""
        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    def _check_wrapper(self) -> None:
        """
        Wrapper function for scheduled check.

        Handles market hours gating and error handling.
        """
        try:
            # Check market hours
            if MARKET_HOURS_ONLY and not MarketCalendar.is_market_open():
                logger.debug("Market closed, skipping check")
                return

            # Run check
            result = self.engine.run_check()

            # Log result
            if result['success']:
                logger.info(f"Check completed: {result['alerts_fired']} alerts fired")
            else:
                logger.error(f"Check failed: {result.get('error')}")

        except Exception as e:
            logger.error(f"Check failed with exception: {e}")

    def is_scheduled(self) -> bool:
        """Check if scheduler is running."""
        return self.is_running

    def get_next_run_time(self) -> datetime:
        """
        Get next scheduled check time.

        Returns:
            Datetime of next run
        """
        try:
            job = self.scheduler.get_job('alert_check_job')
            if job:
                return job.next_run_time
        except Exception as e:
            logger.error(f"Error getting next run time: {e}")

        return None

    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            'is_running': self.is_running,
            'next_run_time': self.get_next_run_time(),
            'check_interval_minutes': CHECK_INTERVAL_MINUTES,
            'market_hours_only': MARKET_HOURS_ONLY,
            'market_open': MarketCalendar.is_market_open(),
            'market_status': MarketCalendar.get_market_status_text()
        }


# Global scheduler instance
_scheduler_instance = None


def get_scheduler() -> JobScheduler:
    """Get or create global JobScheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = JobScheduler()
    return _scheduler_instance
