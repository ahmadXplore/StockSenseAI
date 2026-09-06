"""
StockSense AI — Trading Calendar Factory & Registry
"""

from __future__ import annotations
from typing import Dict
from app.data.calendars.base import TradingCalendar, SessionHours, SessionType
from app.data.calendars.psx import PSXTradingCalendar
from app.data.calendars.us import USTradingCalendar


class GenericTradingCalendar(TradingCalendar):
    """Fallback calendar for international markets without custom holiday rules."""
    def __init__(self, market_code: str, exchange_code: str, tz_name: str = "UTC"):
        super().__init__(market_code=market_code, exchange_code=exchange_code, tz_name=tz_name)

    def get_holidays(self, year: int) -> set:
        return set()

    def is_trading_day(self, check_date) -> bool:
        return check_date.weekday() not in (5, 6)

    def get_session_hours(self, check_date) -> SessionHours:
        from datetime import time
        if not self.is_trading_day(check_date):
            return SessionHours(session_type=SessionType.CLOSED, notes="Market Closed")
        return SessionHours(
            session_type=SessionType.REGULAR,
            open_time=time(9, 0),
            close_time=time(17, 0),
            notes="Standard 09:00-17:00 Session"
        )


_CALENDAR_CACHE: Dict[str, TradingCalendar] = {
    "PK": PSXTradingCalendar(),
    "PSX": PSXTradingCalendar(),
    "US": USTradingCalendar(),
    "NASDAQ": USTradingCalendar(),
    "NYSE": USTradingCalendar(),
}


def get_trading_calendar(identifier: str) -> TradingCalendar:
    """
    Returns the TradingCalendar for the given market code or exchange code (e.g. 'PSX', 'US', 'NASDAQ', 'LSE').
    """
    key = identifier.strip().upper()
    if key in _CALENDAR_CACHE:
        return _CALENDAR_CACHE[key]
    
    # Generic fallback
    if key in ("GB", "LSE"):
        cal = GenericTradingCalendar("GB", "LSE", "Europe/London")
    elif key in ("JP", "TSE"):
        cal = GenericTradingCalendar("JP", "TSE", "Asia/Tokyo")
    elif key in ("HK", "HKEX"):
        cal = GenericTradingCalendar("HK", "HKEX", "Asia/Hong_Kong")
    elif key in ("IN", "NSE", "BSE"):
        cal = GenericTradingCalendar("IN", "NSE", "Asia/Kolkata")
    else:
        cal = GenericTradingCalendar(key, key, "UTC")
        
    _CALENDAR_CACHE[key] = cal
    return cal
