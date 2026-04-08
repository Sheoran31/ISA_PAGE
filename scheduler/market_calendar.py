"""
Market Calendar: Determine if Indian stock market is open.
Checks: weekday, market hours (9:15 AM - 3:30 PM IST), holidays
"""

from datetime import datetime, time
import pytz

from utils.logger import logger


class MarketCalendar:
    """
    Check if Indian stock market (NSE/BSE) is currently open.

    NSE/BSE Market Hours:
    - Pre-open: 9:00 AM - 9:15 AM IST
    - Regular Trading: 9:15 AM - 3:30 PM IST
    - Post-close: 3:30 PM - 4:00 PM IST
    """

    # IST timezone
    IST = pytz.timezone('Asia/Kolkata')

    # Market hours
    MARKET_OPEN_TIME = time(9, 15)      # 9:15 AM
    MARKET_CLOSE_TIME = time(15, 30)    # 3:30 PM (15:30)

    # NSE holidays for 2026
    # Source: https://www1.nseindia.com/nsetools/holidaycalendar.jsp
    NSE_HOLIDAYS_2026 = [
        # (Month, Day)
        (1, 26),   # Republic Day
        (3, 8),    # Maha Shivaratri
        (3, 25),   # Holi
        (3, 29),   # Eid-ul-Fitr
        (4, 2),    # Good Friday
        (4, 21),   # Mahavir Jayanti
        (5, 1),    # May Day
        (8, 15),   # Independence Day
        (8, 30),   # Janmashtami
        (9, 16),   # Milad-un-Nabi
        (10, 2),   # Gandhi Jayanti
        (10, 25),  # Dussehra
        (11, 11),  # Diwali
        (12, 25),  # Christmas
    ]

    @staticmethod
    def is_market_open() -> bool:
        """
        Check if market is currently open.

        Checks:
        1. Is it a weekday? (Mon-Fri)
        2. Is current time within market hours? (9:15 AM - 3:30 PM IST)
        3. Is today an NSE holiday?

        Returns:
            True if market is open
        """
        now = datetime.now(MarketCalendar.IST)

        # Check if weekday (0=Monday, 6=Sunday)
        if now.weekday() >= 5:  # Saturday or Sunday
            logger.debug("Market closed: Weekend")
            return False

        # Check if NSE holiday
        if MarketCalendar._is_nse_holiday(now):
            logger.debug(f"Market closed: NSE holiday")
            return False

        # Check if within market hours
        current_time = now.time()
        if current_time < MarketCalendar.MARKET_OPEN_TIME:
            logger.debug("Market not yet open (pre-open)")
            return False

        if current_time > MarketCalendar.MARKET_CLOSE_TIME:
            logger.debug("Market closed (post-trading)")
            return False

        logger.debug("Market is open")
        return True

    @staticmethod
    def _is_nse_holiday(dt: datetime) -> bool:
        """
        Check if date is an NSE holiday.

        Args:
            dt: Datetime to check

        Returns:
            True if NSE holiday
        """
        month_day = (dt.month, dt.day)
        return month_day in MarketCalendar.NSE_HOLIDAYS_2026

    @staticmethod
    def is_market_hours(dt: datetime = None) -> bool:
        """
        Check if a specific datetime is during market hours.

        Args:
            dt: Datetime to check (default: now)

        Returns:
            True if during market hours
        """
        if dt is None:
            dt = datetime.now(MarketCalendar.IST)
        else:
            # Assume UTC if no timezone, convert to IST
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt).astimezone(MarketCalendar.IST)

        current_time = dt.time()
        return MarketCalendar.MARKET_OPEN_TIME <= current_time <= MarketCalendar.MARKET_CLOSE_TIME

    @staticmethod
    def seconds_until_market_open() -> int:
        """
        Get seconds until market opens.

        Returns:
            Seconds until 9:15 AM IST (next trading day)
        """
        now = datetime.now(MarketCalendar.IST)

        # If after market hours, next open is tomorrow (or Monday if weekend)
        if now.time() > MarketCalendar.MARKET_CLOSE_TIME:
            # Get next market open day
            next_day = now
            while True:
                next_day = next_day.replace(hour=9, minute=15, second=0, microsecond=0)
                next_day = next_day + pytz.timezone('Asia/Kolkata').localize(
                    datetime(next_day.year, next_day.month, next_day.day)
                ).timedelta(days=1)

                if (next_day.weekday() < 5 and not MarketCalendar._is_nse_holiday(next_day)):
                    break

            return int((next_day - now).total_seconds())

        # Market already open, return 0
        if now.time() >= MarketCalendar.MARKET_OPEN_TIME:
            return 0

        # Market will open today
        today_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        return int((today_open - now).total_seconds())

    @staticmethod
    def seconds_until_market_close() -> int:
        """
        Get seconds until market closes.

        Returns:
            Seconds until 3:30 PM IST (or 0 if market closed)
        """
        now = datetime.now(MarketCalendar.IST)

        if not MarketCalendar.is_market_open():
            return 0

        today_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        return int((today_close - now).total_seconds())

    @staticmethod
    def get_market_status_text() -> str:
        """
        Get human-readable market status.

        Returns:
            Status string
        """
        if not MarketCalendar.is_market_open():
            return "CLOSED"

        seconds_until_close = MarketCalendar.seconds_until_market_close()
        minutes = seconds_until_close // 60
        hours = minutes // 60
        remaining_minutes = minutes % 60

        if hours > 0:
            return f"OPEN ({hours}h {remaining_minutes}m remaining)"
        else:
            return f"OPEN ({minutes}m remaining)"

    @staticmethod
    def add_nse_holiday(month: int, day: int) -> None:
        """
        Add custom NSE holiday.

        Args:
            month: Month (1-12)
            day: Day (1-31)
        """
        if (month, day) not in MarketCalendar.NSE_HOLIDAYS_2026:
            MarketCalendar.NSE_HOLIDAYS_2026.append((month, day))
            logger.info(f"Added NSE holiday: {month}/{day}")
