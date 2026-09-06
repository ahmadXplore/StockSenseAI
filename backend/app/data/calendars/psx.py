"""
StockSense AI — Pakistan Stock Exchange (PSX) Trading Calendar
Includes Pakistan public holidays, bank holidays, and Friday Jummah split session schedules.
"""

from __future__ import annotations
from datetime import date, time, datetime, timedelta
from typing import Set

from app.data.calendars.base import TradingCalendar, SessionHours, SessionType


class PSXTradingCalendar(TradingCalendar):
    """
    Trading calendar implementation for PSX (Karachi, Pakistan).
    """

    def __init__(self):
        super().__init__(market_code="PK", exchange_code="PSX", tz_name="Asia/Karachi")

    def get_holidays(self, year: int) -> Set[date]:
        """
        Returns fixed national and known Islamic lunar holidays observed by PSX.
        """
        holidays = {
            date(year, 1, 1),   # Bank Holiday
            date(year, 2, 5),   # Kashmir Day
            date(year, 3, 23),  # Pakistan Day
            date(year, 5, 1),   # Labor Day
            date(year, 7, 1),   # Bank Holiday
            date(year, 8, 14),  # Independence Day
            date(year, 11, 9),  # Iqbal Day
            date(year, 12, 25), # Quaid-e-Azam Day
        }

        # Multi-year mapped Islamic holidays for Pakistan
        known_lunar_holidays = {
            # 2024
            date(2024, 4, 10), date(2024, 4, 11), date(2024, 4, 12), # Eid-ul-Fitr
            date(2024, 6, 17), date(2024, 6, 18), date(2024, 6, 19), # Eid-ul-Adha
            date(2024, 7, 16), date(2024, 7, 17),                     # Ashura (9, 10 Muharram)
            date(2024, 9, 17),                                         # Eid Milad-un-Nabi
            # 2025
            date(2025, 3, 31), date(2025, 4, 1), date(2025, 4, 2),   # Eid-ul-Fitr
            date(2025, 6, 6), date(2025, 6, 7), date(2025, 6, 8),     # Eid-ul-Adha
            date(2025, 7, 5), date(2025, 7, 6),                       # Ashura
            date(2025, 9, 5),                                         # Eid Milad-un-Nabi
            # 2026
            date(2026, 3, 20), date(2026, 3, 21), date(2026, 3, 22), # Eid-ul-Fitr
            date(2026, 5, 27), date(2026, 5, 28), date(2026, 5, 29), # Eid-ul-Adha
            date(2026, 6, 25), date(2026, 6, 26),                     # Ashura
            date(2026, 8, 26),                                         # Eid Milad-un-Nabi
        }

        for h in known_lunar_holidays:
            if h.year == year:
                holidays.add(h)

        return holidays

    def is_trading_day(self, check_date: date) -> bool:
        # Weekend check (Saturday=5, Sunday=6)
        if check_date.weekday() in (5, 6):
            return False
        # Holiday check
        if check_date in self.get_holidays(check_date.year):
            return False
        return True

    def get_session_hours(self, check_date: date) -> SessionHours:
        if not self.is_trading_day(check_date):
            return SessionHours(session_type=SessionType.CLOSED, notes="Market Closed")

        # Friday (weekday=4): Two split trading sessions with Jummah break
        if check_date.weekday() == 4:
            return SessionHours(
                session_type=SessionType.SPLIT_SESSION,
                open_time=time(9, 15),
                close_time=time(16, 30),
                break_start=time(12, 0),
                break_end=time(14, 30),
                notes="Friday Split Session (Jummah Prayer Break 12:00-14:30)"
            )

        # Monday through Thursday (weekday 0..3): 09:15 - 15:30 continuous
        return SessionHours(
            session_type=SessionType.REGULAR,
            open_time=time(9, 15),
            close_time=time(15, 30),
            notes="Regular Trading Session"
        )
