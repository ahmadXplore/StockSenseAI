"""
StockSense AI — US Markets (NYSE / NASDAQ) Trading Calendar
Includes Federal holidays, SIFMA/exchange closures, and 13:00 early closes.
"""

from __future__ import annotations
from datetime import date, time, datetime, timedelta
from typing import Set

from app.data.calendars.base import TradingCalendar, SessionHours, SessionType


class USTradingCalendar(TradingCalendar):
    """
    Trading calendar implementation for US Equities (NYSE / NASDAQ).
    """

    def __init__(self):
        super().__init__(market_code="US", exchange_code="NASDAQ", tz_name="America/New_York")

    @staticmethod
    def _get_nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
        """Finds nth occurrence of a weekday in a month (e.g., 3rd Monday in Jan)."""
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()
        day_offset = (weekday - first_weekday) % 7
        target_day = 1 + day_offset + (n - 1) * 7
        return date(year, month, target_day)

    @staticmethod
    def _get_last_weekday_of_month(year: int, month: int, weekday: int) -> date:
        """Finds last occurrence of a weekday in a month (e.g., last Monday in May)."""
        # Start at end of month
        if month == 12:
            next_month_first = date(year + 1, 1, 1)
        else:
            next_month_first = date(year, month + 1, 1)
        last_day = next_month_first - timedelta(days=1)
        offset = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=offset)

    @staticmethod
    def _calculate_good_friday(year: int) -> date:
        """Meeus/Jones/Butcher algorithm for Easter / Good Friday."""
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        easter = date(year, month, day)
        return easter - timedelta(days=2) # Good Friday

    def get_holidays(self, year: int) -> Set[date]:
        holidays = set()

        # 1. New Year's Day (Jan 1, or observed if weekend)
        ny = date(year, 1, 1)
        if ny.weekday() == 6: # Sunday -> Monday observed
            holidays.add(date(year, 1, 2))
        else:
            holidays.add(ny)

        # 2. Martin Luther King Jr. Day (3rd Monday in January)
        holidays.add(self._get_nth_weekday_of_month(year, 1, 0, 3))

        # 3. Washington's Birthday / Presidents' Day (3rd Monday in February)
        holidays.add(self._get_nth_weekday_of_month(year, 2, 0, 3))

        # 4. Good Friday
        holidays.add(self._calculate_good_friday(year))

        # 5. Memorial Day (Last Monday in May)
        holidays.add(self._get_last_weekday_of_month(year, 5, 0))

        # 6. Juneteenth National Independence Day (Jun 19)
        june19 = date(year, 6, 19)
        if june19.weekday() == 5:
            holidays.add(date(year, 6, 18))
        elif june19.weekday() == 6:
            holidays.add(date(year, 6, 20))
        else:
            holidays.add(june19)

        # 7. Independence Day (Jul 4)
        july4 = date(year, 7, 4)
        if july4.weekday() == 5:
            holidays.add(date(year, 7, 3))
        elif july4.weekday() == 6:
            holidays.add(date(year, 7, 5))
        else:
            holidays.add(july4)

        # 8. Labor Day (1st Monday in September)
        holidays.add(self._get_nth_weekday_of_month(year, 9, 0, 1))

        # 9. Thanksgiving Day (4th Thursday in November)
        holidays.add(self._get_nth_weekday_of_month(year, 11, 3, 4))

        # 10. Christmas Day (Dec 25)
        xmas = date(year, 12, 25)
        if xmas.weekday() == 5:
            holidays.add(date(year, 12, 24))
        elif xmas.weekday() == 6:
            holidays.add(date(year, 12, 26))
        else:
            holidays.add(xmas)

        return holidays

    def get_early_closes(self, year: int) -> Set[date]:
        """Dates with 13:00 EST early market close."""
        early_closes = set()
        
        # Day before Independence Day (if weekday)
        july3 = date(year, 7, 3)
        if july3.weekday() not in (5, 6):
            early_closes.add(july3)
            
        # Black Friday (Day after Thanksgiving - 4th Friday in Nov)
        thanksgiving = self._get_nth_weekday_of_month(year, 11, 3, 4)
        early_closes.add(thanksgiving + timedelta(days=1))

        # Christmas Eve (Dec 24, if weekday)
        dec24 = date(year, 12, 24)
        if dec24.weekday() not in (5, 6) and dec24 not in self.get_holidays(year):
            early_closes.add(dec24)

        return early_closes

    def is_trading_day(self, check_date: date) -> bool:
        if check_date.weekday() in (5, 6):
            return False
        if check_date in self.get_holidays(check_date.year):
            return False
        return True

    def get_session_hours(self, check_date: date) -> SessionHours:
        if not self.is_trading_day(check_date):
            return SessionHours(session_type=SessionType.CLOSED, notes="Market Closed")

        if check_date in self.get_early_closes(check_date.year):
            return SessionHours(
                session_type=SessionType.EARLY_CLOSE,
                open_time=time(9, 30),
                close_time=time(13, 0),
                notes="Early Close at 13:00 EST"
            )

        return SessionHours(
            session_type=SessionType.REGULAR,
            open_time=time(9, 30),
            close_time=time(16, 0),
            notes="Regular Trading Session"
        )
