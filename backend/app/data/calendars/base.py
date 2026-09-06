"""
StockSense AI — Generic Trading Calendar Interface
Defines market sessions, trading hours, holidays, and timezone abstractions.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from datetime import date, time, datetime, timezone
from typing import List, Optional, Set
import zoneinfo


class SessionType(str, Enum):
    REGULAR = "REGULAR"
    EARLY_CLOSE = "EARLY_CLOSE"
    SPLIT_SESSION = "SPLIT_SESSION" # e.g. PSX Friday jummah break, Asian lunch breaks
    CLOSED = "CLOSED"


@dataclass
class SessionHours:
    session_type: SessionType
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    notes: Optional[str] = None


class TradingCalendar(ABC):
    """
    Abstract Trading Calendar specification for market-specific exchange schedules.
    """

    def __init__(self, market_code: str, exchange_code: str, tz_name: str):
        self.market_code = market_code.upper()
        self.exchange_code = exchange_code.upper()
        self.tz_name = tz_name
        self.tz = zoneinfo.ZoneInfo(tz_name)

    @abstractmethod
    def is_trading_day(self, check_date: date) -> bool:
        """Returns True if the exchange is open for trading on check_date."""
        pass

    @abstractmethod
    def get_holidays(self, year: int) -> Set[date]:
        """Returns the set of recognized public/exchange holidays for the year."""
        pass

    @abstractmethod
    def get_session_hours(self, check_date: date) -> SessionHours:
        """Returns open/close timings and breaks for a given date."""
        pass

    def get_trading_days_between(self, start_date: date, end_date: date) -> List[date]:
        """Returns all trading dates in the date range [start_date, end_date] inclusive."""
        from datetime import timedelta
        current = start_date
        trading_days: List[date] = []
        while current <= end_date:
            if self.is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)
        return trading_days

    def is_market_open_now(self, dt: Optional[datetime] = None) -> bool:
        """Checks if market is currently active."""
        if dt is None:
            dt = datetime.now(self.tz)
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.tz)
        else:
            dt = dt.astimezone(self.tz)

        d = dt.date()
        if not self.is_trading_day(d):
            return False

        hours = self.get_session_hours(d)
        t = dt.time()
        
        if hours.session_type == SessionType.CLOSED:
            return False
        
        if hours.open_time and hours.close_time:
            if hours.break_start and hours.break_end:
                # Active during session 1 or session 2
                in_session_1 = hours.open_time <= t <= hours.break_start
                in_session_2 = hours.break_end <= t <= hours.close_time
                return in_session_1 or in_session_2
            return hours.open_time <= t <= hours.close_time

        return False
